import io
import os
import zipfile
import httpx
import pandas as pd
import typing as t
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from jsonpath_ng.ext import parse
from cmflib.cmfquery import CmfQuery
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from server.app.db.dbqueries import (
    create_schedule,
    update_schedule_fields,
    log_sync_run,
    get_registered_server_by_name_url,
)

#Converts sync functions to async
async def async_api(function_to_async, query: CmfQuery, *argv):
    return await run_in_threadpool(function_to_async, query, *argv)


def get_model_data(query: CmfQuery, modelId: int):
    '''
      This function retrieves the necessary model data required for generating a model card.

      Arguments:
        modelId (int): The ID of the model for which data is required.

      Returns:
        This function returns a tuple of DataFrames containing the following:

        model_data_df (DataFrame): Metadata related to the model itself.
        model_exe_df (DataFrame): Metadata of the executions in which the specified modelId was an input or output.
        model_input_df (DataFrame): Metadata of input artifacts that led to the creation of the model.
        model_output_df (DataFrame): Metadata of artifacts that used the model as an input.
        The returned DataFrames provide comprehensive metadata for the specified model, aiding in the creation of detailed and accurate model cards.
    '''
    pd.set_option('display.max_columns', None)
    model_data_df = pd.DataFrame()
    model_exe_df = pd.DataFrame()
    model_input_df = pd.DataFrame()
    model_output_df = pd.DataFrame()

    # get name from id
    modelName = ""
    model_data_df = query.get_all_artifacts_by_ids_list([modelId])
    # if above dataframe is not empty, we have the dataframe for given modelId with full model related details
    if model_data_df.empty:
        return model_data_df, model_exe_df, model_input_df, model_output_df
    # However following check is done, in case, variable 'modelId' is not an ID for model artifact
    modelType = model_data_df['type'].tolist()[0]
    if not modelType == "Model":
        # making model_data_df empty
        model_data_df = pd.DataFrame()
        return model_data_df, model_exe_df, model_input_df, model_output_df

    # extracting modelName
    modelName = model_data_df['name'].tolist()[0]

    # model's executions data with props and custom props
    exe_df = query.get_all_executions_for_artifact(modelName)
    exe_ids = []
    if not exe_df.empty:
        exe_df.drop(columns=['execution_type_name', 'execution_name'], inplace=True)
        exe_ids = exe_df['execution_id'].tolist()

    if not exe_ids:
         return model_data_df, model_exe_df, model_input_df, model_output_df
    model_exe_df = query.get_all_executions_by_ids_list(exe_ids)
    model_exe_df.drop(columns=['Git_Start_Commit', 'Git_End_Commit'], inplace=True)

    in_art_ids =  []
    # input artifacts
    # it is usually not a good practice to use functions starting with _ outside of the file they are defined .. should i change??
    in_art_ids.extend(query._get_input_artifacts(exe_ids))
    if modelId in in_art_ids:
        in_art_ids.remove(modelId)
    model_input_df = query.get_all_artifacts_by_ids_list(in_art_ids)

    out_art_ids = []
    # output artifacts
    out_art_ids.extend(query._get_output_artifacts(exe_ids))
    if modelId in out_art_ids:
        out_art_ids.remove(modelId)
    model_output_df = query.get_all_artifacts_by_ids_list(out_art_ids)

    return model_data_df, model_exe_df, model_input_df, model_output_df


