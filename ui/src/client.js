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

    // Response interceptor to handle standardized API response format
    client.interceptors.response.use(
      (response) => {
        // Check if response has standardized format
        if (response.data && typeof response.data === 'object' && 'status' in response.data && 'code' in response.data && 'data' in response.data) {
          const apiResponse = response.data;
          
          // If status is error or code indicates error, throw error
          if (apiResponse.status === 'error' || apiResponse.code >= 400) {
            const error = new Error(apiResponse.message);
            error.code = apiResponse.code;
            error.errors = apiResponse.errors;
            error.requestId = apiResponse.meta?.request_id;
            throw error;
          }
          
          // Return unwrapped data for successful responses
          return {
            ...response,
            data: apiResponse.data, // Extract the actual data from standardized format
            meta: apiResponse.meta, // Keep meta for pagination info if needed
            message: apiResponse.message,
          };
        }
        
        // Return response as-is if not in standardized format (legacy endpoints)
        return response;
      },
      (error) => {
        console.error('API Error:', error);
        
        // Handle standardized error response
        if (error.response?.data?.status === 'error' || error.response?.data?.code >= 400) {
          const apiError = error.response.data;
          console.error('Standardized error:', apiError);
          error.message = apiError.message;
          error.code = apiError.code;
          error.errors = apiError.errors;
          error.requestId = apiError.meta?.request_id;
        }
        
        // Show error message to user
        if (error.response?.status >= 500) {
          alert('Server error. Please try again later.');
        } else if (error.request && !error.response) {
          alert('Server connection refused. The backend service may be down. Please restart your Docker container and try again.');
        } else if (error.response?.status === 422) {
          alert(`Validation error: ${error.message}`);
        }
        return Promise.reject(error);
      }
    );

    return client;
  }

  async getArtifactLineage(pipeline) {
  return this.apiClient
    .get(`/v1/pipelines/${encodeURIComponent(pipeline)}/artifacts/lineage`)
    .then(({ data }) => {
      return data;
    });
}

  async getExecutionTypes(pipeline) {
    return this.apiClient
      .get(`/v1/pipelines/${encodeURIComponent(pipeline)}/executions/list`)
      .then(({ data }) => {
        return data;
      });
  }

  async getExecutionLineage(pipeline, uuid) {
    return this.apiClient
      .get(`/v1/pipelines/${encodeURIComponent(pipeline)}/executions/${uuid}/lineage`)
      .then(({ data }) => {
        return data;
      });
  }

  async getArtiExeTreeLineage(pipeline) {
    return this.apiClient
      .get(`/v1/pipelines/${encodeURIComponent(pipeline)}/artifact-executions/lineage`)
      .then(({ data }) => {
        return data;
      });
  }

  async getHierarchicalLineage(pipeline) {
    return this.apiClient
      .get(`/v1/pipelines/${encodeURIComponent(pipeline)}/hierarchical-lineage`)
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
      const { data } = await this.apiClient.get(`/v1/pipelines`);
      return data;
    } catch (error) {
      // Error already handled by interceptor, just return empty array
      return [];
    }
  }

 async getModelCard(modelId) {
    return this.apiClient
      .get(`/v1/model-card`, {
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
      .get(`/v1/python-env/${encodeURIComponent(file_name)}`, {
        responseType: "text",
      })
      .then((response) => {
        return response.data;
      });
  }

  async getLabelData(file_name) {
    return this.apiClient
      .get(`/v1/label-data`, {
        params: {
          file_name: file_name
        },
        responseType: "text", // Explicitly specify response type as text
      })
      .then((response) => {
        return response.data;
      });
  }
  async getServerRegistration(server_name, server_url) {
    return this.apiClient
      .post(`/v1/servers/register`, {
        server_name: server_name,
        server_url: server_url,
      })
      .then(({ data }) => {
        return data;
      });
  }

  async getRegistredServerList() {
    return this.apiClient
      .get(`/v1/servers`)
      .then(({ data }) => {
        return data;
      });
  }

  async sync(serverName, serverUrl) {
    return this.apiClient
      .post(`/v1/servers/sync`, {
        server_name: serverName,
        server_url: serverUrl,
      })
      .then(({ data }) => {
        return data;
      });
  }

  async scheduleSync(serverId, timezone, startTimeLocalIso, oneTime = false, recurrenceMode = 'interval', intervalUnit = 'hours', intervalValue = 6, dailyTime = null, weeklyDay = null, weeklyTime = null) {
    const payload = {
      server_id: serverId,
      timezone: timezone,
      start_time_local_iso: startTimeLocalIso,
      one_time: oneTime,
    };

    // Only add recurrence mode for periodic syncs
    if (!oneTime) {
      payload.recurrence_mode = recurrenceMode;

      // Add mode-specific fields
      if (recurrenceMode === 'interval') {
        payload.interval_unit = intervalUnit;
        payload.interval_value = intervalValue;
      } else if (recurrenceMode === 'daily') {
        payload.daily_time = dailyTime;
      } else if (recurrenceMode === 'weekly') {
        payload.weekly_day = weeklyDay;
        payload.weekly_time = weeklyTime;
      }
    }

    return this.apiClient
      .post(`/v1/schedules`, payload)
      .then(({ data }) => data);
  }

  async getSchedules(serverId) {
    return this.apiClient
      .get(`/v1/schedules`, {
        params: { server_id: serverId },
      })
      .then(({ data }) => data);
  }

  async getScheduleLogs(scheduleId) {
    return this.apiClient
      .get(`/v1/schedules/${scheduleId}/logs`)
      .then(({ data }) => data);
  }

  async getCompletedLogs(serverId) {
    return this.apiClient
      .get(`/v1/servers/${serverId}/completed-logs`)
      .then(({ data }) => data);
  }

  async deleteSchedule(scheduleId) {
    return this.apiClient
      .delete(`/v1/schedules/${scheduleId}`)
      .then(({ data }) => data);
  }
  
  async getExecutionsByStage(pipelineName, stageName, activePage = 1, recordPerPage = 5, sortOrder = "desc", filterValue = "") {
    return this.apiClient
      .post(`/v1/pipelines/${encodeURIComponent(pipelineName)}/stages/${encodeURIComponent(stageName)}/executions`, {
        active_page: activePage,
        record_per_page: recordPerPage,
        sort_order: sortOrder,
        filter_value: filterValue,
      })
      .then(({ data }) => {
        return data;
      });
  }

  async getPipelineStages(pipelineName) {
    return this.apiClient
      .get(`/v1/pipelines/${encodeURIComponent(pipelineName)}/stages`)
      .then(({ data }) => {
        return data;
      });
  }

  async getArtifactTypesByStage(pipelineName, stageName) {
    return this.apiClient
      .post(`/v1/pipelines/${encodeURIComponent(pipelineName)}/stages/${encodeURIComponent(stageName)}/artifacts/types`, {
      })
      .then(({ data }) => {
        return data;
      }); 
  }

  async getArtifactsByStage(pipelineName, stageName, artifactType, sortOrder, activePage = 1, recordPerPage = 5, filter = "", sortField = "name") {
    return this.apiClient
      .post(`/v1/pipelines/${encodeURIComponent(pipelineName)}/stages/${encodeURIComponent(stageName)}/artifacts`, {
        artifact_type: artifactType,
        sort_order: sortOrder,
        active_page: activePage,
        record_per_page: recordPerPage,
        filter_value: filter,
        sort_field: sortField,
      })
      .then(({ data }) => {
        return data;
      });
  }

}



export default FastAPIClient;

