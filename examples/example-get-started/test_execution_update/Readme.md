This folder contins examples for reusing executions and updating existing execution with additional metadata.
Some important points related to reusing executions:
1. Executions that needs to be reused should be created with flag create_new_execution set to false. This flag should be set as false, everytime a reusable execution is created(including the very first time)
Once a reusable execution is created, it can be reused using the following two methods:
    1. Exection can be reused as shown in "test_execution_update_method_1.py" by accessing an existing execution and setting it as the current execution 
    2. Execution can be reused as shown in "test_execution_update_method_2.py" by calling create_execution with create_new_execution flag set as false.

Some important points regarding metadata update of executions(adding additional custom properties after execution is created):
1. metadata update(adding custom properties) of existing executions are enabled using update_execution call. See "test_execution_update.py for examples". 
2. metadata can be updated for an existing execution in the local cmf and then pushed to server. The server will reflect all properties including the updated added properties. 
3. if an existing execution is pulled from the server and its metadata is updated using the update_execution call and pushed again, the new metadata will NOT be updated in the server side. In otherwords you cannot update metadata of existing executions in the server. 






