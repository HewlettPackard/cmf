import requests
import json
url="http://127.0.0.1:8000"
r=requests.get(url)

json_payload= {
   "Pipeline": [
      {
         "create_time_since_epoch": 1664313166038,
         "custom_properties": {},
         "id": 1,
         "last_update_time_since_epoch": 1664313166038,
         "name": "Test-env",
         "properties": {
            "Pipeline": "Test-env"
         },
         "type": "",
         "type_id": 10,
         "stages": [
            {
               "create_time_since_epoch": 1664313166046,
               "custom_properties": {
                  "user-metadata1": "metadata_value"
               },
               "id": 2,
               "last_update_time_since_epoch": 1664313166046,
               "name": "Prepare",
               "properties": {
                  "Pipeline_Stage": "Prepare"
               },
               "type": "",
               "type_id": 11,
               "executions": [
                  {
                     "create_time_since_epoch": 1664313166058,
                     "custom_properties": {
                        "seed": 20170428,
                        "split": 0.2
                     },
                     "id": 1,
                     "last_update_time_since_epoch": 1664313166058,
                     "name": "",
                     "properties": {
                        "Git_Start_Commit": "aedf51d8098fe3c47a73064dbce60080f0d71090",
                        "Execution": "['src/parse.py', 'artifacts/data.xml.gz', 'artifacts/parsed']",
                        "Context_Type": "Prepare",
                        "Context_ID": 2,
                        "Git_Repo": "/tmp/cmf/example_get_started/git_remote",
                        "Pipeline_id": 1,
                        "Git_End_Commit": "",
                        "Pipeline_Type": "Test-env"
                     },
                     "type": "",
                     "type_id": 12,
                     "events": [
                        {
                           "type": 3,
                           "artifact": {
                              "create_time_since_epoch": 1664313168112,
                              "custom_properties": {
                                 "user-metadata1": "metadata_value",
                                 "user-metadata2": "metadata_value"
                              },
                              "id": 1,
                              "last_update_time_since_epoch": 1664313176015,
                              "name": "artifacts/data.xml.gz:236d9502e0283d91f689d7038b8508a2",
                              "properties": {
                                 "git_repo": "/tmp/cmf/example_get_started/git_remote",
                                 "Commit": "commit 03c25dfdb6c188b7b04f7e675dec072de192b851"
                              },
                              "type": "",
                              "type_id": 13
                           }
                        },
                        {
                           "type": 4,
                           "artifact": {
                              "create_time_since_epoch": 1664313172179,
                              "custom_properties": {},
                              "id": 2,
                              "last_update_time_since_epoch": 1664313172179,
                              "name": "artifacts/parsed/train.tsv:32b715ef0d71ff4c9e61f55b09c15e75",
                              "properties": {
                                 "Commit": "commit 341efc55b9c2f4974189f7c7b423ccec18047394",
                                 "git_repo": "/tmp/cmf/example_get_started/git_remote"
                              },
                              "type": "",
                              "type_id": 13
                           }
                        },
                        {
                           "type": 4,
                           "artifact": {
                              "create_time_since_epoch": 1664313174106,
                              "custom_properties": {},
                              "id": 3,
                              "last_update_time_since_epoch": 1664313174106,
                              "name": "artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81",
                              "properties": {
                                 "git_repo": "/tmp/cmf/example_get_started/git_remote",
                                 "Commit": "commit c9f7d9b2f0829e6c43d8776fef0a2edc04000f3a"
                              },
                              "type": "",
                              "type_id": 13
                           }
                        }
                     ]
                  }
               ]
            },
            {
               "create_time_since_epoch": 1664313178873,
               "custom_properties": {},
               "id": 3,
               "last_update_time_since_epoch": 1664313178873,
               "name": "Featurize",
               "properties": {
                  "Pipeline_Stage": "Featurize"
               },
               "type": "",
               "type_id": 11,
               "executions": [
                  {
                     "create_time_since_epoch": 1664313178883,
                     "custom_properties": {
                        "max_features": 3000,
                        "ngrams": 2
                     },
                     "id": 2,
                     "last_update_time_since_epoch": 1664313178883,
                     "name": "",
                     "properties": {
                        "Execution": "['src/featurize.py', 'artifacts/parsed', 'artifacts/features']",
                        "Pipeline_Type": "Test-env",
                        "Git_Repo": "/tmp/cmf/example_get_started/git_remote",
                        "Git_End_Commit": "",
                        "Pipeline_id": 1,
                        "Git_Start_Commit": "c9f7d9b2f0829e6c43d8776fef0a2edc04000f3a",
                        "Context_Type": "Featurize-execution",
                        "Context_ID": 3
                     },
                     "type": "",
                     "type_id": 14,
                     "events": [
                        {
                           "type": 3,
                           "artifact": {
                              "create_time_since_epoch": 1664313172179,
                              "custom_properties": {},
                              "id": 2,
                              "last_update_time_since_epoch": 1664313172179,
                              "name": "artifacts/parsed/train.tsv:32b715ef0d71ff4c9e61f55b09c15e75",
                              "properties": {
                                 "git_repo": "/tmp/cmf/example_get_started/git_remote",
                                 "Commit": "commit 341efc55b9c2f4974189f7c7b423ccec18047394"
                              },
                              "type": "",
                              "type_id": 13
                           }
                        },
                        {
                           "type": 3,
                           "artifact": {
                              "create_time_since_epoch": 1664313174106,
                              "custom_properties": {},
                              "id": 3,
                              "last_update_time_since_epoch": 1664313174106,
                              "name": "artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81",
                              "properties": {
                                 "git_repo": "/tmp/cmf/example_get_started/git_remote",
                                 "Commit": "commit c9f7d9b2f0829e6c43d8776fef0a2edc04000f3a"
                              },
                              "type": "",
                              "type_id": 13
                           }
                        },
                        {
                           "type": 4,
                           "artifact": {
                              "create_time_since_epoch": 1664313198441,
                              "custom_properties": {},
                              "id": 4,
                              "last_update_time_since_epoch": 1664313198441,
                              "name": "artifacts/features/train.pkl:c565b23737962d61ccf1122cb211fc37",
                              "properties": {
                                 "git_repo": "/tmp/cmf/example_get_started/git_remote",
                                 "Commit": "commit ddb1e04ce70eb3c957f295866a0396c906bc317f"
                              },
                              "type": "",
                              "type_id": 13
                           }
                        },
                        {
                           "type": 4,
                           "artifact": {
                              "create_time_since_epoch": 1664313200629,
                              "custom_properties": {},
                              "id": 5,
                              "last_update_time_since_epoch": 1664313200629,
                              "name": "artifacts/features/test.pkl:96af3114a0c204043ded8c419eab8dbe",
                              "properties": {
                                 "git_repo": "/tmp/cmf/example_get_started/git_remote",
                                 "Commit": "commit 7a319a3cafad1fe6f2ab91f9a92401bf67a429fb"
                              },
                              "type": "",
                              "type_id": 13
                           }
                        }
                     ]
                  }
               ]
            },
            {
               "create_time_since_epoch": 1664313203354,
               "custom_properties": {},
               "id": 4,
               "last_update_time_since_epoch": 1664313203354,
               "name": "Train",
               "properties": {
                  "Pipeline_Stage": "Train"
               },
               "type": "",
               "type_id": 11,
               "executions": [
                  {
                     "create_time_since_epoch": 1664313203369,
                     "custom_properties": {
                        "min_split": 64,
                        "seed": 20170428,
                        "n_est": 100
                     },
                     "id": 3,
                     "last_update_time_since_epoch": 1664313203369,
                     "name": "",
                     "properties": {
                        "Git_End_Commit": "",
                        "Execution": "['src/train.py', 'artifacts/features', 'artifacts/model']",
                        "Context_ID": 4,
                        "Pipeline_Type": "Test-env",
                        "Git_Start_Commit": "7a319a3cafad1fe6f2ab91f9a92401bf67a429fb",
                        "Context_Type": "Train-execution",
                        "Git_Repo": "/tmp/cmf/example_get_started/git_remote",
                        "Pipeline_id": 1
                     },
                     "type": "",
                     "type_id": 15,
                     "events": [
                        {
                           "type": 3,
                           "artifact": {
                              "create_time_since_epoch": 1664313198441,
                              "custom_properties": {},
                              "id": 4,
                              "last_update_time_since_epoch": 1664313198441,
                              "name": "artifacts/features/train.pkl:c565b23737962d61ccf1122cb211fc37",
                              "properties": {
                                 "git_repo": "/tmp/cmf/example_get_started/git_remote",
                                 "Commit": "commit ddb1e04ce70eb3c957f295866a0396c906bc317f"
                              },
                              "type": "",
                              "type_id": 13
                           }
                        },
                        {
                           "type": 4,
                           "artifact": {
                              "create_time_since_epoch": 1664313210080,
                              "custom_properties": {},
                              "id": 6,
                              "last_update_time_since_epoch": 1664313210080,
                              "name": "artifacts/model/model.pkl:9351b160e2e355b1412633cdfb0460c7:3",
                              "properties": {
                                 "model_framework": "SKlearn",
                                 "Commit": "commit 1146dad8b74cae205db6a3132ea403db1e4032e5",
                                 "model_type": "RandomForestClassifier",
                                 "model_name": "RandomForestClassifier:default"
                              },
                              "type": "",
                              "type_id": 16
                           }
                        }
                     ]
                  }
               ]
            },
            {
               "create_time_since_epoch": 1664313212856,
               "custom_properties": {},
               "id": 5,
               "last_update_time_since_epoch": 1664313212856,
               "name": "Evaluate",
               "properties": {
                  "Pipeline_Stage": "Evaluate"
               },
               "type": "",
               "type_id": 11,
               "executions": [
                  {
                     "create_time_since_epoch": 1664313212866,
                     "custom_properties": {},
                     "id": 4,
                     "last_update_time_since_epoch": 1664313212866,
                     "name": "",
                     "properties": {
                        "Git_Repo": "/tmp/cmf/example_get_started/git_remote",
                        "Execution": "['src/test.py', 'artifacts/model', 'artifacts/features', 'artifacts/test_results']",
                        "Git_End_Commit": "",
                        "Git_Start_Commit": "1146dad8b74cae205db6a3132ea403db1e4032e5",
                        "Pipeline_Type": "Test-env",
                        "Pipeline_id": 1,
                        "Context_ID": 5,
                        "Context_Type": "Evaluate-execution"
                     },
                     "type": "",
                     "type_id": 17,
                     "events": [
                        {
                           "type": 3,
                           "artifact": {
                              "create_time_since_epoch": 1664313210080,
                              "custom_properties": {},
                              "id": 6,
                              "last_update_time_since_epoch": 1664313210080,
                              "name": "artifacts/model/model.pkl:9351b160e2e355b1412633cdfb0460c7:3",
                              "properties": {
                                 "model_type": "RandomForestClassifier",
                                 "model_name": "RandomForestClassifier:default",
                                 "Commit": "commit 1146dad8b74cae205db6a3132ea403db1e4032e5",
                                 "model_framework": "SKlearn"
                              },
                              "type": "",
                              "type_id": 16
                           }
                        },
                        {
                           "type": 3,
                           "artifact": {
                              "create_time_since_epoch": 1664313200629,
                              "custom_properties": {},
                              "id": 5,
                              "last_update_time_since_epoch": 1664313200629,
                              "name": "artifacts/features/test.pkl:96af3114a0c204043ded8c419eab8dbe",
                              "properties": {
                                 "Commit": "commit 7a319a3cafad1fe6f2ab91f9a92401bf67a429fb",
                                 "git_repo": "/tmp/cmf/example_get_started/git_remote"
                              },
                              "type": "",
                              "type_id": 13
                           }
                        },
                        {
                           "type": 4,
                           "artifact": {
                              "create_time_since_epoch": 1664313217131,
                              "custom_properties": {
                                 "avg_prec": 0.604054,
                                 "roc_auc": 0.960802
                              },
                              "id": 7,
                              "last_update_time_since_epoch": 1664313217131,
                              "name": "metrics:40866eee-3ea9-11ed-99a3-b47af137252e:4",
                              "properties": {
                                 "metrics_name": "metrics:40866eee-3ea9-11ed-99a3-b47af137252e:4"
                              },
                              "type": "",
                              "type_id": 18
                           }
                        }
                     ]
                  }
               ]
            }
         ]
      }
   ]
}


x=requests.post("http://127.0.0.1:8000/mlmd",json=json_payload)
print(x.json())
print("Status code -",x.status_code)

