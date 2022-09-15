#!/usr/bin/env python 3
from cmflib import cmfquery
from cmflib import artifacts
import sys
#arg=sys.argv   when command is created arguments will be passed using sys.argv
arg=['/home/abhinavchobey/bin/cmf','pull','Test-env']
cmd=arg[1]

def cmf(arg):
    if len(arg) > 3:
        print("Error: more than two elements passed")
        print("Usage: cmf pull <'Pipeline_Name'>")
    elif len(arg)< 3:
        print("Error: Command not found")
    elif cmd=='pull':
        pipeline = arg[2]
        query = cmfquery.CmfQuery("./mlmd")
        stages = query.get_pipeline_stages(pipeline)

        identifiers=[]
        for i in stages:
            executions = query.get_all_executions_in_stage(i)       #getting all executions for stages
            dict_executions=executions.to_dict("dict")                            #converting it to dictionary
            identifiers.append(dict_executions['id'][0])               #id's of execution

        name=[]
        url=[]
        for identifier in identifiers:
            artifacts = query.get_all_artifacts_for_execution(identifier)   # getting all artifacts

            artifacts_dict=artifacts.to_dict('dict')                         #converting it to dictionary
            name.append(list(artifacts_dict['name'].values()))
            url.append(list(artifacts_dict['url'].values()))


        name_list_updated=[]
        url_list_updated=[]
        for i in range(len(name)):                                          #getting all the names and urls together
            name_list_updated=name_list_updated+name[i]
            url_list_updated=url_list_updated+url[i]

        final_list=[]
        file_name=[(i.split(':'))[0] for i in name_list_updated]           #getting names
        for i in (tuple(zip(file_name,url_list_updated))):
            if type(i[1])==str and i[1].startswith('s3://'):
                final_list.append(i)
        names_urls=list(set(final_list))                                   #list of tuple consist of names and urls
        print(names_urls)
        artifact_class_obj = artifacts.Artifacts()
        for name_url in names_urls:
            temp = name_url[1].split("/")
            bucket_name = temp[2]
            object_name = temp[3] + "/" + temp[4]
            stmt = artifact_class_obj.download_artifacts(bucket_name, object_name, name_url[0])
            print(stmt)
    else:
            print("Error:Command not found")









if __name__ == "__main__":
    cmf(arg)
