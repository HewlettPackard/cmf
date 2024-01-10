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

  async getArtifacts(pipelineName, type, page, sortField, sortOrder, filterBy, filterValue) {
    return this.apiClient
      .get(`/display_artifacts/${pipelineName}/${type}`, {
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
    return this.apiClient
      .get(`/display_artifact_types`)
      .then(({ data }) => {
        return data;
      });
  }

  async getLineage(pipeline,lineage_type) {
   try {
      const response  = await this.apiClient.get(`/display_lineage/${lineage_type}/${pipeline}`, { responseType: "blob" });
      const objectURL = URL.createObjectURL(response.data);
      return objectURL;
    } catch (error) {
      console.error(error);
    }
  }


  async getExecutions(pipelineName, page, sortField, sortOrder , filterBy, filterValue) {
    return this.apiClient
      .get(`/display_executions/${pipelineName}`, {
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
      const { data } = await this.apiClient.get(`/display_pipelines`);
      return data;
    } catch (error) {
      console.error(error);
    }
  }
}

export default FastAPIClient;