def get_all_exe_ids(query: CmfQuery, pipeline_name: t.Optional[str] = None) -> t.Dict[str, pd.DataFrame]:
    '''
    Returns:
    returns a dictionary which has pipeline_name as key and dataframe which includes {id,Execution_uuid,Context_Type,Context_id} as value.
    '''
    execution_ids = {}
    executions = pd.DataFrame()    # df is emptied to store execution ids for next pipeline.
    if pipeline_name:
        executions = query.get_all_executions_in_pipeline(pipeline_name)
        if not executions.empty:
            execution_ids[pipeline_name] = executions[['id', 'Context_Type', 'Execution_uuid', 'Context_ID']]
        else:
            execution_ids[pipeline_name] = pd.DataFrame()
    else:
        names = query.get_pipeline_names()
        for name in names:
            executions = pd.DataFrame()    # df is emptied to store execution ids for next pipeline.
            executions = query.get_all_executions_in_pipeline(name)
            # check if df is empty return just pipeline_name: {}
            # if df is not empty return dictionary with pipeline_name as key
            # and df with id, context_type, uuid, context_ID as value.
            if not executions.empty:
                execution_ids[name] = executions[['id', 'Context_Type', 'Execution_uuid', 'Context_ID']]
            else:
                execution_ids[name] = pd.DataFrame()
    return execution_ids


def get_all_artifact_ids(query: CmfQuery, execution_ids, pipeline_name: t.Optional[str] = None) -> t.Dict[str, t.Dict[str, pd.DataFrame]]:
    # following is a dictionary of dictionaries

    # First level dictionary key is pipeline_name
    # First level dicitonary value is nested dictionary
    # Nested dictionary key is type i.e. Dataset, Model, etc.
    # Nested dictionary value is a pandas df with id and artifact name
    artifact_ids: t.Dict[str, t.Dict[str, pd.DataFrame]] = {}
    artifacts = pd.DataFrame()
    if pipeline_name:
        if not execution_ids.get(pipeline_name).empty:
            exe_ids = execution_ids[pipeline_name]['id'].tolist()
            artifacts = query.get_all_artifacts_for_executions(exe_ids)
            #acknowledging pipeline exist even if df is empty. 
            if artifacts.empty:
                artifact_ids[pipeline_name] = {}   # { pipeline_name: {empty dict} }
            else:
                artifact_ids[pipeline_name] = {}
                for art_type in artifacts['type']:
                    filtered_values = artifacts.loc[artifacts['type'] == art_type, ['id', 'name']]
                    artifact_ids[pipeline_name][art_type] = filtered_values
        # if execution_ids is empty then create dictionary with key as pipeline name
        # and value as empty df
        else:
            artifact_ids[pipeline_name] = {}
    else:
        names = query.get_pipeline_names()
        for name in names:
            if not execution_ids.get(name).empty:
                exe_ids = execution_ids[name]['id'].tolist()
                artifacts = query.get_all_artifacts_for_executions(exe_ids)
                #acknowledging pipeline exist even if df is empty. 
                if artifacts.empty:
                    artifact_ids[name] = {}   # { pipeline_name: {empty dict} }
                else:
                    artifact_ids[name] = {}
                    for art_type in artifacts['type']:
                        filtered_values = artifacts.loc[artifacts['type'] == art_type, ['id', 'name']]
                        artifact_ids[name][art_type] = filtered_values
            # if execution_ids is empty then create dictionary with key as pipeline name
            # and value as empty df
            else:
                artifact_ids[name] = {}
    return artifact_ids


def get_artifact_types(query: CmfQuery) -> t.List[str]:
    artifact_types = query.get_all_artifact_types()
    return artifact_types


