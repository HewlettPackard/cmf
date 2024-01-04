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

import os
import sys
import json
import shutil
import subprocess

if __name__ == "__main__":
    try:
       client_test_suite = 'client_test_suite.py'
       server_test_suite = 'server_api_endpoints_test_suite.py'

       subprocess.run(['python', client_test_suite])
       subprocess.run(['python', server_test_suite])


    except Exception as e:
        print(f"An error occurred: {e}")



