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

from cmflib.dvc_wrapper import dvc_get_config

# This class handles pulls dvc configuration
class DvcConfig:
    @staticmethod
    def get_dvc_config():
        message = "'cmf' is not configured.\nExecute 'cmf init' command."
        result = dvc_get_config()
        if not result:
            return message
        else:
            # splitting config on new line
            config_list = result.split("\n")
            config_dict = {}
            for item in config_list:
                # seprating every dvc property and its value using split on '='
                item_list = item.split("=") 
                config_dict[item_list[0]] = item_list[1]
            return config_dict


def main():
    print(DvcConfig.get_dvc_config())


if __name__ == "__main__":
    main()
