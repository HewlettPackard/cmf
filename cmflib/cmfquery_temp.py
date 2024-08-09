import json
import logging
import typing as t
import pandas as pd
import time
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto import metadata_store_pb2 as mlpb
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.concurrency import run_in_threadpool
from typing import List
from cmflib.mlmd_objects import CONTEXT_LIST

class CmfQuery(object):
    """CMF Query communicates with the MLMD database and implements basic search and retrieval functionality.

    This class has been designed to work with the CMF framework. CMF alters names of pipelines, stages and artifacts
    in various ways. This means that actual names in the MLMD database will be different from those originally provided
    by users via CMF API. When methods in this class accept `name` parameters, it is expected that values of these
    parameters are fully-qualified names of respective entities.


    Args:
        filepath: Path to the MLMD database file.
    """

    def __init__(self, filepath: str = "mlmd") -> None:
        config = mlpb.ConnectionConfig()
        config.sqlite.filename_uri = filepath
        self.store = metadata_store.MetadataStore(config)
	
    def get_all_artifacts(self) -> t.List[str]:
        """Return names of all artifacts.

        Returns:
            List of all artifact names.
        """
        time.sleep(100)
        return [artifact.name for artifact in self.store.get_artifacts()]

    async def async_get_artifacts(self) :
        return await run_in_threadpool(self.get_all_artifacts)
"""


    async def async_get_artifacts(self) -> List[mlpb.Context]:
        return await loop.run_in_executor(executor, self.get_all_artifacts)
"""
