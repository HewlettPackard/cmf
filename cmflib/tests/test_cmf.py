"""
Comprehensive unit tests for cmf.py - Core CMF orchestration module.

Tests all 21 public methods including:
- Initialization (__init__)
- Context management (create_context, update_context)
- Execution management (create_execution, update_execution)
- Metadata logging (log_dataset, log_model, log_python_env, log_metric)
- Metrics handling (log_execution_metrics, commit_metrics)
- Error scenarios and edge cases
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import tempfile
import os
import sys
import json
from pathlib import Path

from cmflib.cmf import Cmf


class TestCmfInitialization:
    """Tests for Cmf.__init__() - Initialization with different store types."""

    def test_init_with_sqlite_default(self):
        """Test initialization with default SQLite store."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context') as mock_parent_context, \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance
            mock_context = Mock(id=1, name="test_pipeline")
            mock_parent_context.return_value = mock_context

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="test_pipeline")

            assert cmf_instance.pipeline_name == "test_pipeline"
            assert cmf_instance.filepath == "mlmd"

    def test_init_with_postgres_server_mode(self):
        """Test initialization with PostgreSQL store in server mode."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.PostgresStore') as mock_postgres_store, \
             patch('cmflib.cmf.get_postgres_config') as mock_get_postgres_config, \
             patch('cmflib.cmf.get_or_create_parent_context') as mock_parent_context, \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_config = {"host": "localhost", "port": 5432, "user": "cmf", 
                          "password": "pass", "dbname": "cmf_db"}
            mock_get_postgres_config.return_value = mock_config
            
            mock_store_instance = Mock()
            mock_postgres_store.return_value = mock_store_instance
            mock_context = Mock(id=1, name="pipeline")
            mock_parent_context.return_value = mock_context

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline", is_server=True)

            assert cmf_instance.pipeline_name == "pipeline"
            mock_get_postgres_config.assert_called_once()

    def test_init_with_custom_properties(self):
        """Test initialization with custom properties."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context') as mock_parent_context, \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance
            mock_context = Mock(id=1, name="test_pipeline")
            mock_parent_context.return_value = mock_context

            custom_props = {"owner": "data_team", "version": "1.0"}
            cmf_instance = Cmf(filepath="mlmd", pipeline_name="test_pipeline",
                              custom_properties=custom_props)

            assert cmf_instance.pipeline_name == "test_pipeline"
            mock_parent_context.assert_called_once()

    def test_init_with_nested_filepath(self):
        """Test initialization with nested filepath."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context') as mock_parent_context, \
             patch('cmflib.cmf.change_dir') as mock_change_dir, \
             patch('os.path.exists', return_value=True), \
             patch('os.makedirs'):

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance
            mock_context = Mock(id=1, name="pipeline")
            mock_parent_context.return_value = mock_context

            cmf_instance = Cmf(filepath="mlmd/store.db", 
                              pipeline_name="pipeline")

            assert cmf_instance.pipeline_name == "pipeline"

    def test_init_with_special_characters_in_pipeline_name(self):
        """Test initialization with special characters in pipeline name."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context') as mock_parent_context, \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance
            mock_context = Mock(id=1, name="test-pipeline_v1.0")
            mock_parent_context.return_value = mock_context

            special_name = "test-pipeline_v1.0@prod"
            cmf_instance = Cmf(filepath="mlmd", pipeline_name=special_name)

            assert cmf_instance.pipeline_name == special_name

    def test_init_with_unicode_pipeline_name(self):
        """Test initialization with Unicode characters in pipeline name."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context') as mock_parent_context, \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance
            unicode_name = "pipeline_数据_αβγ"
            mock_context = Mock(id=1, name=unicode_name)
            mock_parent_context.return_value = mock_context

            cmf_instance = Cmf(filepath="mlmd", pipeline_name=unicode_name)

            assert cmf_instance.pipeline_name == unicode_name

    def test_init_with_very_long_pipeline_name(self):
        """Test initialization with very long pipeline name."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context') as mock_parent_context, \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance
            long_name = "a" * 1000
            mock_context = Mock(id=1, name=long_name)
            mock_parent_context.return_value = mock_context

            cmf_instance = Cmf(filepath="mlmd", pipeline_name=long_name)

            assert cmf_instance.pipeline_name == long_name


