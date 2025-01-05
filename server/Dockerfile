###
# Copyright (2023) Hewlett Packard Enterprise Development LP
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

# Use python 3.10-slim-buster as base image.
FROM python:3.10-slim-buster

#Update the proxy if needed
#ENV http_proxy http://web-proxy.corp.hpecorp.net:8080
# Create a cmf-server directory.
WORKDIR /cmf-server

# Execute the mkdir command to create a data folder inside the cmf-server directory.
RUN mkdir -p /cmf-server/data

# folder for static files
RUN mkdir -p /cmf-server/data/static

# folder for tensorboard logs
RUN mkdir -p /cmf-server/data/tensorboard-logs

# library required for curl command
RUN apt-get update -y && apt-get install -y gcc

RUN apt-get update -y && apt-get install -y curl

# Copy the requirements.txt file from the server to the cmf-server.
COPY ./server/requirements.txt /cmf-server/requirements.txt

# library required for lineage
RUN apt-get install -y graphviz graphviz-dev 

# Install requirements.txt
RUN pip install --no-cache-dir --upgrade -r /cmf-server/requirements.txt

# Copy the setup.py file to cmf-server
COPY ./setup.py  /cmf-server/setup.py

# Copy the cmflib file to cmf-server
COPY ./cmflib /cmf-server/cmflib

# Install cmflib
RUN python /cmf-server/setup.py bdist_wheel

# Installing cmf on server
RUN pip install /cmf-server/dist/*
 
# Copy the app file from server to cmf-server/server
COPY ./server/app /cmf-server/server/app

# Run the server with uvicorn
CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "80"]

RUN cd /cmf-server/data/static

ENV NEO4J_URI=""
ENV NEO4J_USER_NAME=""
ENV NEO4J_PASSWD=""