def get_mlmd_from_server(query: CmfQuery, pipeline_name: t.Optional[str] = None, exec_uuid: t.Optional[str] = None, last_sync_time: t.Optional[str] = None, 
                         dict_of_exe_ids: t.Optional[dict] = None) -> t.Optional[str]:
    """
    Retrieves metadata from the server for a given pipeline and execution UUID if mentioned.

    Args:
        query (CmfQuery): The CmfQuery object.
        pipeline_name (str): The name of the pipeline.
        exec_uuid (str): The execution UUID.
        dict_of_exe_ids (dict): A dictionary containing execution IDs for pipelines.

    Returns:
        json_payload (str or None): The metadata in JSON format if found, "no_exec_uuid" 
        if the execution UUID is not found, or None if the pipeline name is not available.
    """
    json_payload = None
    flag=False
    if pipeline_name == None and not last_sync_time:
        # in case of first sync or second sync we don't know if there is one pipeline or multiple pipelines
        if last_sync_time is None:
            json_payload = query.extract_to_json(0)
    elif pipeline_name == None and last_sync_time:
        json_payload = query.extract_to_json(int(last_sync_time))
    else:
        if(pipeline_name is not None and query.get_pipeline_id(pipeline_name) != -1 and dict_of_exe_ids is not None):  # checks if pipeline name is available in mlmd
            if exec_uuid != None:
                dict_of_exe_ids = dict_of_exe_ids[pipeline_name]
                # Loop through each row in the DataFrame since `dict_of_exe_ids` is a pandas DataFrame.
                for index, row in dict_of_exe_ids.iterrows():
                    # When user reuses execution, execution_uuid get appeneded separated by ","
                    exec_uuid_list = row['Execution_uuid'].split(",")
                    if exec_uuid in exec_uuid_list:
                        flag=True
                        break
                if not flag:
                    json_payload = "no_exec_uuid"
                    return json_payload
            json_payload = query.dumptojson(pipeline_name, exec_uuid)
    return json_payload


def executions_list(query: CmfQuery, pipeline_name, dict_of_exe_ids):
    list_of_exec = []
    list_of_exec_uuid = []
    list_of_exec = dict_of_exe_ids[pipeline_name]["Context_Type"].tolist()
    list_of_uuid = dict_of_exe_ids[pipeline_name]["Execution_uuid"].tolist()
    for exec_type, uuid in zip(list_of_exec, list_of_uuid):
        list_of_exec_uuid.append(exec_type.split("/",1)[1] + "_" + uuid.split("-")[0][:4])
    print(type(list_of_exec_uuid))
    return list_of_exec_uuid


async def server_mlmd_pull(server_url, last_sync_time):
    """
    Fetch mlmd data from a specified server.

    Args:
        server_url (str): The full URL of the target server.
        last_sync_time (int): The last sync time in milliseconds since epoch.

    Returns:
        dict: The mlmd data fetched from the specified server.

    Raises:
        HTTPException: If the server is not reachable or an error occurs during the request.
    """
    try:
        # Step 1: Send a request to the target server to fetch mlmd data
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(f"{server_url}/api/mlmd_pull", json={'last_sync_time': last_sync_time})

                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail="Target server did not respond successfully")

                json_payload = response.json()
                python_env_store_path = "/cmf-server/data/env"

                if last_sync_time:
                    # Extract the Environment file names from the JSON payload
                    data = json_payload
                    jsonpath_expr = parse('$..events[?(@.artifact.type == "Environment")].artifact.name')
                    environment_names = {match.value.split(":")[0].split("/")[-1] for match in jsonpath_expr.find(data)}

                    # Check if the list is empty or not
                    if len(environment_names) == 0: 
                        print("No Environment files are found inside json payload.")
                        return json_payload

                    list_of_files = list(environment_names)
                    python_env_zip = await client.get(f"{server_url}/api/download-python-env", params=list_of_files)
                else:
                    python_env_zip = await client.get(f"{server_url}/api/download-python-env", params=None)

                if python_env_zip.status_code == 200:
                    try:
                        # Create the directory if it doesn't exist
                        os.makedirs(python_env_store_path, exist_ok=True)

                        # Unzip the zip file content
                        with zipfile.ZipFile(io.BytesIO(python_env_zip.content)) as zf:
                            # Extract all files to a temporary directory
                            temp_dir = os.path.join(python_env_store_path, "temp_extracted")
                            os.makedirs(temp_dir, exist_ok=True)
                            zf.extractall(temp_dir)

                            # Move all extracted files to the target directory
                            for root, dirs, files in os.walk(temp_dir):
                                for file in files:
                                    src_file = os.path.join(root, file)
                                    dest_file = os.path.join(python_env_store_path, file)
                                    try:
                                        os.rename(src_file, dest_file)
                                        print(f"Moved {src_file} to {dest_file}")
                                    except Exception as e:
                                        print(f"Failed to move {src_file} to {dest_file}: {e}")

                            # Clean up the temporary directory
                            os.rmdir(temp_dir)
                        # print("Storing at:", os.path.abspath(python_env_store_path))
                        # print("Files in target directory:", os.listdir(python_env_store_path))
                        print("All files stored successfully.")
                    except Exception as e:
                        print(f"Error during file extraction or storage: {e}")
                else:
                    print(f"Failed to download ZIP file. Status code: {python_env_zip.status_code}")
            except httpx.RequestError:
                raise HTTPException(status_code=500, detail="Target server is not reachable")
        return json_payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch mlmd data: {e}")