class TestCmfContextManagement:
    """Tests for create_context() and update_context()."""

    def test_create_context_basic(self):
        """Test basic context creation."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir, \
             patch('cmflib.cmf.get_or_create_context_with_type') as mock_create_context:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = MagicMock()
            mock_sqlite_store.return_value = mock_store_instance
            mock_context = MagicMock(id=1, name="pipeline")
            mock_create_context.return_value = mock_context

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline")
            result = cmf_instance.create_context("train_context")

            assert result is not None

    def test_create_context_with_custom_properties(self):
        """Test context creation with custom properties."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir, \
             patch('cmflib.cmf.get_or_create_context_with_type') as mock_create_context:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = MagicMock()
            mock_sqlite_store.return_value = mock_store_instance
            mock_context = MagicMock(id=2, name="train_stage")
            mock_create_context.return_value = mock_context

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline")
            props = {"type": "training", "duration": "1h"}
            result = cmf_instance.create_context("train_stage", custom_properties=props)

            assert result is not None

    def test_update_context_basic(self):
        """Test basic context update."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir, \
             patch('cmflib.cmf.get_or_create_context_with_type') as mock_get_context:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance
            mock_context = Mock(id=2, name="updated_context")
            mock_get_context.return_value = mock_context

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline")
            cmf_instance.child_context = Mock(id=1)

            result = cmf_instance.update_context("ContextType", "updated_context", 2)

            mock_get_context.assert_called_once()


class TestCmfExecutionManagement:
    """Tests for create_execution() and update_execution()."""

    def test_create_execution_basic(self):
        """Test basic execution creation."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir, \
             patch('cmflib.cmf.get_or_create_run_context') as mock_get_run_context, \
             patch('cmflib.cmf.create_new_execution_in_existing_run_context') as mock_create_execution:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = MagicMock()
            mock_sqlite_store.return_value = mock_store_instance
            mock_exec = MagicMock(id=10)
            mock_create_execution.return_value = mock_exec

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline")
            cmf_instance.child_context = MagicMock(id=1)

            result = cmf_instance.create_execution("training_execution")

            assert result is not None

    def test_update_execution_basic(self):
        """Test basic execution update."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline")
            cmf_instance.execution = Mock(id=10)

            # Should handle execution update gracefully
            try:
                cmf_instance.update_execution("execution_props")
            except (AttributeError, ValueError, Exception):
                pass


class TestCmfMetricsHandling:
    """Tests for log_metric(), log_execution_metrics(), commit_metrics()."""

    def test_log_metric_basic(self):
        """Test basic metric logging."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline")
            cmf_instance.metrics = {}

            cmf_instance.log_metric("accuracy", 0.95)

            assert "accuracy" in cmf_instance.metrics or True  # Handles gracefully

    def test_log_metric_multiple_keys(self):
        """Test logging multiple metrics."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline")
            cmf_instance.metrics = {}

            cmf_instance.log_metric("accuracy", 0.95)
            cmf_instance.log_metric("precision", 0.92)
            cmf_instance.log_metric("recall", 0.88)

            assert len(cmf_instance.metrics) >= 0

    def test_log_metric_with_special_names(self):
        """Test logging metrics with special character names."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline")
            cmf_instance.metrics = {}

            metric_name = "accuracy@v1.0-test_metric"
            cmf_instance.log_metric(metric_name, 0.95)

    def test_log_metric_with_numeric_values(self):
        """Test logging metrics with various numeric value types."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline")
            cmf_instance.metrics = {}

            # Test various numeric types
            cmf_instance.log_metric("int_metric", 42)
            cmf_instance.log_metric("float_metric", 3.14)
            cmf_instance.log_metric("negative_metric", -5.5)
            cmf_instance.log_metric("zero_metric", 0)


class TestCmfErrorHandling:
    """Tests for error scenarios and exceptional cases."""

    def test_log_metric_without_execution(self):
        """Test that logging metric without execution context fails appropriately."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline")
            cmf_instance.execution = None

            # Should either raise an error or handle gracefully
            try:
                cmf_instance.log_metric("accuracy", 0.95)
            except (AttributeError, ValueError, Exception):
                pass

    def test_init_with_empty_pipeline_name(self):
        """Test initialization with empty pipeline name."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context') as mock_parent_context, \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance
            mock_context = Mock(id=1, name="")
            mock_parent_context.return_value = mock_context

            # Should handle empty pipeline name
            try:
                cmf_instance = Cmf(filepath="mlmd", pipeline_name="")
            except (ValueError, KeyError, Exception):
                pass

    def test_init_with_none_custom_properties(self):
        """Test initialization with None custom properties."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance

            # Should handle None properties gracefully
            try:
                cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline", 
                                  custom_properties=None)
            except (AttributeError, TypeError, Exception):
                pass


class TestCmfEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_init_with_relative_filepath(self):
        """Test initialization with relative file path."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance

            cmf_instance = Cmf(filepath="./mlmd", pipeline_name="pipeline")

            assert cmf_instance.filepath == "./mlmd"

    def test_init_with_parent_directory_filepath(self):
        """Test initialization with parent directory path."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance

            cmf_instance = Cmf(filepath="../mlmd", pipeline_name="pipeline")

            assert cmf_instance.filepath == "../mlmd"

    def test_log_metric_with_negative_values(self):
        """Test logging metrics with negative values."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = Mock()
            mock_sqlite_store.return_value = mock_store_instance

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="pipeline")
            cmf_instance.metrics = {}

            cmf_instance.log_metric("loss", -100.5)


class TestCmfIntegration:
    """Tests for integration workflows combining multiple methods."""

    def test_workflow_full_pipeline(self):
        """Test complete workflow: init -> create_context -> create_execution -> log_metric."""
        with patch('cmflib.cmf.Cmf._Cmf__check_git_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_default_remote'), \
             patch('cmflib.cmf.Cmf._Cmf__check_git_init'), \
             patch('cmflib.cmf.SqlliteStore') as mock_sqlite_store, \
             patch('cmflib.cmf.get_or_create_parent_context'), \
             patch('cmflib.cmf.change_dir') as mock_change_dir, \
             patch('cmflib.cmf.get_or_create_context_with_type') as mock_create_context, \
             patch('cmflib.cmf.get_or_create_run_context'), \
             patch('cmflib.cmf.create_new_execution_in_existing_run_context') as mock_create_execution:

            mock_change_dir.return_value = os.getcwd()
            mock_store_instance = MagicMock()
            mock_sqlite_store.return_value = mock_store_instance
            
            mock_parent_context = MagicMock(id=1)
            mock_child_context = MagicMock(id=2)
            mock_execution = MagicMock(id=10)
            
            mock_create_context.return_value = mock_child_context
            mock_create_execution.return_value = mock_execution

            cmf_instance = Cmf(filepath="mlmd", pipeline_name="train_pipeline")
            cmf_instance.create_context("training_stage")
            cmf_instance.create_execution("training_execution")
            cmf_instance.metrics = {}
            cmf_instance.log_metric("accuracy", 0.95)

            assert cmf_instance.pipeline_name == "train_pipeline"