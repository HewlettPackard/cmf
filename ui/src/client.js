/***
 * Copyright (2023) Hewlett Packard Enterprise Development LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * You may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ***/

import config from "./config";

const axios = require("axios");

class FastAPIClient {
  constructor(overrides) {
    this.config = {
      ...config,
      ...overrides,
    };
    this.apiClient = this.getApiClient(this.config);
  }

  /* ----- Client Configuration ----- */

  /* Create Axios client instance pointing at the REST api backend */
  getApiClient(config) {
    const initialConfig = {
      baseURL: `${config.apiBasePath}/`,
    };
    const client = axios.create(initialConfig);

    // Simple error interceptor
    client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        // Show simple error message to user
        if (error.response?.status >= 500) {
          alert('Server error. Please try again later.');
        } else if (error.request && !error.response) {
          alert('Unable to connect to server. Please check your connection.');
        }
        return Promise.reject(error);
      }
    );

    return client;
  }

  // Deprecated legacy methods (unused by current stage-based grid pages).
  // Replaced by: getArtifactsByStage / getArtifactTypesByStage
  // async getArtifacts(pipeline_name, artifact_type, sort_order, active_page, filter_value, sort_field) {
  //   return this.apiClient
  //     .get(`/artifacts/${pipeline_name}/${artifact_type}`, {
  //       params: {
  //         filter_value: filter_value,
  //         sort_order: sort_order,
  //         active_page: active_page,
  //         sort_field: sort_field,
  //       },
  //     })
  //     .then(({ data }) => {
  //       return data;
  //     });
  // }

  // async getArtifactTypes() {
  //   return this.apiClient.get(`/artifact_types`).then(({ data }) => {
  //     return data;
  //   });
  // }

  async getArtifactLineage(pipeline) {
    return this.apiClient
      .get(`/artifact-lineage/force-directed-graph/${pipeline}`)
      .then(({ data }) => {
        return data;
      });
  }

  async getArtiTreeLineage(pipeline) {
    return this.apiClient
      .get(`/artifact-lineage/tangled-tree/${pipeline}`)
      .then(({ data }) => {
        return data;
      });
  }

  async getExecutionTypes(pipeline) {
    return this.apiClient
      .get(`/list-of-executions/${pipeline}`)
      .then(({ data }) => {
        return data;
      });
  }

  async getExecutionLineage(pipeline, uuid) {
    return this.apiClient
      .get(`/execution-lineage/force-directed-graph/${pipeline}/${uuid}`)
      .then(({ data }) => {
        return data;
      });
  }

  async getExecTreeLineage(pipeline, uuid) {
    return this.apiClient
      .get(`/execution-lineage/tangled-tree/${uuid}/${pipeline}`)
      .then(({ data }) => {
        return data;
      });
  }

  async getArtiExeTreeLineage(pipeline) {
    return this.apiClient
      .get(`/artifact-execution-lineage/tangled-tree/${pipeline}`)
      .then(({ data }) => {
        return data;
      });
  }

  // Deprecated legacy method (unused by current stage-based grid pages).
  // Replaced by: getExecutionsByStage
  // async getExecutions(pipeline_name, active_page, filter_value, sort_order) {
  //   return this.apiClient
  //     .get(`/executions/${pipeline_name}`, {
  //       params: {
  //         active_page: active_page,
  //         filter_value: filter_value,
  //         sort_order: sort_order,
  //       },
  //     }).
  //     then(({ data }) => {
  //       return data;
  //     });
  // }

  async getPipelines(value) {
    try {
      const { data } = await this.apiClient.get(`/pipelines`);
      return data;
    } catch (error) {
      // Error already handled by interceptor, just return empty array
      return [];
    }
  }

  async getModelCard(modelId) {
    return this.apiClient
      .get(`/model-card`, {
        params: {
          modelId: modelId,
        },
      })
      .then(({ data }) => {
        return data;
      });
  }

  async getPythonEnv(file_name) {
    return this.apiClient
      .get(`/python-env`, {
        params: {
          file_name: file_name
        },
        responseType: "text", // Explicitly specify response type as text
      })
      .then((response) => {
        return response.data;
      });
  }

  async getLabelData(file_name) {
    return this.apiClient
      .get(`/label-data`, {
        params: {
          file_name: file_name
        },
        responseType: "text",
      })
      .then((response) => {
        return response.data;
      });
  }

  async getServerRegistration(server_name, server_url) {
    return this.apiClient
      .post(`/register-server`, {
        server_name: server_name,
        server_url: server_url,
      })
      .then(({ data }) => {
        return data;
      });
  }

  async getRegistredServerList() {
    return this.apiClient
      .get(`/server-list`)
      .then(({ data }) => {
        return data;
      });
  }

  async sync(serverName, serverUrl) {
    return this.apiClient
      .post(`/sync`, {
        server_name: serverName,
        server_url: serverUrl,
      })
      .then(({ data }) => {
        return data;
      });
  }

  async getExecutionsByStage(pipelineName, stageName, activePage = 1, recordPerPage = 5, sortOrder = "desc", filterValue = "") {
    return this.apiClient
      .get(`/executions-by-stage/${pipelineName}`, {
        params: {
          stage_name: stageName,
          active_page: activePage,
          record_per_page: recordPerPage,
          sort_order: sortOrder,
          filter_value: filterValue,
        },
      })
      .then(({ data }) => {
        return data;
      });
  }

  async getPipelineStages(pipelineName) {
    return this.apiClient
      .get(`/pipeline-stages/${pipelineName}`)
      .then(({ data }) => {
        return data;
      });
  }

  async getArtifactTypesByStage(pipelineName, stageName) {
    return this.apiClient
      .get(`/artifact-types-by-stage/${pipelineName}`, {
        params: {
          stage_name: stageName,
        },
      })
      .then(({ data }) => {
        return data;
      });
  }

  async getArtifactsByStage(pipelineName, stageName, artifactType, sortOrder, activePage = 1, recordPerPage = 5, filter = "", sortField = "name") {
    return this.apiClient
      .get(`/artifacts-by-stage/${pipelineName}`, {
        params: {
          stage_name: stageName,
          artifact_type: artifactType,
          sort_order: sortOrder,
          active_page: activePage,
          record_per_page: recordPerPage,
          filter_value: filter,
          sort_field: sortField,
        },
      })
      .then(({ data }) => {
        return data;
      });
  }

}



export default FastAPIClient;

