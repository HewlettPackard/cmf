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
import re
import sys
import yaml
import gzip
import random
import typing as t
import collections
import click
import xml.etree.ElementTree
from cmflib.cmf import Cmf

__all__ = ['parse']


""" In the traditional apporach in CMF, the typical sequence involves the
    initialization of the Cmf class, the creation of a context (analogous
    to a stage in Machine Learning), and the creation an execution before
    logging datasets, models, or metrics.
    However, CMF provides a streamlined feature wherein users have the flexibility
    to log datasets, models, and metrics without the explicit requirement of
    creating a context and an execution.
"""

def _process_posts(fd_in: t.IO, fd_out_train: t.IO, fd_out_test: t.IO, target_tag: str, split: int) -> None:
    for idx, line in enumerate(fd_in):
        try:
            fd_out = fd_out_train if random.random() > split else fd_out_test
            attr = xml.etree.ElementTree.fromstring(line).attrib

            pid = attr.get("Id", "")
            label = 1 if target_tag in attr.get("Tags", "") else 0
            title = re.sub(r"\s+", " ", attr.get("Title", "")).strip()
            body = re.sub(r"\s+", " ", attr.get("Body", "")).strip()
            text = title + " " + body

            fd_out.write("{}\t{}\t{}\n".format(pid, label, text))
        except Exception as ex:
            sys.stderr.write(f"Skipping the broken line {idx}: {ex}\n")


def parse(input_file: str, output_dir: str) -> None:
    """ Parse input file (input_file) and create train/test files in output_dir directory.
    Args:
         input_file: Path to a compressed (.gz) XML-lines file (data.xml.gz).
         output_dir: Path to a directory that will contain train (train.tsv) and test (test.tsv) files.

    Machine Learning Artifacts:
        Input: ${input_file}
        Output: ${output_dir}/train.tsv, ${output_dir}/test.tsv
    """
    params = yaml.safe_load(open("params.yaml"))["parse"]
    random.seed(params["seed"])
    # Cmf class takes four parameters: filename, pipeline_name, custom_properties, graph
    # User can pass any combination of these four.
    metawriter = Cmf()
    _ = metawriter.log_dataset(input_file, "input", custom_properties={"user-metadata1": "metadata_value"}, \
                                label="artifacts/labels.csv", label_properties={"user1": "xyz"})


    os.makedirs(output_dir, exist_ok=True)
    Dataset = collections.namedtuple('Dataset', ['train', 'test'])
    output_ds = Dataset(train=os.path.join(output_dir, "train.tsv"), test=os.path.join(output_dir, "test.tsv"))

    with gzip.open(input_file, "rb") as fd_in,\
         io.open(output_ds.train, "w", encoding="utf8") as fd_out_train,\
         io.open(output_ds.test, "w", encoding="utf8") as fd_out_test:
        _process_posts(fd_in, fd_out_train, fd_out_test, "<python>", params["split"])

    _ = metawriter.log_dataset(output_ds.train, "output")
    _ = metawriter.log_dataset(output_ds.test, "output")


@click.command()
@click.argument('input_file', required=True, type=str)
@click.argument('output_dir', required=True, type=str)
def parse_cli(input_file: str, output_dir: str) -> None:
    parse(input_file, output_dir)


if __name__ == '__main__':
    parse_cli()
