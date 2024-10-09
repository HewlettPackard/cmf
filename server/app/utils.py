def modify_arti_name(arti_name, type):
    # artifact_name optimization based on artifact type.["Dataset","Model","Metrics"]
    try:
        spliting_arti = arti_name.split(':')
        name = ""
        if type == "Metrics" :   # Example metrics:4ebdc980-1e7c-11ef-b54c-25834a9c665c:388 -> metrics:4ebd:388
            name = f"{spliting_arti[0]}:{spliting_arti[1][:4]}:{spliting_arti[2]}"
        elif type == "Model":
            #first split on ':' then on '/' to get name. Example 'Test-env/prepare:uuid:32' -> prepare_uuid
            name = spliting_arti[-3].split("/")[-1] + ":" + spliting_arti[-2][:4]
        elif type == "Dataset":
            # Example artifacts/data.xml.gz:236d9502e0283d91f689d7038b8508a2 -> data.xml.gz:236d
            name = arti_name.rsplit(':')[0] .split("/")[-1] + ":" +  spliting_arti[-1][:4]
        elif type == "Dataslice":
            # cmf_artifacts/dataslices/ecd6dcde-4f3b-11ef-b8cd-f71a4cc9ba38/slice-1:e77e3466872898fcf2fa22a3752bc1ca
            dataslice_part1 = arti_name.split("/",1)[1] #remove cmf_artifacts/
            # dataslices/ecd6dcde-4f3b-11ef-b8cd-f71a4cc9ba38/slice-1 + : + e77e
            name = dataslice_part1.rsplit(":",-1)[0] + ":" + dataslice_part1.rsplit(":",-1)[-1][:4]
        elif type == "Step_Metrics":
            #cmf_artifacts/metrics/1a86b01c-4da9-11ef-b8cd-f71a4cc9ba38/training_metrics:d7c32a3f4fce4888c905de07ba253b6e:3:2029c720-4da9-11ef-b8cd-f71a4cc9ba38
            step_new = arti_name.split("/",1)[1]     #remove cmf_artifacts/
            step_metrics_part2 = arti_name.rsplit(":")
            # metrics/1a86b01c-4da9-11ef-b8cd-f71a4cc9ba38/training_metrics: + d7c3 + : +3 + : + 2029
            name = step_new.rsplit(":",-3)[0] + ":" + step_metrics_part2[-3][:4] + ":" + step_metrics_part2[-2] + ":" + step_metrics_part2[-1][:4]
        else:
            name = arti_name  
    except Exception as e:
        print(f"Error parsing artifact name: {e}")
        name = arti_name  # Fallback to the original arti_name in case of error
    return name
