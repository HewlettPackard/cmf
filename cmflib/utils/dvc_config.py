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
import subprocess

# This class handles pulls dvc configuration
class dvc_config:
    @staticmethod
    def get_dvc_config():
        result = subprocess.run(["dvc", "config", "-l"], capture_output=True, text=True)
        if len(result.stdout) == 0:
            return "'cmf' is not configured.\nExecute 'cmf init' command."
        else:
            config_list = result.stdout.split("\n")
            config_list.pop(-1)
            config_dict = {}
            for item in config_list:
                item_list = item.split("=")
                config_dict[item_list[0]] = item_list[1]
            remote = config_dict["core.remote"]
            if config_dict["core.remote"] == "minio":
                return (
                    config_dict["core.remote"],
                    config_dict["remote.minio.endpointurl"],
                    config_dict["remote.minio.access_key_id"],
                    config_dict["remote.minio.secret_access_key"],
                    config_dict["remote.minio.url"],
                )
            elif config_dict["core.remote"] == "local-storage":
                return (
                    config_dict["core.remote"],
                    config_dict["remote.local-storage.url"],
                )
            elif config_dict["core.remote"] == "ssh-storage":
                return (
                    config_dict["core.remote"],
                    config_dict["remote.ssh-storage.url"],
                    config_dict["remote.ssh-storage.user"],
                    config_dict["remote.ssh-storage.port"],
                    config_dict["remote.ssh-storage.password"],
                )
            elif config_dict["core.remote"] == "amazons3":
                return (
                    config_dict["core.remote"],
                    config_dict["remote.amazons3.url"],
                    config_dict["remote.amazons3.access_key_id"],
                    config_dict["remote.amazons3.secret_access_key"],
                )
            else:
                return f"{remote} doesn't exist."


def main():
    print(dvc_config.get_dvc_config())


if __name__ == "__main__":
    main()
