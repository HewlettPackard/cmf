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

  async getImage(pipeline) {
   try {
      const response  = await this.apiClient.get(`/display_lineage/${pipeline}`, { responseType: "blob" });
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
