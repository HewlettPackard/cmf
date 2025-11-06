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

export hostname=$REACT_APP_CMF_API_URL

original_docker_file="../../server/Dockerfile"
new_docker_file="../../server/Dockerfile_new"
cp "$original_docker_file" "$new_docker_file"
sed -i 's/--port, "80"/--port, "8080"/g' "$new_docker_file"

original_compose_file="../../docker-compose-server.yml"
new_compose_file="../../docker-compose-server-new.yml"
cp "$original_compose_file" "$new_compose_file"
sed -i 's/8080:80/8080:8080/g' "$new_compose_file"
sed -i 's/dockerfile: ./server\/Dockerfile/dockerfile: ../server\/Dockerfile-new/g' "$new_compose_file"

docker-compose --verbose -f $new_compose_file build
rm $new_docker_file
rm $new_compose_file


#setup minio server
export bucket_name="dvc-art"
export access_key_id="minioadmin"
export secret_key="minioadmin"

docker-compose --verbose -f docker-compose-minio.yml build

#setup neo4j server
#
export neo4j_user="neo4j"
export neo4j_password="test1234"

docker-compose --verbose -f docker-compose-neo4j.yml build
