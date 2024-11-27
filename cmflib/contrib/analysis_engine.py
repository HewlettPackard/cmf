###
# Copyright (2023) Hewlett Packard Enterprise Development LP
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

"""
This module defines a number of analysis engines that provide domain- or task-specific analytic functions that can
be performed on AI pipeline metadata.

# Utility classes
Different analysis engines can consume data in various flavours, such as tabular- or graph-based representation. The
`MetricSource` class can be used to enable some or all of the implemented analysis engines access data stored
differently. Internally, two classes  are implemented -  `_TabularMetricSource` and `_GraphMetricSource`.


# Analysis engine classes
Each analysis engine implements one or multiple related analytic functions. The following analysis engines are
implemented.

## Parameter sensitivity analysis engine
This engine can be used to identify how a machine learning metric like accuracy depends on a particular parameter such
as learning rate.
"""

import abc
import typing as t

import numpy as np
import pandas as pd
from contrib.graph_api import Artifact, Type

__all__ = ["MetricSource", "ParameterSensitivityReport", "ParameterSensitivityAnalysisEngine"]


class MetricSource(abc.ABC):
    """Class that provides standard interface for getting metric values.

    This class is public to enable users define their own sources.
    """

    @abc.abstractmethod
    def values(self, metric_name: str) -> np.ndarray:
        """Retrieve metric values for the given metric.

        Args:
            metric_name: Name of a metric.
        Returns:
            One-rank numpy array containing metric values.
        """
        raise NotImplementedError


class ParameterSensitivityReport:
    """Class that provides information on how sensitive an AI pipeline is with respect to a given parameter.

    Instances of this class are created by the `ParameterSensitivityAnalysisEngine` class.

    Args:
         parameter_name: Name of a parameter (e.g., learning_rate).
         metric_name: Machine learning metric name (e.g., accuracy).
    """

    def __init__(self, parameter_name: t.Optional[str], metric_name: str) -> None:
        self.parameter_name = parameter_name
        """Parameter name that this report is built for (e.g., learning_rate)."""

        self.metric_name = metric_name
        """Machine learning metric this report is built for (e.g., accuracy)."""

        self.metric_vals: t.Optional[np.ndarray] = None
        """Values for the `metric_name` metric."""

    def to_json(self) -> t.Dict:
        """Convert report into JSON-compatible dictionary object.

        Returns:
            JSON-compatible dictionary.
        """
        return {
            "parameter_name": self.parameter_name,
            "metric_name": self.metric_name,
            "metric_vals": self.metric_vals.tolist(),
        }

    @classmethod
    def from_json(cls, data: t.Dict) -> "ParameterSensitivityReport":
        """Create report from a dictionary.

        Args:
            data: Dictionary containing at least three fields - "parameter_name", "metric_name" and "metric_vals".
        Returns:
            Instance of a `ParameterSensitivityReport` class.
        """
        report = ParameterSensitivityReport(data["parameter_name"], data["metric_name"])
        report.metric_vals = np.asarray(data["metric_vals"], dtype=np.float64)
        return report

    def log_with_cmf(self, logger: object) -> None:
        """Log as CMF artifact (execution metrics).

        TODO (sergey): the `metrics_name` fields for this and other methods should probably be declared centrally.
        TODO (sergey): implementation not tested - will custom_properties accept list of items?

        Args:
            logger: Instance of `Cmf` class.
        """
        from cmflib import cmf

        if not isinstance(logger, cmf.Cmf):
            raise ValueError(f"Invalid logger (type={type(logger)}). Expected type is `{cmf.Cmf}`.")
        logger.log_execution_metrics(
            metrics_name="AnalyticEngine_ParameterSensitivityReport", custom_properties=self.to_json()
        )


class ParameterSensitivityAnalysisEngine:
    """Perform sensitivity analysis on how ML metric depends on a particular parameter.

    Sensitivity analysis explains how a metric varies depending on one (hyper-) parameter. For instance, if one wants
    to analysis how stable their hyperparameters are, they can run multiple training sessions varying random seed.

    Args:
        parameter_name: Name of a parameter that is under investigation (used only for reporting).
        metric_source: An instance of the `MetricSource` class that retrieves metric values.
    """

    def __init__(self, parameter_name: str, metric_source: t.Optional[MetricSource] = None) -> None:
        self._parameter_name = parameter_name
        self._metric_source = metric_source

    @classmethod
    def from_graph(cls, parameter_name: str, artifacts: t.List[Artifact]) -> "ParameterSensitivityAnalysisEngine":
        """Construct analysis engine from the graph data.

        Args:
            parameter_name: Name of a parameter that is under investigation (used only for reporting).
            artifacts: List of artifacts that must represent execution metrics.
        Returns:
            Instance of `ParameterSensitivityAnalysisEngine` that brings together various pieces of information that are
                useful for building sensitivity analysis reports.
        """
        return ParameterSensitivityAnalysisEngine(parameter_name, _GraphMetricSource(artifacts))

    @classmethod
    def from_table(cls, parameter_name: str, df: pd.DataFrame) -> "ParameterSensitivityAnalysisEngine":
        """Construct analysis engine from the tabular data.

        Args:
            parameter_name: Name of a parameter that is under investigation (used only for reporting).
            df: Pandas data frame containing various columns including performance metrics.
        Returns:
            Instance of `ParameterSensitivityAnalysisEngine` that brings together various pieces of information that are
                useful for building sensitivity analysis reports.
        """
        return ParameterSensitivityAnalysisEngine(parameter_name, _TableMetricSource(df))

    def analyze(self, metric_name: str) -> ParameterSensitivityReport:
        """Analyze experiment data and consolidate results in a report."""
        report = ParameterSensitivityReport(self._parameter_name, metric_name)
        report.metric_vals = self._metric_source.values(metric_name)
        return report


