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

let url = "";
let url_without_port = "";
const env = runtimeEnv();
if (process.env.REACT_APP_MY_IP !== "127.0.0.1" && process.env.REACT_APP_MY_IP !=="") {
    url = "http://" + process.env.REACT_APP_MY_IP + ":8080";
    url_without_port = "http://" + process.env.REACT_APP_MY_IP
}
else {
    url= " http://" + process.env.REACT_APP_MY_HOSTNAME + ":8080";
    url_without_port = "http://" + process.env.REACT_APP_MY_HOSTNAME
}
const config = {
  apiBasePath: env.REACT_APP_API_BASE_PATH || url,
  reactAppMode: process.env.REACT_APP_MODE || "dev",
  apiBasePathWOPort: url_without_port
};

export default config;
