from cmflib import cmf
from cmflib import cmfquery

query = cmfquery.CmfQuery("mlmd")
pipeline_name = query.get_pipeline_names()[0]
print(pipeline_name)
#stages = query.get_pipeline_stages(pipeline_name)
#train_stage = None
#for stage in stages:
#    print(stage)
#    if stage == pipeline_name+"/"+"Train":
#        train_stage = stage
#        break
#print(train_stage)
#execution = None
#exes = query.get_all_exe_in_stage(train_stage)
#print(exes[0])
#execution = exes[0]

metawriter = cmf.Cmf("mlmd", "test-execution-update")
_ = metawriter.create_context("Train")
_ = metawriter.create_execution("Train-execution",{"name":"test-1"}, create_new_execution=False)

_ = metawriter.log_dataset("artifacts/data.xml.gz", "input", custom_properties={"user-metadata1": "metadata_value"})
_ = metawriter.log_execution_metrics("metrics-1", {"auc":0.4})

metawriter.finalize()
