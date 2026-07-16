"""
CMF Async API - Lightweight proxy for async CMF logging.

This module provides CmfAsyncProxy, a lightweight wrapper that submits tasks
to the shared worker subprocess. Multiple CmfAsyncProxy instances share one subprocess.
"""

import logging
import typing as t
import uuid

from cmflib.cmf_subprocess_manager import get_manager

logger = logging.getLogger(__name__)


class CmfAsyncProxy:
    """
    Lightweight async proxy for CMF.
    
    This class provides the same interface as Cmf, but all operations are
    executed in a shared worker subprocess. Multiple CmfAsyncProxy instances
    share the same subprocess, avoiding resource exhaustion.
    
    Example:
        ```python
        # Create multiple Cmf instances - they all share one subprocess
        cmf1 = Cmf(pipeline_name="pipeline1", async_logging=True)
        cmf2 = Cmf(pipeline_name="pipeline2", async_logging=True)
        
        # Operations are queued to the shared subprocess
        cmf1.log_dataset("data.csv", event="input")
        cmf2.log_model("model.pkl", event="output")
        
        # Finalize and wait for completion
        cmf1.finalize()
        cmf2.finalize()
        ```
    
    Args:
        filepath: Path to metadata store
        pipeline_name: Name of the pipeline
        custom_properties: Pipeline custom properties
        graph: Whether to use graph database
        finalize_timeout: Timeout for finalize() in seconds
    """
    
    def __init__(
        self,
        filepath: str = "mlmd",
        pipeline_name: str = "",
        custom_properties: t.Optional[t.Dict] = None,
        graph: bool = False,
        finalize_timeout: int = 300,
    ):
        # Generate unique session ID
        self._session_id = f"{pipeline_name}_{uuid.uuid4().hex[:8]}"
        
        # Store parameters
        self._worker_params = {
            'filepath': filepath,
            'pipeline_name': pipeline_name,
            'custom_properties': custom_properties or {},
            'graph': graph,
        }
        
        self.filepath = filepath
        self.pipeline_name = pipeline_name
        self.finalize_timeout = finalize_timeout
        
        # Get the singleton manager
        self._manager = get_manager()
        
        # Start subprocess if not already started
        self._manager.start()
        
        # Initialize this session in the worker subprocess
        self._submit_task("_init_session", **self._worker_params)
        
        logger.info(f"[CmfAsyncProxy] Created session {self._session_id}")
    
    def _submit_task(self, method: str, **kwargs) -> t.Any:
        """
        Submit a task to the worker subprocess.
        
        This is a blocking call - it waits for the subprocess to complete
        the task and return the result.
        
        Args:
            method: Name of the CMF method to call
            **kwargs: Keyword arguments for the method
        
        Returns:
            Result from the method execution
        """
        return self._manager.submit_task(
            session_id=self._session_id,
            method=method,
            kwargs=kwargs,
            timeout=self.finalize_timeout
        )
    
    # Public API - mirrors Cmf interface
    
    def create_context(
        self, pipeline_stage: str, custom_properties: t.Optional[t.Dict] = None
    ):
        """Create context (executed in worker subprocess)."""
        return self._submit_task(
            "create_context",
            pipeline_stage=pipeline_stage,
            custom_properties=custom_properties
        )
    
    def update_context(
        self,
        type_name: str,
        context_name: str,
        context_id: int,
        properties: t.Optional[t.Dict] = None,
        custom_properties: t.Optional[t.Dict] = None
    ):
        """Update context (executed in worker subprocess)."""
        return self._submit_task(
            "update_context",
            type_name=type_name,
            context_name=context_name,
            context_id=context_id,
            properties=properties,
            custom_properties=custom_properties
        )
    
    def create_execution(
        self,
        execution_type: str,
        custom_properties: t.Optional[t.Dict] = None,
        cmd: t.Optional[str] = None,
        create_new_execution: bool = True,
    ):
        """Create execution (executed in worker subprocess)."""
        return self._submit_task(
            "create_execution",
            execution_type=execution_type,
            custom_properties=custom_properties,
            cmd=cmd,
            create_new_execution=create_new_execution
        )
    
    def update_execution(
        self, execution_id: int, custom_properties: t.Optional[t.Dict] = None
    ):
        """Update execution (executed in worker subprocess)."""
        return self._submit_task(
            "update_execution",
            execution_id=execution_id,
            custom_properties=custom_properties
        )
    
    def log_dataset(
        self,
        url: str,
        event: str,
        custom_properties: t.Optional[t.Dict] = None,
        label: t.Optional[str] = None,
        label_properties: t.Optional[t.Dict] = None,
        external: bool = False,
    ):
        """Log dataset (executed in worker subprocess)."""
        return self._submit_task(
            "log_dataset",
            url=url,
            event=event,
            custom_properties=custom_properties,
            label=label,
            label_properties=label_properties,
            external=external
        )
    
    def log_model(
        self,
        path: str,
        event: str,
        model_framework: str = "Default",
        model_type: str = "Default",
        model_name: str = "Default",
        custom_properties: t.Optional[t.Dict] = None,
    ):
        """Log model (executed in worker subprocess)."""
        return self._submit_task(
            "log_model",
            path=path,
            event=event,
            model_framework=model_framework,
            model_type=model_type,
            model_name=model_name,
            custom_properties=custom_properties
        )
    
    def log_execution_metrics(
        self, metrics_name: str, custom_properties: t.Optional[t.Dict] = None
    ):
        """Log execution metrics (executed in worker subprocess)."""
        return self._submit_task(
            "log_execution_metrics",
            metrics_name=metrics_name,
            custom_properties=custom_properties
        )
    
    def log_metric(
        self, metrics_name: str, custom_properties: t.Optional[t.Dict] = None
    ):
        """Log metric (executed in worker subprocess)."""
        return self._submit_task(
            "log_metric",
            metrics_name=metrics_name,
            custom_properties=custom_properties
        )
    
    def commit_metrics(self, metrics_name: str):
        """Commit metrics (executed in worker subprocess)."""
        return self._submit_task(
            "commit_metrics",
            metrics_name=metrics_name
        )
    
    def finalize(self):
        """
        Finalize the CMF logging session.
        
        Blocks until the worker subprocess completes the finalize operation.
        """
        logger.info(f"[CmfAsyncProxy] Finalizing session {self._session_id}")
        
        # Execute finalize in subprocess (blocking)
        self._submit_task("finalize")
        
        # Cleanup this session
        self._submit_task("_cleanup_session")
        
        logger.info(f"[CmfAsyncProxy] Session {self._session_id} finalized")


def shutdown_worker(timeout: float = 10.0):
    """
    Shutdown the shared worker subprocess.
    
    This is called automatically at program exit. You can also call it manually
    if you want to explicitly shutdown the subprocess before program exit.
    
    Args:
        timeout: Maximum time to wait for subprocess to exit
    """
    manager = get_manager()
    manager.shutdown(timeout=timeout)
