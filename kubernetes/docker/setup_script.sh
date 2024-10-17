#!/bin/bash
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

#setup cmf server

export IP="192.168.30.116"
export hostname=""

docker-compose --verbose -f ../../docker-compose-server.yml up -d

#setup minio server
export bucket_name="dvc-art"
export access_key_id="minioadmin"
export secret_key="minioadmin"

docker-compose --verbose -f docker-compose-minio.yml up -d

#setup neo4j serverA
#
export neo4j_user="neo4j"
export neo4j_password="test1234"

docker-compose --verbose -f docker-compose-neo4j.yml up -d
