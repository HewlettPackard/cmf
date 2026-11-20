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
CMF API Client module.

High-level client wrapper for communicating with CMF Server REST API.
Provides domain-specific methods for pipelines, executions, artifacts, metadata,
servers, schedules, and Python environment management.

Originally from the cmfAPI package (https://github.com/atripathy86/cmfapi).
Inlined here to remove the external dependency.
"""

from .conn import cmfConnection


class cmfClient:
    def __init__(self, base_url, tls_verify=None):
        """
        Initialize the CMF API client wrapper.

        :param base_url: CMF Server base URL
        :param tls_verify: TLS certificate verification (True/False/path to CA bundle, default from env)
        """
        self.connection = cmfConnection(base_url, tls_verify=tls_verify)

    # Pipelines
    def get_pipelines(self):
         """
        Retrieve currently registered pipelines.

        :return: API response containing registered pipelines."""
         return self.connection.get("/v1/pipelines")

    # Executions
    def get_executions_list(self, pipeline_name):
        """
        Retrieve a brief list of execution names for a pipeline.

        :param pipeline_name: Name of the pipeline.
        :return: API response containing execution names.
        """
        return self.connection.get(f"/v1/pipelines/{pipeline_name}/executions/list")

    def get_executions(self, pipeline_name):
        """
        Retrieve detailed executions for a pipeline.

        :param pipeline_name: Name of the pipeline.
        :return: API response containing executions.
        """
        # Use the standardized endpoint for getting all executions in the pipeline.
        return self.connection.get(f"/v1/pipelines/{pipeline_name}/executions")


    def get_execution_lineage_tangled_tree(self, uuid, pipeline_name):
        """
        Retrieve the execution lineage tangled tree for a given UUID and pipeline.

        :param uuid: Unique identifier for the execution.
        :param pipeline_name: Name of the pipeline.
        :return: API response containing the execution lineage tangled tree.
        """
        return self.connection.get(f"/v1/pipelines/{pipeline_name}/executions/{uuid}/lineage")

    # Artifacts
    def get_artifact_types(self):
        """
        Retrieve a list of artifact types.

        :return: API response containing artifact types.
        """
        return self.connection.get("/v1/artifacts/types")


    def get_artifacts(self, pipeline_name):
        """
        Retrieve all artifacts for a given pipeline.
        :return: API response containing all artifacts for the pipeline.
        """
        # Use the standardized endpoint for getting all artifacts in the pipeline.
        return self.connection.get(f"/v1/pipelines/{pipeline_name}/artifacts")

    def get_artifact_lineage_tangled_tree(self, pipeline_name):
        """
        Retrieve the artifact lineage for a given pipeline.

        :param pipeline_name: Name of the pipeline.
        :return: API response containing the artifact lineage tangled tree.
        """
        return self.connection.get(f"/v1/pipelines/{pipeline_name}/artifacts/lineage")

    def get_model_card(self, model_id):
        """
        Retrieve the model card information.

        :param model_id: Unique identifier for the model (as int).
        :return: API response containing the model card details.
        """
        model_id_int = int(model_id)
        return self.connection.get(f"/v1/artifacts/models/{model_id_int}/card")

    def get_python_env(self, pipeline_name, execution_uuid):
        """
        Retrieve the Python environment details.

        :return: API response containing the Python environment details.
        """
        return self.connection.get(f"/v1/pipelines/{pipeline_name}/executions/{execution_uuid}/python-env")


    # MLMD metadata sync
    def mlmd_push(self, pipeline_name, json_payload, exec_uuid=None):
        """
        Push metadata to the MLMD server.

        :param payload: The data to be pushed (as a dictionary).
        :return: API response after pushing the metadata.
        """
        payload = {
            "pipeline_name": pipeline_name,
            "json_payload": json_payload,
            "exec_uuid": exec_uuid,
        }
        return self.connection.post("/v1/mlmd/push", data=payload)

    def mlmd_pull(self, pipeline_name=None, exec_uuid=None, last_sync_time=None):
        """
        Retrieve metadata for a specific pipeline.

        :param pipeline_name: Name of the pipeline.
        :return: API response containing the metadata.
        """
        payload = {
            "pipeline_name": pipeline_name,
            "exec_uuid": exec_uuid,
            "last_sync_time": last_sync_time,
        }
        return self.connection.post("/v1/mlmd/pull", data=payload)

    def close_session(self):
        """Close the session with the CMF server."""
        self.connection.exit()
