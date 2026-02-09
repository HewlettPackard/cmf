from cmflib.cmf import Cmf
from cmflib.cmfquery import CmfQuery

query = CmfQuery("mlmd")
if len(query.get_pipeline_names()) == 0:
    print("This script needs to be run after test_execution_update.py")
    exit()
pipeline_name = query.get_pipeline_names()[0]
print(pipeline_name)

metawriter = Cmf("mlmd", "test-execution-update")
_ = metawriter.create_context("Train")
_ = metawriter.create_execution("Train-execution",{"name":"test-1"}, create_new_execution=False)

_ = metawriter.log_dataset("artifacts/data.xml.gz", "input", custom_properties={"user-metadata1": "metadata_value"})
_ = metawriter.log_execution_metrics("metrics-1", {"auc":0.4})

metawriter.finalize()
print("Test executed successfully")
