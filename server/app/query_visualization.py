import networkx as nx
import pandas as pd
from cmflib import cmfquery
import networkx
import matplotlib.pyplot as plt
import dvc
import warnings


def query_visualization(mlmd_path, pipeline_name):
    g = networkx.DiGraph()
    query = cmfquery.CmfQuery(mlmd_path)
    stages = query.get_pipeline_stages(pipeline_name)
    list_all_artifacts = []
    for stage in stages:
        executions = query.get_all_executions_in_stage(stage)
        artifacts = query.get_all_artifacts_for_execution(executions.iloc[0]["id"])
        for name in artifacts["name"]:
            list_all_artifacts.append(name)
    for artifact in list(set(list_all_artifacts)):
        g.add_node(artifact.split(":")[0])
        immediate_child_artifacts = query.get_one_hop_child_artifacts(artifact)
        if immediate_child_artifacts.empty == True:
            pass
        else:
            for i in immediate_child_artifacts["name"]:
                g.add_edge(artifact.split(":")[0], i.split(":")[0])
    pos = networkx.spiral_layout(g, scale=4)
    networkx.draw_networkx(
        g,
        pos,
        font_size=10,
        arrowsize=20,
        node_color="skyblue",
        node_size=400,
        with_labels=True,
    )
    plt.savefig(
        "./lineage.png", dpi=899, pad_inches=10
    )
    return True
    # query_visualization("/home/abhinavchobey/hpserver/cmf/local/example-get-started/mlmd",'Test-env' )
