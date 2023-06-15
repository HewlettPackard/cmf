import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import pandas as pd
from cmflib import cmfquery
import matplotlib.pyplot as plt
import dvc
import json
import random
import warnings

warnings.filterwarnings("ignore")


def query_visualization(mlmd_path, pipeline_name):
    g = nx.DiGraph()
    query = cmfquery.CmfQuery(mlmd_path)
    stages = query.get_pipeline_stages(pipeline_name)
    list_all_artifacts = []
    list_of_edges = []
    temp = []
    temp1 = []
    list_all_artifacts_with_chash = []
    artifact_name_type_dict = {}
    static_path= "/cmf-server/data/static/"
    for stage in stages:
        executions = query.get_all_executions_in_stage(stage)
        artifacts = query.get_all_artifacts_for_execution(executions.iloc[0]["id"])
        artifact_type_list = [i for i in artifacts["type"]]
        artifact_name_list = [i.split(":")[0].split("/")[-1] for i in artifacts["name"]]
        artifact_name_type_dict.update(
            dict(zip(artifact_name_list, artifact_type_list))
        )
        for name in artifacts["name"]:
            list_all_artifacts.append(name)
    list_all_artifacts_with_chash = list_all_artifacts

    for artifact in list(set(list_all_artifacts_with_chash)):
        temp1.append(artifact.split(":")[0].split("/")[-1])
        immediate_child_artifacts = query.get_one_hop_child_artifacts(artifact)
        if len(immediate_child_artifacts) != 0:
            temp1.extend(
                [
                    i.split(":")[0].split("/")[-1]
                    for i in list(set(immediate_child_artifacts["name"]))
                ]
            )
    list_all_artifacts = list(set(temp1))
    g.add_nodes_from(list_all_artifacts)
    for artifact in list(set(list_all_artifacts_with_chash)):
        immediate_child_artifacts = query.get_one_hop_child_artifacts(artifact)
        if immediate_child_artifacts.empty == True:
            pass
        else:
            for i in list(set(immediate_child_artifacts["name"])):
                g.add_edge(
                    (artifact.split(":")[0].split("/")[-1]),
                    i.split(":")[0].split("/")[-1],
                )
    nx.nx_agraph.write_dot(g, "Test.dot")
    node_color_list = []
    for i in list_all_artifacts:
        if i in artifact_name_type_dict.keys():
            if artifact_name_type_dict[i] == "Dataset":
                node_color_list.append("orange")
            elif artifact_name_type_dict[i] == "Model":
                node_color_list.append("skyblue")
            else:
                node_color_list.append("green")
        else:
            node_color_list.append("red")
    pos = graphviz_layout(g, prog="dot", args="-Grankdir=LR")
    nx.draw(
        g,
        pos,
        font_size=10,
        arrowsize=20,
        node_color=node_color_list,
        node_size=1000,
        with_labels=True,
    )

    img_path = "lineage" + str(random.randint(1, 20)) + ".png"
    img_path = static_path + img_path
    plt.savefig(
        img_path,
        bbox_inches="tight",
        pad_inches=1,
        orientation="landscape",
    )
    plt.figure().clear()
    return img_path
