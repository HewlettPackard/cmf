import uuid
import json
my_uuid = str(uuid.uuid4())
dict_ = {'uuid_var': my_uuid}
with open('uuid.json','w') as f:
    json.dump(dict_, f)