async def log_sync_attempt(
    status: str,
    message: str,
    db: AsyncSession,
    server_name: str,
    server_url: str,
    current_utc_epoch_time: int,
    skip_logging: bool,
):
    """
    Input: status (str), message (str), db (AsyncSession), server_name (str), server_url (str), current_utc_epoch_time (int), skip_logging (bool)
    Output: None
    Description: Persists manual/immediate sync run records in schedule/log tables.
    Step 1: Skip immediately when skip_logging is true to avoid duplicate scheduler logs.
    Step 2: Resolve server row from registered servers table.
    Step 3: Create one-time synthetic schedule entry for sync_now log grouping.
    Step 4: Mark synthetic schedule completed and insert sync log entry.
    Example: manual /sync call writes sync_type="sync_now" log row."""
    
    # Log the sync attempt in the database with status and message.
    # When scheduler already writes logs, skip to avoid duplicate entries.
    if skip_logging:
        return
    try:
        server_row = await get_registered_server_by_name_url(db, server_name, server_url)
        if server_row:
            created = await create_schedule(
                db,
                server_id=server_row["id"],
                timezone="UTC",
                start_time_utc=current_utc_epoch_time,
                next_run_time_utc=current_utc_epoch_time,
                created_at=current_utc_epoch_time,
                one_time=True,
            )
            await update_schedule_fields(
                db,
                schedule_id=created["id"],
                active=False,
                status="completed",
            )
            await log_sync_run(
                db,
                schedule_id=created["id"],
                run_time_utc=current_utc_epoch_time,
                status=status,
                message=message,
                sync_type="sync_now",
            )
    except Exception as log_error:
        print(
            f"Failed to record immediate sync log entry for server '{server_name}' at '{server_url}'. "
            f"Error details: {log_error}"
        )


DAY_NAME_TO_WEEKDAY = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def get_timezone(timezone: str) -> ZoneInfo:
    """Return a safe timezone object for periodic sync calculations.
    """
    try:
        return ZoneInfo(timezone)
    except Exception:
        return ZoneInfo("UTC")


def parse_schedule_time(value: t.Optional[str], field_name: str) -> tuple[int, int]:
    """ Parse HH:MM time strings used by daily and weekly periodic sync rules.
        For example, "14:30" -> (14, 30) for 2:30 PM."
    """
    try:
        parsed = datetime.strptime(value or "", "%H:%M")
    except ValueError as exc:
        raise ValueError(f"{field_name} must use HH:MM format") from exc
    return parsed.hour, parsed.minute


