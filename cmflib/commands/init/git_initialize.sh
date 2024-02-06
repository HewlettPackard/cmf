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

#!/bin/bash

git init -q
git checkout -q -b master
cur_dir=$(pwd)
head_dir="$cur_dir/.git/refs/heads"
if [ "$(ls -A $head_dir)" ]
then
  true
else
  git commit -q --allow-empty -n -m "Initial code commit"
fi
git remote add cmf_origin $1
