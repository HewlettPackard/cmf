from cmflib.cmf import Cmf
from cmflib.cmfquery import CmfQuery

metawriter = Cmf("mlmd", "test-execution-update")
_  = metawriter.create_context("Train", {"test":"1"})

#Creating execution with create_new_execution flag set to false.
#This flag enables creation of reusable executions
exe = metawriter.create_execution("Train-execution",create_new_execution=False )
print(exe)

#update_execution enables setting new metadata value for existing execution
metawriter.update_execution(exe.id, {"new_new":"value_value"})

#This call will not create new execution, it will re-use existing execution created above.
exe = metawriter.create_execution("Train-execution",create_new_execution=False )
print(exe)
#Update the execution with new meatadata values

metawriter.update_execution(exe.id, {"new_new_1":"value_value_1"})

metawriter.finalize()

print("Test executed successfully")