async def compute_next_run_from_recurrence(
    current_run_utc_ms: int,
    timezone: str,
    recurrence_mode: str,
    interval_unit: t.Optional[str] = None,
    interval_value: t.Optional[int] = None,
    daily_time: t.Optional[str] = None,
    weekly_day: t.Optional[str] = None,
    weekly_time: t.Optional[str] = None,
    strict_after: bool = True,
) -> int:
    """Compute the next periodic sync run time from the stored recurrence rule.

    This is used after each periodic execution so interval/daily/weekly
    schedules continue with their exact user-defined behavior.

    Example:
    If a job runs now at Monday 10:00 (local timezone):
    - interval every 30 minutes -> next run is Monday 10:30
    - daily at 09:00 -> next run is Tuesday 09:00
    - weekly on friday at 15:00 -> next run is Friday 15:00
    """
    # Resolve timezone (fallback to UTC if invalid).
    tz = get_timezone(timezone)
    # Convert current run time from epoch ms to UTC datetime.
    current_dt_utc = datetime.fromtimestamp(current_run_utc_ms / 1000.0, tz=ZoneInfo("UTC"))
    # Convert UTC datetime to user's local timezone.
    current_dt_local = current_dt_utc.astimezone(tz)

    # Compute next local run using selected recurrence rule.
    if recurrence_mode == "interval":
        # Interval mode: add N minutes/hours from current local time.
        if interval_unit == "minutes" and interval_value:
            next_dt_local = current_dt_local + timedelta(minutes=interval_value)
        elif interval_unit == "hours" and interval_value:
            next_dt_local = current_dt_local + timedelta(hours=interval_value)
        else:
            raise ValueError("Interval schedules require interval_unit and interval_value")
    elif recurrence_mode == "daily":
        # Daily mode: parse target HH:MM.
        hours, minutes = parse_schedule_time(daily_time, "daily_time")
        # Build candidate run time for today in local timezone.
        next_dt_local = current_dt_local.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        # Move to tomorrow if candidate is not valid for "next" run.
        if (strict_after and next_dt_local <= current_dt_local) or (not strict_after and next_dt_local < current_dt_local):
            next_dt_local += timedelta(days=1)
    elif recurrence_mode == "weekly":
        # Weekly mode: map weekday name to weekday number.
        target_weekday = DAY_NAME_TO_WEEKDAY.get((weekly_day or "").lower())
        if target_weekday is None:
            # Weekly mode requires a valid weekday string.
            raise ValueError("Weekly schedules require a valid weekly_day")
        # Parse target HH:MM for the selected weekday.
        hours, minutes = parse_schedule_time(weekly_time, "weekly_time")
        # Build candidate on current week/day at target time.
        next_dt_local = current_dt_local.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        # Compute day distance to target weekday.
        days_until_target = (target_weekday - next_dt_local.weekday()) % 7
        # If same day but time already passed, schedule next week.
        if days_until_target == 0 and ((strict_after and next_dt_local <= current_dt_local) or (not strict_after and next_dt_local < current_dt_local)):
            days_until_target = 7
        # Shift candidate to the target weekday.
        next_dt_local += timedelta(days=days_until_target)
    else:
        raise ValueError(f"Unsupported recurrence mode: {recurrence_mode}")

    # Convert computed local run back to UTC epoch ms.
    next_dt_utc = next_dt_local.astimezone(ZoneInfo("UTC"))
    return int(next_dt_utc.timestamp() * 1000)


