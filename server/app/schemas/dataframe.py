from pydantic import BaseModel, HttpUrl
import pandas as pd
from typing import Sequence


class ExecutionDataFrame(BaseModel):
    context_id: str
    context_type: str
    execution: str
