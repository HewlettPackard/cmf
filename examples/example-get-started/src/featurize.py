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

import os
import sys
import yaml
import pickle
import click
import collections
import numpy as np
import pandas as pd
import scipy.sparse as sparse
from sklearn.feature_extraction.text import (CountVectorizer, TfidfTransformer)
from cmflib import cmf

__all__ = ['featurize']


def _get_df(data: str) -> pd.DataFrame:
    df = pd.read_csv(
        data,
        encoding="utf-8",
        header=None,
        delimiter="\t",
        names=["id", "label", "text"],
    )
    sys.stderr.write(f"The input data frame {data} size is {df.shape}\n")
    return df


def _save_matrix(df: pd.DataFrame, matrix, output: str) -> None:
    id_matrix = sparse.csr_matrix(df.id.astype(np.int64)).T
    label_matrix = sparse.csr_matrix(df.label.astype(np.int64)).T

    result = sparse.hstack([id_matrix, label_matrix, matrix], format="csr")

    msg = "The output matrix {} size is {} and data type is {}\n"
    sys.stderr.write(msg.format(output, result.shape, result.dtype))

    with open(output, "wb") as fd:
        pickle.dump(result, fd)


def featurize(input_dir: str, output_dir: str) -> None:
    """ Create train and test Machine Learning datasets.
    Args:
        input_dir: Path to a directory containing train.tsv and test.tsv files.
        output_dir: Path to a directory that will contain train.pkl and test.pkl files.

    Machine Learning Artifacts:
        Input: ${input_dir}/train.tsv, ${input_dir}/test.tsv
        Output: ${output_dir}/train.pkl, ${output_dir}/test.pkl
    """
    params = yaml.safe_load(open("params.yaml"))["featurize"]
    np.set_printoptions(suppress=True)

    Dataset = collections.namedtuple('Dataset', ['train', 'test'])
    input_ds = Dataset(train=os.path.join(input_dir, "train.tsv"), test=os.path.join(input_dir, "test.tsv"))

    os.makedirs(output_dir, exist_ok=True)
    output_ds = Dataset(train=os.path.join(output_dir, "train.pkl"), test=os.path.join(output_dir, "test.pkl"))
    graph_env = os.getenv("NEO4J", "False")
    graph = True if graph_env == "True" or graph_env == "TRUE" else False
    metawriter = cmf.Cmf(filepath="mlmd", pipeline_name="Test-env", graph=graph)

    _ = metawriter.create_context(pipeline_stage="Featurize")
    _ = metawriter.create_execution(execution_type="Featurize-execution", custom_properties=params)

    _ = metawriter.log_dataset(input_ds.train, "input")
    _ = metawriter.log_dataset(input_ds.test, "input")

    # Generate train feature matrix
    df_train = _get_df(input_ds.train)
    train_words = np.array(df_train.text.str.lower().values.astype("U"))

    bag_of_words = CountVectorizer(
        stop_words="english", max_features=params["max_features"], ngram_range=(1, params["ngrams"])
    )

    bag_of_words.fit(train_words)
    train_words_binary_matrix = bag_of_words.transform(train_words)
    tfidf = TfidfTransformer(smooth_idf=False)
    tfidf.fit(train_words_binary_matrix)
    train_words_tfidf_matrix = tfidf.transform(train_words_binary_matrix)

    _save_matrix(df_train, train_words_tfidf_matrix, output_ds.train)

    # Generate test feature matrix
    df_test = _get_df(input_ds.test)
    test_words = np.array(df_test.text.str.lower().values.astype("U"))
    test_words_binary_matrix = bag_of_words.transform(test_words)
    test_words_tfidf_matrix = tfidf.transform(test_words_binary_matrix)

    _save_matrix(df_test, test_words_tfidf_matrix, output_ds.test)

    _ = metawriter.log_dataset(output_ds.train, "output")
    _ = metawriter.log_dataset(output_ds.test, "output")


@click.command()
@click.argument('input_dir', required=True, type=str)
@click.argument('output_dir', required=True, type=str)
def featurize_cli(input_dir: str, output_dir: str) -> None:
    featurize(input_dir, output_dir)


if __name__ == '__main__':
    featurize_cli()
