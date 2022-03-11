###
# Copyright (2022) Hewlett Packard Enterprise Development LP
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

import io
import os
import random
import re
import sys
import xml.etree.ElementTree
from cmflib import cmf
import yaml
import random

'''
Input - Data.xml
Output - test.tsv
Output - train.tsv
Output - slice-a
'''
params = yaml.safe_load(open("params.yaml"))["prepare"]

if len(sys.argv) != 2:
    sys.stderr.write("Arguments error. Usage:\n")
    sys.stderr.write("\tpython prepare.py data-file\n")
    sys.exit(1)

# Test data set split ratio
split = params["split"]
random.seed(params["seed"])

input = sys.argv[1]
output_train = os.path.join("data", "prepared", "train.tsv")
output_test = os.path.join("data", "prepared", "test.tsv")

'''
Create the metadata writer
The metadata writer is responsible to manage the backend to record the metadata.
It also creates a pipeline abstraction, which helps to group individual stages and execution.
'''
metawriter = cmf.Cmf(filename="mlmd",
                                  pipeline_name="Test-env")

'''
Create the stage in pipeline.
An ML pipeline can have multiple stages.
This context abstraction tracks the stage and its metadata.
A dictionary can be passed to hold the user given metadata. The custom properties is an optional argument
'''
context = metawriter.create_context(pipeline_stage="Prepare",
                            custom_properties={"user-metadata1":"metadata_value"})

'''
Create the execution
A stage in ML pipeline can have multiple executions.
Every run is marked as an execution.
This API helps to track the metadata associated with the execution
'''
execution = metawriter.create_execution(execution_type="Prepare",
        custom_properties = {"split":split, "seed":params["seed"]})

'''
Log the artifacts
An Execution could have multiple artifacts associated with it as Input or Output.
The metadata associated with the artifact could be logged as an optional argument which takes in a dictionary
'''
metawriter.log_dataset(input, "input", custom_properties={"user-metadata1":"metadata_value"})

def process_posts(fd_in, fd_out_train, fd_out_test, target_tag):

    num = 1
    for line in fd_in:
        try:
            fd_out = fd_out_train if random.random() > split else fd_out_test
            attr = xml.etree.ElementTree.fromstring(line).attrib

            pid = attr.get("Id", "")
            label = 1 if target_tag in attr.get("Tags", "") else 0
            title = re.sub(r"\s+", " ", attr.get("Title", "")).strip()
            body = re.sub(r"\s+", " ", attr.get("Body", "")).strip()
            text = title + " " + body

            fd_out.write("{}\t{}\t{}\n".format(pid, label, text))

            num += 1
        except Exception as ex:
            sys.stderr.write(f"Skipping the broken line {num}: {ex}\n")


os.makedirs(os.path.join("data", "prepared"), exist_ok=True)

with io.open(input, encoding="utf8") as fd_in:
    with io.open(output_train, "w", encoding="utf8") as fd_out_train:
        with io.open(output_test, "w", encoding="utf8") as fd_out_test:
            process_posts(fd_in, fd_out_train, fd_out_test, "<python>")


metawriter.log_dataset(output_train, "output")
metawriter.log_dataset(output_test, "output")
