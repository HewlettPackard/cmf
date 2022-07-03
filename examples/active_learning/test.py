import dvc.api

list_artifacts = [ "data/model-0", "data/model-1", "data/model-2", "data/round-0.txt", "data/round-1.txt", "data/round-2.txt"]
for l in list_artifacts:
    resource_url = dvc.api.get_url(l)
    print(resource_url)

