from cmflib.cmf import Cmf
from cmflib.cmfquery import CmfQuery


metawriter = Cmf("mlmd", "test-execution-update")
query = CmfQuery("mlmd")
ctx = metawriter.child_context = metawriter.create_context("Train")
exes = query.get_all_exe_in_stage(ctx.name)
if len(exes) == 0:
    print("This script needs to be run after `test_execution_update.py`")
    exit()

print("===========printing previous execution================")
print(exes[0])

for exe in exes:
    if exe.name == "Train-execution":
        execution = exes[0]
metawriter.execution = execution

_ = metawriter.log_dataset("artifacts/data.xml.gz", "input", custom_properties={"user-metadata1": "metadata_value"})
_ = metawriter.log_execution_metrics("metrics-1", {"auc":0.3})

metawriter.finalize()
print("Test executed successfully")
