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
    /* client.interceptors.request.use(localStorageTokenInterceptor);*/
    return client;
  }

  async getArtifacts(
    pipelineName,
    type,
    page,
    sortField,
    sortOrder,
    filterBy,
    filterValue,
  ) {
    return this.apiClient
      .get(`/artifacts/${pipelineName}/${type}`, {
        params: {
          page: page,
          sort_field: sortField,
          sort_order: sortOrder,
          filter_by: filterBy,
          filter_value: filterValue,
        },
      })
      .then(({ data }) => {
        return data;
      });
  }

  async getArtifactTypes() {
    return this.apiClient.get(`/artifact_types`).then(({ data }) => {
      return data;
    });
  }

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
    return this.apiClient.get(`/artifact-execution-lineage/tangled-tree/${pipeline}`)
    .then(({ data }) => {
      return data;
    }); 
  }

  async getExecutions(pipelineName, page, sortField, sortOrder , filterBy, filterValue) {
    return this.apiClient
      .get(`/executions/${pipelineName}`, {
        params: {
          page: page,
          sort_field: sortField,
          sort_order: sortOrder,
          filter_by: filterBy,
          filter_value: filterValue,
        },
      })
      .then(({ data }) => {
        return data;
      });
  }

  async getPipelines(value) {
    try {
      const { data } = await this.apiClient.get(`/pipelines`);
      return data;
    } catch (error) {
      console.error(error);
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
      .then(( response ) => {
        return response.data;
      });
  }

}



export default FastAPIClient;
