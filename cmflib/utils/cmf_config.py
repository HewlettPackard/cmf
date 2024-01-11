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

import configparser
import os
import base64

class CmfConfig:
    @staticmethod
    def write_config(config_file:str, section_name:str, dict_of_attr, file_exists=False):
        config = configparser.ConfigParser()
        if file_exists:
            with open(config_file, "r") as file:
                config.read_file(file)
            if config.has_section(section_name):
                config.remove_section(section_name)
        config.add_section(section_name)
        for key, value in dict_of_attr.items():
            if section_name =='neo4j' and key == 'password':
                value = str(base64.b64encode(value.encode("UTF-8")), "UTF-8")
            config.set(section_name, key, value)
        with open(config_file, "w") as file:
            config.write(file)

    @staticmethod
    def read_config(config_file:str):
        output_dict = {}
        config_data = configparser.ConfigParser()
        with open(config_file, "r") as file:
            config_data.read_file(file)
        sections = config_data.sections()
        for sec in sections:
            sec_data = config_data[sec]
            for key in sec_data:
                value = sec_data.get(key)
                if sec == 'neo4j' and key == 'password':
                    encoded_pass = bytes(value,"utf-8")
                    value = base64.b64decode(encoded_pass).decode("utf-8")
                key = f"{sec}-{key}"
                output_dict[key] = value
        return output_dict
