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
