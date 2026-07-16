"""
CMF Worker Loop - Runs in the subprocess.

This module contains the worker loop that executes CMF operations in a separate process.
All CMF instances in the main process share this single worker subprocess.
"""

import multiprocessing
import traceback
import logging
import time
import typing as t

logger = logging.getLogger(__name__)


def worker_loop(
    task_queue: multiprocessing.Queue,
    result_queue: multiprocessing.Queue,
    shutdown_event: multiprocessing.Event
):
    """
    Main worker loop that runs in the subprocess.
    
    This loop:
    1. Pulls tasks from task_queue
    2. Executes the task (CMF operations)
    3. Puts the result back in result_queue
    4. Continues until shutdown_event is set
    
    Args:
        task_queue: Queue to receive tasks from main process
        result_queue: Queue to send results back to main process
        shutdown_event: Event to signal shutdown
    """
    logger.info(f"[CMF Worker] Worker subprocess started (PID: {multiprocessing.current_process().pid})")
    
    # Import here to avoid circular dependency and to keep imports isolated in subprocess
    from cmflib.cmf import Cmf
    
    # Map session_id -> Cmf instance
    # Each Cmf object in main process gets a corresponding real Cmf instance here
    cmf_sessions: t.Dict[str, Cmf] = {}
    
    try:
        while not shutdown_event.is_set():
            try:
                # Wait for next task (with timeout to check shutdown_event)
                task = task_queue.get(timeout=1.0)
                
                if task is None:  # Poison pill
                    logger.info("[CMF Worker] Received poison pill, shutting down")
                    break
                
                # Extract task details
                task_id = task.get("task_id")
                session_id = task.get("session_id")
                method = task.get("method")
                kwargs = task.get("kwargs", {})
                
                logger.debug(f"[CMF Worker] Executing task {task_id}: {session_id}.{method}")
                
                # Execute the task
                result = execute_task(
                    cmf_sessions=cmf_sessions,
                    session_id=session_id,
                    method=method,
                    kwargs=kwargs
                )
                
                # Send result back
                result_queue.put({
                    "task_id": task_id,
                    "status": "success",
                    "result": result
                })
                
            except multiprocessing.queues.Empty:
                # Timeout - just check shutdown_event again
                continue
                
            except Exception as e:
                # Task execution error - send back error result
                logger.error(f"[CMF Worker] Error executing task {task_id}: {e}")
                result_queue.put({
                    "task_id": task_id,
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
    
    except KeyboardInterrupt:
        logger.info("[CMF Worker] Interrupted by keyboard")
    
    except Exception as e:
        logger.error(f"[CMF Worker] Fatal error in worker loop: {e}")
        traceback.print_exc()
    
    finally:
        # Cleanup: close all Cmf sessions
        logger.info("[CMF Worker] Cleaning up CMF sessions")
        for session_id, cmf in list(cmf_sessions.items()):
            try:
                if hasattr(cmf, 'driver') and cmf.graph and cmf.driver:
                    cmf.driver.close()
            except Exception as e:
                logger.error(f"[CMF Worker] Error closing session {session_id}: {e}")
        
        logger.info("[CMF Worker] Worker subprocess shutting down")


def execute_task(
    cmf_sessions: t.Dict[str, t.Any],
    session_id: str,
    method: str,
    kwargs: t.Dict
) -> t.Any:
    """
    Execute a CMF task.
    
    Routes the method call to the appropriate handler based on the method name.
    
    Args:
        cmf_sessions: Dictionary mapping session_id to Cmf instances
        session_id: Unique identifier for the CMF session
        method: Name of the CMF method to call
        kwargs: Keyword arguments for the method
    
    Returns:
        Result of the method execution (usually None for logging operations)
    """
    # Special commands for session management
    if method == "_init_session":
        return _init_session_handler(cmf_sessions, session_id, kwargs)
    
    elif method == "_cleanup_session":
        return _cleanup_session_handler(cmf_sessions, session_id)
    
    # Regular CMF methods
    elif session_id not in cmf_sessions:
        raise ValueError(f"Session {session_id} not found. Call _init_session first.")
    
    # Get the Cmf instance for this session
    cmf = cmf_sessions[session_id]
    
    # Call the method on the Cmf instance
    method_func = getattr(cmf, method)
    result = method_func(**kwargs)
    
    return result


def _init_session_handler(
    cmf_sessions: t.Dict[str, t.Any],
    session_id: str,
    kwargs: t.Dict
) -> str:
    """
    Initialize a new CMF session.
    
    Creates a real Cmf instance (synchronous mode) for this session.
    
    Args:
        cmf_sessions: Dictionary to store the new session
        session_id: Unique identifier for this session
        kwargs: Parameters to pass to Cmf constructor
    
    Returns:
        Success message
    """
    from cmflib.cmf import Cmf
    
    logger.info(f"[CMF Worker] Initializing session: {session_id}")
    
    # Create a real Cmf instance in synchronous mode
    cmf_sessions[session_id] = Cmf(
        **kwargs,
        async_logging=False  # IMPORTANT: Worker always uses synchronous mode
    )
    
    logger.info(f"[CMF Worker] Session {session_id} initialized")
    return f"Session {session_id} initialized"


def _cleanup_session_handler(
    cmf_sessions: t.Dict[str, t.Any],
    session_id: str
) -> str:
    """
    Clean up a CMF session.
    
    Closes resources and removes the session from the dictionary.
    
    Args:
        cmf_sessions: Dictionary containing sessions
        session_id: Session to clean up
    
    Returns:
        Success message
    """
    if session_id not in cmf_sessions:
        logger.warning(f"[CMF Worker] Cleanup: Session {session_id} not found")
        return f"Session {session_id} not found"
    
    logger.info(f"[CMF Worker] Cleaning up session: {session_id}")
    
    cmf = cmf_sessions[session_id]
    
    # Close graph driver if exists
    try:
        if hasattr(cmf, 'driver') and cmf.graph and cmf.driver:
            cmf.driver.close()
    except Exception as e:
        logger.error(f"[CMF Worker] Error closing driver for {session_id}: {e}")
    
    # Remove from dictionary
    del cmf_sessions[session_id]
    
    logger.info(f"[CMF Worker] Session {session_id} cleaned up")
    return f"Session {session_id} cleaned up"
