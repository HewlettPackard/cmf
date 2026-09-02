###
# Copyright (2026) Hewlett Packard Enterprise Development LP
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

FROM docker.io/library/nginx:alpine

# Build context is the repository root, so nginx.conf is at the top level.
COPY nginx.conf /etc/nginx/nginx.conf

# Note: skip `nginx -t` here since upstream hostnames (e.g. "server") only
# resolve on the docker-compose network at container runtime, not at build time.
RUN apk add --no-cache curl

EXPOSE 80 443

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -f http://127.0.0.1:80/check.html || exit 1

CMD ["nginx", "-g", "daemon off;"]
