"""
CMF Subprocess Manager - Singleton that manages the shared worker subprocess.

This module provides a singleton manager that:
1. Starts a single worker subprocess
2. Routes tasks from all Cmf instances to that subprocess
3. Handles results and errors
4. Gracefully shuts down the subprocess
5. Recovers from subprocess crashes via session registry and task log
6. Handles queue failures with retry logic and automatic recovery
"""

import multiprocessing
import threading
import atexit
import logging
import time
import uuid
import typing as t
import queue
import errno

logger = logging.getLogger(__name__)

MAX_RESTART_ATTEMPTS = 3
MAX_QUEUE_PUT_RETRIES = 3
QUEUE_PUT_RETRY_DELAY = 0.1  # seconds


class CmfSubprocessManager:
    """
    Singleton manager for the shared CMF worker subprocess.
    
    This class ensures that only ONE subprocess is created, no matter how many
    Cmf instances are created. All Cmf instances share this single subprocess.
    
    Thread-safe: Uses locks to prevent race conditions during initialization.
    Crash-resilient: Restarts the subprocess and replays tasks if it dies.
    """
    
    _instance: t.Optional['CmfSubprocessManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern: only one instance ever exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check
                    cls._instance = super(CmfSubprocessManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the manager (only runs once due to singleton)."""
        if self._initialized:
            return
        
        # Communication channels
        self.task_queue: t.Optional[multiprocessing.Queue] = None
        self.result_queue: t.Optional[multiprocessing.Queue] = None
        self.shutdown_event: t.Optional[multiprocessing.Event] = None
        
        # Subprocess
        self.worker_process: t.Optional[multiprocessing.Process] = None
        
        # State
        self._started = False
        self._shutdown_requested = False
        self._initialized = True

        # --- Recovery state (lives in main process, survives subprocess crashes) ---

        # session_id -> constructor kwargs, used to re-init sessions after restart
        self._session_registry: t.Dict[str, t.Dict] = {}

        # session_id -> ordered list of (task_id, method, kwargs) for confirmed tasks
        self._task_log: t.Dict[str, t.List[t.Dict]] = {}

        # task_id -> session_id for tasks that are in-flight (sent but no result yet)
        self._inflight: t.Dict[str, str] = {}

        # Traffic light: held by recovery thread; all submit_task callers wait on it
        self._recovery_lock = threading.Lock()

        # Tracks how many times the subprocess has been restarted
        self._restart_count = 0

        # Lock for thread-safe queue operations
        self._queue_lock = threading.Lock()

        logger.info("[CMF Manager] CmfSubprocessManager initialized")
    
    def start(self):
        """
        Start the worker subprocess.
        
        This is called automatically by the first Cmf instance that's created.
        Subsequent calls do nothing (subprocess already running).
        """
        with self._lock:
            if self._started:
                logger.debug("[CMF Manager] Subprocess already started")
                return
            
            logger.info("[CMF Manager] Starting worker subprocess")
            
            # Create communication channels
            self.task_queue = multiprocessing.Queue()
            self.result_queue = multiprocessing.Queue()
            self.shutdown_event = multiprocessing.Event()
            
            # Import worker loop
            from cmflib.cmf_worker_loop import worker_loop
            
            # Create and start subprocess
            self.worker_process = multiprocessing.Process(
                target=worker_loop,
                args=(self.task_queue, self.result_queue, self.shutdown_event),
                name="cmf-worker-subprocess",
                daemon=False  # Not daemon - we want graceful shutdown
            )
            self.worker_process.start()
            
            self._started = True
            
            # Register cleanup on program exit
            atexit.register(self.shutdown)
            
            logger.info(f"[CMF Manager] Worker subprocess started (PID: {self.worker_process.pid})")
    
    def _validate_queues(self) -> bool:
        """Check if queues are in a valid state.
        
        Returns:
            True if queues are valid, False otherwise
        """
        try:
            if self.task_queue is None or self.result_queue is None:
                return False
            
            # Check if queues are closed (they have _closed attribute when closed)
            if hasattr(self.task_queue, '_closed') and self.task_queue._closed:
                return False
            if hasattr(self.result_queue, '_closed') and self.result_queue._closed:
                return False
            
            return True
        except Exception as e:
            logger.error(f"[CMF Manager] Queue validation failed: {e}")
            return False
    
    def _safe_put_task(self, task: t.Dict, timeout: float = 5.0) -> bool:
        """Safely put a task on the queue with retry logic.
        
        Args:
            task: Task dictionary to send
            timeout: Timeout for each put attempt
        
        Returns:
            True if successful, False if all retries failed
        """
        for attempt in range(MAX_QUEUE_PUT_RETRIES):
            try:
                if not self._validate_queues():
                    logger.error(f"[CMF Manager] Invalid queue state on put attempt {attempt + 1}")
                    if attempt < MAX_QUEUE_PUT_RETRIES - 1:
                        time.sleep(QUEUE_PUT_RETRY_DELAY)
                        continue
                    return False
                
                with self._queue_lock:
                    self.task_queue.put(task, timeout=timeout)
                return True
                
            except queue.Full:
                logger.warning(f"[CMF Manager] Task queue full on attempt {attempt + 1}")
                if attempt < MAX_QUEUE_PUT_RETRIES - 1:
                    time.sleep(QUEUE_PUT_RETRY_DELAY)
                    continue
                logger.error("[CMF Manager] Task queue remains full after retries")
                return False
                
            except (ValueError, OSError, BrokenPipeError, EOFError) as e:
                logger.error(f"[CMF Manager] Queue operation failed on attempt {attempt + 1}: {e}")
                if attempt < MAX_QUEUE_PUT_RETRIES - 1:
                    time.sleep(QUEUE_PUT_RETRY_DELAY)
                    continue
                return False
                
            except Exception as e:
                logger.error(f"[CMF Manager] Unexpected error putting task (attempt {attempt + 1}): {e}")
                if attempt < MAX_QUEUE_PUT_RETRIES - 1:
                    time.sleep(QUEUE_PUT_RETRY_DELAY)
                    continue
                return False
        
        return False
    
    def _safe_get_result(self, timeout: float = 1.0) -> t.Optional[t.Dict]:
        """Safely get a result from the queue with comprehensive error handling.
        
        Args:
            timeout: Timeout for the get operation
        
        Returns:
            Result dictionary or None if failed
        
        Raises:
            QueueBrokenError: If queue is in a broken state and recovery needed
        """
        try:
            if not self._validate_queues():
                raise QueueBrokenError("Result queue is invalid or closed")
            
            with self._queue_lock:
                result = self.result_queue.get(timeout=timeout)
            return result
            
        except queue.Empty:
            # This is expected - not an error
            return None
            
        except (ValueError, OSError, BrokenPipeError, EOFError) as e:
            logger.error(f"[CMF Manager] Queue operation failed during get: {e}")
            raise QueueBrokenError(f"Result queue broken: {e}")
            
        except Exception as e:
            logger.error(f"[CMF Manager] Unexpected error getting result: {e}")
            raise QueueBrokenError(f"Unexpected queue error: {e}")
    
    def _cleanup_queues(self):
        """Safely cleanup and close queues to prevent resource leaks."""
        try:
            if self.task_queue is not None:
                try:
                    # Close and join the queue
                    self.task_queue.close()
                    self.task_queue.join_thread()
                except Exception as e:
                    logger.warning(f"[CMF Manager] Error closing task_queue: {e}")
            
            if self.result_queue is not None:
                try:
                    self.result_queue.close()
                    self.result_queue.join_thread()
                except Exception as e:
                    logger.warning(f"[CMF Manager] Error closing result_queue: {e}")
                    
        except Exception as e:
            logger.error(f"[CMF Manager] Error during queue cleanup: {e}")
    
    def register_session(self, session_id: str, init_kwargs: t.Dict):
        """
        Register a session so it can be reconstructed after a subprocess crash.

        Args:
            session_id: Unique identifier for the session
            init_kwargs: Constructor kwargs passed to Cmf inside the worker
        """
        self._session_registry[session_id] = init_kwargs
        self._task_log[session_id] = []
        logger.debug(f"[CMF Manager] Session registered: {session_id}")

    def unregister_session(self, session_id: str):
        """
        Remove a session from the registry once it has been finalized.

        Args:
            session_id: Session to remove
        """
        self._session_registry.pop(session_id, None)
        self._task_log.pop(session_id, None)
        logger.debug(f"[CMF Manager] Session unregistered: {session_id}")

    def submit_task(
        self,
        session_id: str,
        method: str,
        kwargs: t.Dict,
        timeout: t.Optional[float] = None
    ) -> t.Any:
        """
        Submit a task to the worker subprocess and wait for the result.

        Blocks if a crash recovery is in progress (traffic light is RED).
        Triggers recovery automatically if the subprocess dies mid-task.

        Args:
            session_id: Unique identifier for the CMF session
            method: Name of the CMF method to call
            kwargs: Keyword arguments for the method
            timeout: Maximum time to wait for result (None = wait forever)

        Returns:
            Result from the method execution

        Raises:
            RuntimeError: If subprocess not started, crashed unrecoverably, or task failed
            TimeoutError: If result not received within timeout
        """
        if not self._started:
            raise RuntimeError("Subprocess not started. Call start() first.")

        # --- Traffic light: block here if recovery is in progress ---
        with self._recovery_lock:
            pass  # immediately released once recovery finishes

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Create task
        task = {
            "task_id": task_id,
            "session_id": session_id,
            "method": method,
            "kwargs": kwargs,
            "timestamp": time.time()
        }

        logger.debug(f"[CMF Manager] Submitting task {task_id}: {session_id}.{method}")

        # Track as in-flight before putting on queue
        self._inflight[task_id] = session_id

        # Send task to subprocess with safe queue operation
        if not self._safe_put_task(task):
            self._inflight.pop(task_id, None)
            # Queue is broken - trigger recovery
            logger.error(f"[CMF Manager] Failed to submit task {task_id}, triggering recovery")
            self._recover(failed_task=task)
            # After recovery, retry
            return self.submit_task(session_id, method, kwargs, timeout)

        # Wait for result
        start_time = time.time()
        while True:
            try:
                result = self._safe_get_result(timeout=1.0)
                
                # None means Empty exception (timeout) - not an error
                if result is None:
                    # Check timeout
                    if timeout is not None and (time.time() - start_time) > timeout:
                        self._inflight.pop(task_id, None)
                        raise TimeoutError(f"Task {task_id} timed out after {timeout}s")

                    # Check if subprocess is still alive
                    if not self.worker_process.is_alive():
                        logger.error(f"[CMF Manager] Subprocess died during task {task_id}. Attempting recovery.")
                        self._inflight.pop(task_id, None)
                        self._recover(failed_task=task)
                        # After recovery, re-submit this task
                        return self.submit_task(session_id, method, kwargs, timeout)

                    continue

                # Check if this is our result
                if result.get("task_id") == task_id:
                    self._inflight.pop(task_id, None)

                    if result.get("status") == "success":
                        logger.debug(f"[CMF Manager] Task {task_id} completed successfully")
                        # Record in task log (skip internal session management methods)
                        if method not in ("_init_session", "_cleanup_session") and session_id in self._task_log:
                            self._task_log[session_id].append({
                                "task_id": task_id,
                                "method": method,
                                "kwargs": kwargs
                            })
                        return result.get("result")

                    elif result.get("status") == "error":
                        error_msg = result.get("error", "Unknown error")
                        error_trace = result.get("traceback", "")
                        logger.error(f"[CMF Manager] Task {task_id} failed: {error_msg}")
                        raise RuntimeError(f"Task execution failed: {error_msg}\n{error_trace}")

                else:
                    # Not our result - put it back (shouldn't happen with FIFO execution)
                    logger.warning(f"[CMF Manager] Received result for wrong task: {result.get('task_id')}")
                    # Use safe put to handle errors
                    if not self._safe_put_task(result, timeout=1.0):
                        logger.error(f"[CMF Manager] Failed to return mismatched result to queue")

            except QueueBrokenError as e:
                # Queue is broken but subprocess might still be alive - trigger recovery
                logger.error(f"[CMF Manager] Queue broken during task {task_id}: {e}. Attempting recovery.")
                self._inflight.pop(task_id, None)
                self._recover(failed_task=task)
                # After recovery, re-submit this task
                return self.submit_task(session_id, method, kwargs, timeout)

    def _recover(self, failed_task: t.Optional[t.Dict] = None):
        """
        Restart the subprocess and replay all session state and confirmed tasks.

        Acquires the recovery lock (turns traffic light RED) so no new tasks
        are submitted until recovery is complete.

        Args:
            failed_task: The task that was in-flight when the crash was detected,
                         used to avoid double-logging it in the replay.
        """
        # Only one thread should perform recovery
        if not self._recovery_lock.acquire(blocking=False):
            # Another thread is already recovering — wait for it to finish
            logger.debug("[CMF Manager] Recovery already in progress, waiting")
            with self._recovery_lock:
                pass
            return

        try:
            if self._restart_count >= MAX_RESTART_ATTEMPTS:
                raise RuntimeError(
                    f"[CMF Manager] Subprocess crashed {self._restart_count} times. "
                    "Giving up. Check logs for root cause."
                )

            self._restart_count += 1
            logger.warning(
                f"[CMF Manager] Starting recovery (attempt {self._restart_count}/{MAX_RESTART_ATTEMPTS})"
            )

            # Clean up dead process and old queues
            if self.worker_process and self.worker_process.is_alive():
                self.worker_process.terminate()
                self.worker_process.join(timeout=3.0)
            
            # Close old queues to prevent resource leaks
            self._cleanup_queues()

            # Fresh communication channels with error handling
            try:
                self.task_queue = multiprocessing.Queue()
                self.result_queue = multiprocessing.Queue()
                self.shutdown_event = multiprocessing.Event()
            except Exception as e:
                logger.error(f"[CMF Manager] Failed to create new queues: {e}")
                raise RuntimeError(f"Recovery failed: cannot create communication channels: {e}")

            # Start new subprocess
            from cmflib.cmf_worker_loop import worker_loop
            self.worker_process = multiprocessing.Process(
                target=worker_loop,
                args=(self.task_queue, self.result_queue, self.shutdown_event),
                name="cmf-worker-subprocess",
                daemon=False
            )
            self.worker_process.start()
            logger.info(f"[CMF Manager] New worker subprocess started (PID: {self.worker_process.pid})")

            # Step 1: Re-initialise all registered sessions
            for session_id, init_kwargs in list(self._session_registry.items()):
                logger.info(f"[CMF Manager] Recovering session: {session_id}")
                reinit_task_id = str(uuid.uuid4())
                reinit_task = {
                    "task_id": reinit_task_id,
                    "session_id": session_id,
                    "method": "_init_session",
                    "kwargs": init_kwargs,
                    "timestamp": time.time()
                }
                if not self._safe_put_task(reinit_task):
                    raise RuntimeError(f"Recovery failed: cannot submit session init for {session_id}")
                self._wait_for_result(reinit_task_id)

            # Step 2: Replay confirmed tasks for each session in order
            failed_task_id = failed_task.get("task_id") if failed_task else None
            for session_id, log in list(self._task_log.items()):
                for entry in log:
                    if entry["task_id"] == failed_task_id:
                        # This task never fully completed; it will be re-submitted by submit_task
                        continue
                    replay_task_id = str(uuid.uuid4())
                    replay_task = {
                        "task_id": replay_task_id,
                        "session_id": session_id,
                        "method": entry["method"],
                        "kwargs": entry["kwargs"],
                        "timestamp": time.time()
                    }
                    if not self._safe_put_task(replay_task):
                        raise RuntimeError(f"Recovery failed: cannot replay task {replay_task_id}")
                    self._wait_for_result(replay_task_id)

            # Reset restart counter on successful recovery
            self._restart_count = 0
            logger.info("[CMF Manager] Recovery complete")

        finally:
            self._recovery_lock.release()  # GREEN light — all waiting threads unblock

    def _wait_for_result(self, task_id: str, timeout: float = 60.0):
        """
        Block until result for task_id arrives on result_queue.
        Used only during recovery replay (no crash-detection loop needed here).

        Args:
            task_id: ID of the task to wait for
            timeout: Maximum seconds to wait

        Raises:
            RuntimeError: If result indicates error or timeout exceeded
        """
        start = time.time()
        while True:
            try:
                result = self._safe_get_result(timeout=1.0)
                if result is None:
                    # Check timeout
                    if time.time() - start > timeout:
                        raise RuntimeError(f"[CMF Manager] Replay task {task_id} timed out")
                    continue
                    
                if result.get("task_id") == task_id:
                    if result.get("status") == "error":
                        raise RuntimeError(
                            f"[CMF Manager] Replay task {task_id} failed: {result.get('error')}"
                        )
                    return
                else:
                    if not self._safe_put_task(result, timeout=1.0):
                        logger.warning(f"[CMF Manager] Failed to return mismatched result during replay")
            except QueueBrokenError as e:
                raise RuntimeError(f"[CMF Manager] Queue broken during replay of task {task_id}: {e}")
    
    def shutdown(self, timeout: float = 10.0):
        """
        Gracefully shutdown the worker subprocess.
        
        Args:
            timeout: Maximum time to wait for subprocess to exit
        """
        if not self._started or self._shutdown_requested:
            return
        
        with self._lock:
            if self._shutdown_requested:
                return
            
            self._shutdown_requested = True
            
            logger.info("[CMF Manager] Shutting down worker subprocess")
            
            # Signal shutdown
            try:
                self.shutdown_event.set()
            except Exception as e:
                logger.warning(f"[CMF Manager] Error setting shutdown event: {e}")
            
            # Send poison pill with error handling
            try:
                if not self._safe_put_task(None, timeout=2.0):
                    logger.warning("[CMF Manager] Failed to send poison pill, will terminate subprocess")
            except Exception as e:
                logger.warning(f"[CMF Manager] Error sending poison pill: {e}")
            
            # Wait for subprocess to exit
            if self.worker_process.is_alive():
                self.worker_process.join(timeout=timeout)
                
                if self.worker_process.is_alive():
                    logger.warning("[CMF Manager] Subprocess did not exit gracefully, terminating")
                    self.worker_process.terminate()
                    self.worker_process.join(timeout=2.0)
                    
                    if self.worker_process.is_alive():
                        logger.error("[CMF Manager] Subprocess did not terminate, killing")
                        self.worker_process.kill()
                        self.worker_process.join()
            
            # Cleanup queues to prevent resource leaks
            self._cleanup_queues()
            
            # Final status
            if self.worker_process.exitcode == 0:
                logger.info("[CMF Manager] Worker subprocess exited cleanly")
            else:
                logger.warning(f"[CMF Manager] Worker subprocess exited with code {self.worker_process.exitcode}")
            
            self._started = False


class QueueBrokenError(Exception):
    """Raised when a queue operation fails due to broken/closed queue."""
    pass


# Global singleton instance (lazy initialization)
_manager: t.Optional[CmfSubprocessManager] = None


def get_manager() -> CmfSubprocessManager:
    """
    Get the global singleton manager instance.
    
    Returns:
        The CmfSubprocessManager singleton
    """
    global _manager
    if _manager is None:
        _manager = CmfSubprocessManager()
    return _manager
