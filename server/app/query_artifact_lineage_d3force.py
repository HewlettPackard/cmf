import pandas as pd
from cmflib.cmfquery import CmfQuery
import warnings
import typing as t

warnings.filterwarnings("ignore")

def truncate_artifact_name(my_str):
    if "/" in my_str:
        my_str = my_str.split("/")[-1]
    temp = my_str.split(":")
    temp[1] = temp[1][:4]
    temp=":".join(temp)
    return temp

def query_artifact_lineage_d3force(query: CmfQuery, pipeline_name, dict_of_art_ids: t.Dict[str, t.Dict[str, pd.DataFrame]]) -> dict:
    art_name_id = {}
    artifact_name_list = []
    node_id_name_list = []
    pipeline_id=query.get_pipeline_id(pipeline_name)
    for type_, df in dict_of_art_ids[pipeline_name].items():
        for index, row in df.iterrows():
            artifact_name_list.append(row["name"])
            art_name_id[row["name"]] = row["id"]
            result="#48D1CC" if type_ == "Dataset" else "#2E8B57" if type_ =="Model" else "#FF8C00"
            node_id_name_list.append({"name": truncate_artifact_name(row["name"]), "id": row["id"], "color": result})
    link_list = []
    for art_name in artifact_name_list:
        immediate_child_artifacts = query.get_one_hop_child_artifacts(art_name, pipeline_id)
        if immediate_child_artifacts.empty == True:
            pass
        else:
            for i in list(set(immediate_child_artifacts["name"])):
                link = {}
                srce_art_id = art_name_id[art_name]
                trgt_art_id = art_name_id[i]
                link["source"] = int(srce_art_id)
                link["target"] = (trgt_art_id)
                link_list.append(link)

    new_list = pd.DataFrame(
    link_list
    ).drop_duplicates().to_dict('records')
    data = {
        "nodes" : node_id_name_list,
        "links" : new_list
    }
    return data

#print(query_visualization("/home/chobey/repair_lineage/testenv/example-get-started/mlmd","Test-env"))
