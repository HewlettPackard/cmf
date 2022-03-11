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

from cmflib import cmf
import random
import pandas as pd

###
"""
Note  - All metadata is stored in a file called "mlmd". It is  a sqlite file
To delete earlier metadata, delete the mlmd file.
"""
metawriter =  cmf.Cmf(filename="mlmd",
                                  pipeline_name="dvc")
context = metawriter.create_context(pipeline_stage="Prepare")
execution = metawriter.create_execution(execution_type="Prepare")

### This is needed as we  have to track the whole dataset
## Not sure this is a feasibile step for mini epoch training
metawriter.log_dataset("data/raw_data", "input")

### creating the data slice - Today we have only path and hash.
### Would need  to expand to take in more metadata
for i in range(1,3,1):
    dataslice = metawriter.create_dataslice("slice-" + str(i))
    for i in range(1,20,1):
        j = random.randrange(100)
        dataslice.add_data("data/raw_data/"+str(j)+".xml", {"key1":"value1", "key2":"value2"})

    dataslice.commit()



## reading the files in the slice
df = metawriter.read_dataslice("slice-1")
record = ""
row_content = None
#data/raw_data/59.xml
for label, content in df.iterrows():
    record = label
    row_content = content

print("Before update")
print(label)
print(row_content)
#Update the metadata for a record in the slice
metawriter.update_dataslice("slice-1",record, {"key1":"1", "key2":"2"})
df = metawriter.read_dataslice("slice-1")


print("After update")
for label, content in df.iterrows():
    if label == record:
        print(content)