class _TableMetricSource(MetricSource):
    """Class that returns columns of pandas data frames (works with tabular API).

    This class should be used in static/class analysis engine methods such as `from_table`.

    Args:
        df: Pandas data frame containing various columns including performance metrics.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def values(self, metric_name: str) -> np.ndarray:
        return self._df[metric_name].values


class _GraphMetricSource(MetricSource):
    """Class that returns metric values given list of graph nodes (artifacts).

    This class should be used in static/class analysis engine methods such as `from_graph`. Implementation is based on
    the following assumptions:
        - Execution metrics are artifacts of `Type.METRICS` type.
        - The `metrics_name` entry of artifact properties define the name of a metrics group (e.g., train_metrics). All
          artifacts must belong to the same group.
        - The metric of interest is stored in `custom_properties` field of artifacts. The key must present and the value
          must not be null.

    Args:
        artifacts: List of artifacts that must represent execution metrics.
    """

    def __init__(self, artifacts: t.List[Artifact]) -> None:
        self._artifacts = artifacts

    def values(self, metric_name: str) -> np.ndarray:
        metric_group: t.Optional[str] = None  # E.g., train_metrics, test_metrics, etc.
        metric_vals = np.empty(shape=(len(self._artifacts),), dtype=np.float64)
        for idx, artifact in enumerate(self._artifacts):
            self._check_artifact_is_execution_metrics(idx, artifact)
            metric_group = self._check_metric_group_is_same(idx, metric_group, artifact)
            metric_value = artifact.custom_properties.get(metric_name, None)
            self._check_metric_value(idx, artifact, metric_name, metric_value)
            metric_vals[idx] = float(metric_value)
        return metric_vals

    @staticmethod
    def _check_artifact_is_execution_metrics(idx: int, artifact: Artifact) -> None:
        if artifact.type.name != Type.METRICS:
            raise ValueError(
                f"Invalid artifact (idx={idx}, artifact={artifact}). Expecting `{Type.METRICS}` type. To"
                f"resolve this, make sure to retrieve only those MLMD artifacts that have `{Type.METRICS}` type."
            )

    @staticmethod
    def _check_metric_group_is_same(idx: int, metric_group: t.Optional[str], artifact: Artifact) -> str:
        _this_metric_group = artifact.properties["metrics_name"]
        if metric_group is None:
            metric_group = _this_metric_group
        else:
            if metric_group != _this_metric_group:
                raise ValueError(
                    f"Metric group names do not match. Execution metrics (idx={idx}, artifact={artifact}) "
                    f"have group name `{_this_metric_group}`. Expected group name is `{metric_group}`. To resolve "
                    "this, use `Artifact.properties.metrics_name` (group name) field for filtering execution "
                    "metric artifacts."
                )
        return metric_group

    @staticmethod
    def _check_metric_value(idx: int, artifact: Artifact, metric_name: str, metric_value: t.Any) -> None:
        if metric_value is None:
            raise ValueError(
                f"No target metric (metric_name={metric_name}) reported in execution metrics (idx={idx}, "
                f"artifact={artifact}). To resolve this, filter execution metrics by "
                "`Artifact.custom_properties.'metric_name'` field (the `metric_name` key must exist in "
                "custom_properties) and be not None. "
            )
        if isinstance(metric_value, (int, bool)):
            raise NotImplementedError(
                f"Metric (name={metric_name}, value={metric_value}, value_type={type(metric_value)}) in execution "
                f"metrics (idx={idx}, artifact={artifact}) is not supported yet. If type is `int`, convert "
                f"every value to floating point number (integers should define metrics with categorical values)."
            )
        if not isinstance(metric_value, float):
            raise ValueError(
                f"Metric (name={metric_name}) in execution metrics artifact (idx={idx}, "
                f"artifact={artifact}) has the wrong type (type=`{type(metric_value)}`). Expected type is"
                "`float`. "
            )
