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

import runtimeEnv from "@mars/heroku-js-runtime-env";

let url="";
const env = runtimeEnv();
if (process.env.REACT_APP_MY_IP !== "127.0.0.1") {
    url="http://"+process.env.REACT_APP_MY_IP+":8080";
}
else {
    url="http://"+process.env.REACT_APP_MY_HOSTNAME+":8080";
}
const config = {
  apiBasePath: env.REACT_APP_API_BASE_PATH || url,
  reactAppMode: process.env.REACT_APP_MODE || "dev",
};

export default config;
