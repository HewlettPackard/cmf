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

/**
 * Runtime configuration for the application, we get the CMF Backend URL from environment variables.
 */

const runtimeConfig = window.RUNTIME_CONFIG || {};

let apiUrl = runtimeConfig.REACT_APP_CMF_API_URL || "http://localhost";
// Only append /api if it's not already there
if (apiUrl && !apiUrl.endsWith('/api')) {
  apiUrl = `${apiUrl}/api`;
}

const config = {
  apiBasePath: apiUrl,
  reactAppMode: "production",
};
console.log("Config:", config);

export default config;
