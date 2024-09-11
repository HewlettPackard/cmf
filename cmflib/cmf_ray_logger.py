from ray import tune
from ray.tune import Callback
from cmflib import cmf

class CmfRayLogger(Callback):
    #id_count = 1
    
    def __init__(self, pipeline_name, file_path, pipeline_stage):
        """
        pipeline_name: The name of the CMF Pipelibe
        file_path: The path to metadata file
        pipeline_stage: The name for the stage of cmf_pipeline
        """
        self.pipeline_name = pipeline_name
        self.file_path = file_path
        self.pipeline_stage = pipeline_stage
        self.cmf_obj = {}
        self.cmf_run = {}

    def on_trial_start(self, iteration, trials, trial, **info):
        trial_id = trial.trial_id
        trial_config = trial.config
        print(f"CMF Logging Started for Trial {trial_id}")
        self.cmf_obj[trial_id] = cmf.Cmf(filepath = self.file_path, pipeline_name = self.pipeline_name)
        _ = self.cmf_obj[trial_id].create_context(pipeline_stage = self.pipeline_stage)
        _ = self.cmf_obj[trial_id].create_execution(execution_type=f"Trial_{trial_id}",
                                            create_new_execution = False,
                                            custom_properties = {'Configuration': trial_config})
        #self.execution_id[trial_id] = CmfRayLogger.id_count
        #CmfRayLogger.id_count+=1

    def on_trial_result(self, iteration, trials, trial, result, **info):
        trial_id = trial.trial_id
        trial_config = trial.config
        trial_result = trial.last_result
        curr_res = result
        #print(f'In Trial Results')
        print(f'Trial_ID: {trial_id}')
        print(f'curr_results is {curr_res}')
        print(f'Logging results to CMF with metric name Trial_{trial_id}_metrics')
        #if trial_id in self.execution_id:
        #    _ = self.metawriter.update_execution(int(self.execution_id[trial_id]))
        _ = self.cmf_obj[trial_id].log_metric(metrics_name = f"Trial_{trial_id}_metrics",
                                      custom_properties = {'Output': curr_res})
        self.cmf_run[trial_id] = True
        
        
    def on_trial_complete(self, iteration, trials, trial, **info):
        trial_id = trial.trial_id
        trial_config = trial.config
        trial_result = trial.last_result
        
        print(f"Trial {trial_id} completed, Commiting to CMF: with name Trial_{trial_id}_metrics")
        print()
        #if trial_id in self.execution_id:
        #    _ = self.metawriter.update_execution(int(self.execution_id[trial_id]))
        _ = self.cmf_obj[trial_id].commit_metrics(f"Trial_{trial_id}_metrics")
        _ = self.cmf_obj[trial_id].log_execution_metrics(metrics_name = f"Trial_{trial_id}_Result",
                                      custom_properties = {'Result': trial_result})
        
    def on_trial_error(self, iteration, trials, trial, **info):
        trial_id = trial.trial_id
        trial_config = trial.config
        trial_result = trial.last_result

        print(f"An error occured with Trial {trial_id}, Not commiting anything to cmf")
        if self.cmf_run[trial_id]:
            _ = self.cmf_obj[trial_id].commit_metrics(f"Trial_{trial_id}_metrics")
            _ = self.cmf_obj[trial_id].log_execution_metrics(metrics_name = f"Trial_{trial_id}_Result",
                                      custom_properties = {'Result': '-inf'})