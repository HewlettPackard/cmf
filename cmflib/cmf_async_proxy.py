"""
Asynchronous proxy for CMF metadata logging.
This module provides a lightweight proxy that queues commands to a worker process.
"""

###
# Copyright (2024) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

import os
import sys
import time
import traceback
import multiprocessing
import atexit
import typing as t
import logging

logger = logging.getLogger(__name__)


class CmfAsyncProxy:
    """
    Lightweight async proxy for CMF.
    
    This class runs in the main process and only queues commands to a worker process.
    It does NOT open database connections, create contexts, or do any heavy lifting.
    All actual work happens in the worker process.
    
    Args:
        filename: Path to metadata store
        pipeline_name: Name of the pipeline
        custom_properties: Pipeline custom properties
        graph: Whether to use graph database
        finalize_timeout: Timeout for finalize() in seconds
    """
    
    def __init__(
        self,
        filename: str = "mlmd",
        pipeline_name: str = "",
        custom_properties: t.Optional[t.Dict] = None,
        graph: bool = False,
        finalize_timeout: int = 300,
    ):
        # Store only parameters needed for worker
        self._worker_params = {
            'filename': filename,
            'pipeline_name': pipeline_name,
            'custom_properties': custom_properties or {},
            'graph': graph,
        }
        
        self.filename = filename
        self.pipeline_name = pipeline_name
        self.finalize_timeout = finalize_timeout
        
        # Initialize IPC and spawn worker
        self._command_queue: t.Optional[multiprocessing.Queue] = None
        self._child_process: t.Optional[multiprocessing.Process] = None
        self._call_id_counter = 0
        
        self._setup_worker()
        
        # Register cleanup on exit
        atexit.register(self._emergency_cleanup)
    
    def _setup_worker(self):
        """Initialize worker process and communication queue."""
        logger.info("[CmfAsyncProxy] Initializing async logging with worker process")
        
        # Create communication queue
        self._command_queue = multiprocessing.Queue()
        
        # Spawn worker process
        self._child_process = multiprocessing.Process(
            target=_worker_process_main,
            args=(self._command_queue, self._worker_params),
            name=f"cmf-worker-{self.pipeline_name}"
        )
        
        # Start the worker
        self._child_process.start()
        logger.info(f"[CmfAsyncProxy] Worker process started (PID: {self._child_process.pid})")
    
    def _queue_command(self, method_name: str, **kwargs):
        """
        Queue a command to be executed by the worker process.
        
        Args:
            method_name: Name of the CMF method to execute
            **kwargs: Keyword arguments for the method
        """
        if self._command_queue is None:
            raise RuntimeError("Worker not initialized")
        
        self._call_id_counter += 1
        message = {
            "method": method_name,
            "kwargs": kwargs,
            "timestamp": time.time(),
            "call_id": self._call_id_counter
        }
        
        try:
            self._command_queue.put(message, block=False)
        except Exception as e:
            logger.error(f"[CmfAsyncProxy] Failed to queue command {method_name}: {e}")
            raise
    
    def _check_error_log(self):
        """Check error log and raise exception if errors were encountered."""
        error_log_path = f"{self.filename}_errors.log"
        if os.path.exists(error_log_path):
            with open(error_log_path, "r") as f:
                errors = f.read()
            if errors.strip():
                error_count = errors.count("ERROR in")
                raise RuntimeError(
                    f"CMF metadata logging encountered {error_count} error(s). "
                    f"Check {error_log_path} for details:\n\n{errors[:500]}..."
                )
    
    def _emergency_cleanup(self):
        """Emergency cleanup if program exits without calling finalize()."""
        if self._child_process and self._child_process.is_alive():
            logger.warning("[CmfAsyncProxy] Emergency cleanup: terminating worker process")
            try:
                if self._command_queue:
                    self._command_queue.put({"method": "shutdown"}, block=False)
                self._child_process.join(timeout=5)
                if self._child_process.is_alive():
                    logger.warning("[CmfAsyncProxy] Emergency cleanup: force terminating")
                    self._child_process.terminate()
                    # Add join() after terminate() to ensure cleanup and prevent zombie process
                    self._child_process.join(timeout=2)
            except Exception as e:
                logger.error(f"[CmfAsyncProxy] Emergency cleanup error: {e}")
    
    # Public API methods - all just queue commands
    
    def create_context(self, pipeline_stage: str, custom_properties: t.Optional[t.Dict] = None):
        """Create context (queued to worker)."""
        self._queue_command("create_context", 
                           pipeline_stage=pipeline_stage,
                           custom_properties=custom_properties)
        return None
    
    def update_context(
        self,
        type_name: str,
        context_name: str,
        context_id: int,
        properties: t.Optional[t.Dict] = None,
        custom_properties: t.Optional[t.Dict] = None
    ):
        """Update context (queued to worker)."""
        self._queue_command("update_context",
                           type_name=type_name,
                           context_name=context_name,
                           context_id=context_id,
                           properties=properties,
                           custom_properties=custom_properties)
        return None
    
    def create_execution(
        self,
        execution_type: str,
        custom_properties: t.Optional[t.Dict] = None,
        cmd: t.Optional[str] = None,
        create_new_execution: bool = True,
    ):
        """Create execution (queued to worker)."""
        self._queue_command("create_execution",
                           execution_type=execution_type,
                           custom_properties=custom_properties,
                           cmd=cmd,
                           create_new_execution=create_new_execution)
        return None
    
    def update_execution(self, execution_id: int, custom_properties: t.Optional[t.Dict] = None):
        """Update execution (queued to worker)."""
        self._queue_command("update_execution",
                           execution_id=execution_id,
                           custom_properties=custom_properties)
        return None
    
    def log_dataset(
        self,
        url: str,
        event: str,
        custom_properties: t.Optional[t.Dict] = None,
        label: t.Optional[str] = None,
        label_properties: t.Optional[t.Dict] = None,
        external: bool = False,
    ):
        """Log dataset (queued to worker)."""
        self._queue_command("log_dataset",
                           url=url,
                           event=event,
                           custom_properties=custom_properties,
                           label=label,
                           label_properties=label_properties,
                           external=external)
        return None
    
    def log_model(
        self,
        path: str,
        event: str,
        model_framework: str = "Default",
        model_type: str = "Default",
        model_name: str = "Default",
        custom_properties: t.Optional[t.Dict] = None,
    ):
        """Log model (queued to worker)."""
        self._queue_command("log_model",
                           path=path,
                           event=event,
                           model_framework=model_framework,
                           model_type=model_type,
                           model_name=model_name,
                           custom_properties=custom_properties)
        return None
    
    def log_execution_metrics(
        self, metrics_name: str, custom_properties: t.Optional[t.Dict] = None
    ):
        """Log execution metrics (queued to worker)."""
        self._queue_command("log_execution_metrics",
                           metrics_name=metrics_name,
                           custom_properties=custom_properties)
        return None
    
    def log_metric(
        self, metrics_name: str, custom_properties: t.Optional[t.Dict] = None
    ):
        """Log metric (queued to worker)."""
        self._queue_command("log_metric",
                           metrics_name=metrics_name,
                           custom_properties=custom_properties)
        return None
    
    def commit_metrics(self, metrics_name: str):
        """Commit metrics (queued to worker)."""
        self._queue_command("commit_metrics",
                           metrics_name=metrics_name)
        return None
    
    def finalize(self):
        """
        Finalize the CMF logging session.
        
        Blocks until all queued operations complete in the worker process.
        """
        if not self._child_process:
            return
        
        logger.info("[CmfAsyncProxy] Finalizing async logging session")
        
        # Queue finalize command
        self._queue_command("finalize")
        
        # Queue shutdown command
        self._command_queue.put({"method": "shutdown"})
        
        # Wait for worker to complete
        logger.info(f"[CmfAsyncProxy] Waiting for worker (timeout: {self.finalize_timeout}s)")
        self._child_process.join(timeout=self.finalize_timeout)
        
        # Check if process is still alive
        if self._child_process.is_alive():
            logger.error("[CmfAsyncProxy] Worker timeout - terminating")
            self._child_process.terminate()
            self._child_process.join(timeout=5)
            raise TimeoutError(
                f"Worker process did not complete within {self.finalize_timeout} seconds"
            )
        
        # Check exit code
        if self._child_process.exitcode != 0:
            logger.warning(f"[CmfAsyncProxy] Worker exited with code {self._child_process.exitcode}")
        
        # Check for errors
        self._check_error_log()
        
        logger.info("[CmfAsyncProxy] Async logging session finalized successfully")


