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
        try:
            process = subprocess.Popen(
                ["dvc", "config", "-l"], stdout=subprocess.PIPE, universal_newlines=True
            )
            output, error = process.communicate(timeout=60)
            result = output.strip()
            print(result)
            if len(result) == 0:
                return "'cmf' is not configured.\nExecute 'cmf init' command."
            else:
                config_list = result.stdout.split("\n")
                config_list.pop(-1)
                config_dict = {}
                for item in config_list:
                    item_list = item.split("=")
                    config_dict[item_list[0]] = item_list[1]
                remote = config_dict["core.remote"]
                if remote == "minio":
                    return (
                        config_dict["core.remote"],
                        config_dict["remote.minio.endpointurl"],
                        config_dict["remote.minio.access_key_id"],
                        config_dict["remote.minio.secret_access_key"],
                        config_dict["remote.minio.url"],
                    )
                elif remote == "local-storage":
                    return (
                        config_dict["core.remote"],
                        config_dict["remote.local-storage.url"],
                    )
                elif remote == "ssh-storage":
                    return (
                        config_dict["core.remote"],
                        config_dict["remote.ssh-storage.url"],
                        config_dict["remote.ssh-storage.user"],
                        config_dict["remote.ssh-storage.port"],
                        config_dict["remote.ssh-storage.password"],
                    )
                elif remote == "amazons3":
                    return (
                        config_dict["core.remote"],
                        config_dict["remote.amazons3.url"],
                        config_dict["remote.amazons3.access_key_id"],
                        config_dict["remote.amazons3.secret_access_key"],
                    )
                else:
                    return f"{remote} doesn't exist."
        except Exception as err:
            process.kill()
            outs, errs = process.communicate()
            return f"Exception occurred: {errs}"


def main():
    print(dvc_config.get_dvc_config())


if __name__ == "__main__":
    main()