async def compute_initial_next_run_utc(
    start_utc_ms: int,
    now_utc_ms: int,
    timezone: str,
    recurrence_mode: str,
    interval_unit: t.Optional[str] = None,
    interval_value: t.Optional[int] = None,
    daily_time: t.Optional[str] = None,
    weekly_day: t.Optional[str] = None,
    weekly_time: t.Optional[str] = None,
) -> int:
    """Compute the first due time when a periodic schedule is created.

    This ensures new schedules start at the correct next valid recurrence
    point based on start time, timezone, and recurrence mode.

    Example:
    If user creates schedule at Monday 10:00 (local timezone):
    - interval every 2 hours with past start -> first due is next 2-hour slot
    - daily at 09:00 -> first due is Tuesday 09:00
    - weekly on friday at 15:00 -> first due is upcoming Friday 15:00
    """
    # For interval schedules, compute the next slot after "now" based on the start time anchor.
    if recurrence_mode == "interval":
        # If start time is in the future, use it as the first due time.
        if start_utc_ms > now_utc_ms:
            return start_utc_ms
        # Convert interval to milliseconds.
        if interval_unit == "minutes" and interval_value:
            interval_ms = interval_value * 60 * 1000
        elif interval_unit == "hours" and interval_value:
            interval_ms = interval_value * 60 * 60 * 1000
        else:
            raise ValueError("Interval schedules require interval_unit and interval_value")
        # Compute elapsed time since start.
        elapsed = now_utc_ms - start_utc_ms
        # Jump to next interval slot after "now".
        steps = (elapsed // interval_ms) + 1
        return start_utc_ms + (steps * interval_ms)

    # For daily/weekly, anchor to the later of start and now.
    reference_utc_ms = max(start_utc_ms, now_utc_ms)
    # Reuse recurrence calculator for first valid due time.
    return await compute_next_run_from_recurrence(
        reference_utc_ms,
        timezone,
        recurrence_mode,
        interval_unit=interval_unit,
        interval_value=interval_value,
        daily_time=daily_time,
        weekly_day=weekly_day,
        weekly_time=weekly_time,
        strict_after=False,
    )


""" Old implemenation of fetching executions """
# def get_executions(query: CmfQuery, pipeline_name, exe_ids) -> pd.DataFrame:
#     '''
#     Args:
#      pipeline_name: name of the pipeline.
#      exe_ids: list of execution ids.

#     Returns:
#      returns dataframe of executions using execution_ids.
#     '''
#     df = pd.DataFrame()
#     executions = query.get_all_executions_by_ids_list(exe_ids)
#     df = pd.concat([df, executions], sort=True, ignore_index=True)
#     return df



""" Old implementation for lineage """
# def get_lineage_data(
#         query: CmfQuery, 
#         pipeline_name, type,
#         dict_of_art_ids,
#         dict_of_exe_ids):
#     """
#     Retrieves lineage data based on the specified type.

#     Parameters:
#     query (CmfQuery): The CmfQuery object
#     pipeline_name (str): The name of the pipeline.
#     type (str): The type of lineage data to retrieve. Can be "Artifacts" or "Execution".
#     dict_of_art_ids (dict): A dictionary of artifact IDs.
#     dict_of_exe_ids (dict): A dictionary of execution IDs.

#     Returns:
#     dict or list: 
#         - If type is "Artifacts", returns a dictionary with nodes and links for artifact lineage.
#                 lineage_data= {
#                     nodes:[],
#                     links:[]
#                 }
#         - If type is "Execution", returns a list of execution types for the specified pipeline.
#         - Otherwise, returns visualization data for artifact execution.
#     """
#     if type=="Artifacts":
#         lineage_data = query_artifact_lineage_d3force(query, pipeline_name, dict_of_art_ids)
#     elif type=="Execution":
#         lineage_data = query_list_of_executions(pipeline_name, dict_of_exe_ids)
#     else:
#         pass
#     return lineage_data

""" This is an old implementation of get_artifacts - not used anymore """
# def get_artifacts(query: CmfQuery, pipeline_name, art_type, artifact_ids):
#     df = pd.DataFrame()
#     if (query.get_pipeline_id(pipeline_name) != -1):
#         df = query.get_all_artifacts_by_ids_list(artifact_ids)
#         if len(df) == 0:
#             return
#         df = df.drop_duplicates()
#         art_names = df['name'].tolist()
#         name_dict = {}
#         name_list = []
#         exec_type_name_list = []
#         exe_type_name = pd.DataFrame()
#         for name in art_names:
#             executions = query.get_all_executions_for_artifact(name)
#             exe_type_name = pd.concat([exe_type_name, executions], ignore_index=True)
#             execution_type_name = exe_type_name["execution_type_name"].drop_duplicates().tolist()
#             execution_type_name = [str(element).split('"')[1] for element in execution_type_name]
#             execution_type_name_str = ',\n '.join(map(str, execution_type_name))
#             name_list.append(name)
#             exec_type_name_list.append(execution_type_name_str)
#         name_dict['name'] = name_list
#         name_dict['execution_type_name'] = exec_type_name_list
#         name_df = pd.DataFrame(name_dict)
#         merged_df = df.merge(name_df, on='name', how='left')
#         merged_df['name'] = merged_df['name'].apply(lambda x: x.split(':')[0] if ':' in x else x)
#         merged_df = merged_df.loc[merged_df["type"] == art_type]
#         result = merged_df.to_json(orient="records")
#         tempout = json.loads(result)
#         return tempout