def _worker_process_main(command_queue: multiprocessing.Queue, worker_params: dict):
    """
    Main entry point for worker process.
    
    This function runs in a separate process and handles CMF commands from the queue.
    It creates a full Cmf instance (synchronous) and processes commands until shutdown.
    
    Args:
        command_queue: Queue to receive commands from main process
        worker_params: Parameters for creating Cmf instance
    """
    logger.info(f"[Worker] Process started (PID: {os.getpid()})")
    
    # Import here to avoid circular dependency
    from cmflib.cmf import Cmf
    
    try:
        # Create full CMF instance in worker process (synchronous mode)
        logger.info("[Worker] Initializing Cmf...")
        cmf_worker = Cmf(
            **worker_params,
            async_logging=False  # Worker always uses synchronous mode
        )
        logger.info("[Worker] Cmf initialized, entering command loop")
        
        error_log_path = f"{worker_params['filename']}_errors.log"
        
        # Main loop - process commands until shutdown
        while True:
            try:
                # Block waiting for next command
                message = command_queue.get()
                
                method_name = message.get("method")
                
                if method_name == "shutdown":
                    logger.info("[Worker] Received shutdown signal")
                    break
                
                # Execute the command
                logger.debug(f"[Worker] Executing {method_name}")
                method = getattr(cmf_worker, method_name)
                method(**message.get("kwargs", {}))
                
            except KeyboardInterrupt:
                logger.info("[Worker] Received keyboard interrupt")
                break
                
            except Exception as e:
                # Log error but continue processing
                logger.error(f"[Worker] Error executing {method_name}: {e}")
                try:
                    with open(error_log_path, "a") as f:
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"\n[{timestamp}] ERROR in {method_name}\n")
                        f.write(f"  Call ID: {message.get('call_id', 'N/A')}\n")
                        f.write(f"  Error: {type(e).__name__}: {str(e)}\n")
                        f.write(f"  Traceback:\n")
                        f.write(traceback.format_exc())
                        f.write("\n" + "="*80 + "\n")
                except:
                    pass
    
    except Exception as e:
        logger.error(f"[Worker] Fatal error in worker process: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Cleanup
        try:
            if hasattr(cmf_worker, 'driver') and cmf_worker.graph and cmf_worker.driver:
                cmf_worker.driver.close()
        except:
            pass
        logger.info("[Worker] Process shutting down")
