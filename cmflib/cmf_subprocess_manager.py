"""
CMF Subprocess Manager - Singleton that manages the shared worker subprocess.

This module provides a singleton manager that:
1. Starts a single worker subprocess
2. Routes tasks from all Cmf instances to that subprocess
3. Handles results and errors
4. Gracefully shuts down the subprocess
"""

import multiprocessing
import threading
import atexit
import logging
import time
import uuid
import typing as t

logger = logging.getLogger(__name__)


class CmfSubprocessManager:
    """
    Singleton manager for the shared CMF worker subprocess.
    
    This class ensures that only ONE subprocess is created, no matter how many
    Cmf instances are created. All Cmf instances share this single subprocess.
    
    Thread-safe: Uses locks to prevent race conditions during initialization.
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
    
    def submit_task(
        self,
        session_id: str,
        method: str,
        kwargs: t.Dict,
        timeout: t.Optional[float] = None
    ) -> t.Any:
        """
        Submit a task to the worker subprocess and wait for the result.
        
        This is a blocking call - it waits for the subprocess to complete the task.
        
        Args:
            session_id: Unique identifier for the CMF session
            method: Name of the CMF method to call
            kwargs: Keyword arguments for the method
            timeout: Maximum time to wait for result (None = wait forever)
        
        Returns:
            Result from the method execution
        
        Raises:
            RuntimeError: If subprocess not started or task execution failed
            TimeoutError: If result not received within timeout
        """
        if not self._started:
            raise RuntimeError("Subprocess not started. Call start() first.")
        
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
        
        # Send task to subprocess
        self.task_queue.put(task)
        
        # Wait for result
        start_time = time.time()
        while True:
            try:
                result = self.result_queue.get(timeout=1.0)
                
                # Check if this is our result
                if result.get("task_id") == task_id:
                    if result.get("status") == "success":
                        logger.debug(f"[CMF Manager] Task {task_id} completed successfully")
                        return result.get("result")
                    
                    elif result.get("status") == "error":
                        error_msg = result.get("error", "Unknown error")
                        error_trace = result.get("traceback", "")
                        logger.error(f"[CMF Manager] Task {task_id} failed: {error_msg}")
                        raise RuntimeError(f"Task execution failed: {error_msg}\n{error_trace}")
                
                else:
                    # Not our result - put it back (shouldn't happen with FIFO execution)
                    logger.warning(f"[CMF Manager] Received result for wrong task: {result.get('task_id')}")
                    self.result_queue.put(result)
            
            except multiprocessing.queues.Empty:
                # Check timeout
                if timeout is not None and (time.time() - start_time) > timeout:
                    raise TimeoutError(f"Task {task_id} timed out after {timeout}s")
                
                # Check if subprocess is still alive
                if not self.worker_process.is_alive():
                    raise RuntimeError(f"Worker subprocess died while executing task {task_id}")
                
                continue
    
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
            self.shutdown_event.set()
            
            # Send poison pill
            self.task_queue.put(None)
            
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
            
            # Cleanup
            if self.worker_process.exitcode == 0:
                logger.info("[CMF Manager] Worker subprocess exited cleanly")
            else:
                logger.warning(f"[CMF Manager] Worker subprocess exited with code {self.worker_process.exitcode}")
            
            self._started = False


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
