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
Provides domain-specific methods for pipelines, executions, artifacts, etc.

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

    def get_pipelines(self):
        """
        Retrieve currently registered pipelines.

        :return: API response containing registered pipelines.
        """
        return self.connection.get("/pipelines")

    def get_executions_list(self, pipeline_name):
        """
        Retrieve a brief list of execution names for a pipeline.

        :param pipeline_name: Name of the pipeline.
        :return: API response containing execution names.
        """
        return self.connection.get(f"/list-of-executions/{pipeline_name}")

    def get_executions(self, pipeline_name):
        """
        Retrieve detailed executions for a pipeline.

        :param pipeline_name: Name of the pipeline.
        :return: API response containing executions.
        """
        return self.connection.get(f"/executions/{pipeline_name}")

    def get_artifact_types(self):
        """
        Retrieve a list of artifact types.

        :return: API response containing artifact types.
        """
        return self.connection.get("/artifact_types")

    def get_artifacts(self, pipeline_name, artifact_type):
        """
        Retrieve artifacts of a specific type for a given pipeline.

        :param pipeline_name: Name of the pipeline.
        :param artifact_type: Type of the artifact.
        :return: API response containing artifacts of the specified type.
        """
        return self.connection.get(f"/artifacts/{pipeline_name}/{artifact_type}")

    def get_artifact_lineage_tangled_tree(self, pipeline_name):
        """
        Retrieve the artifact lineage for a given pipeline.

        :param pipeline_name: Name of the pipeline.
        :return: API response containing the artifact lineage tangled tree.
        """
        return self.connection.get(f"/artifact-lineage/tangled-tree/{pipeline_name}")

    def get_execution_lineage_tangled_tree(self, uuid, pipeline_name):
        """
        Retrieve the execution lineage tangled tree for a given UUID and pipeline.

        :param uuid: Unique identifier for the execution.
        :param pipeline_name: Name of the pipeline.
        :return: API response containing the execution lineage tangled tree.
        """
        return self.connection.get(f"/execution-lineage/tangled-tree/{uuid}/{pipeline_name}")

    def get_model_card(self, model_id):
        """
        Retrieve the model card information.

        :param model_id: Unique identifier for the model (as int).
        :return: API response containing the model card details.
        """
        model_id_int = int(model_id)
        return self.connection.get("/model-card", params={"modelId": model_id_int})

    def get_python_env(self):
        """
        Retrieve the Python environment details.

        :return: API response containing the Python environment details.
        """
        return self.connection.get("/python-env")

    def mlmd_push(self, payload):
        """
        Push metadata to the MLMD server.

        :param payload: The data to be pushed (as a dictionary).
        :return: API response after pushing the metadata.
        """
        return self.connection.post("/mlmd_push", data=payload)

    def mlmd_pull(self, pipeline_name):
        """
        Retrieve metadata for a specific pipeline.

        :param pipeline_name: Name of the pipeline.
        :return: API response containing the metadata.
        """
        return self.connection.get(f"/mlmd_pull/{pipeline_name}")

    def close_session(self):
        """
        Close the session with the CMF server.
        """
        self.connection.exit()
