from ray import tune
from ray.tune import Callback
from cmflib import cmf
import heapq

class CmfRayLogger(Callback):
    #id_count = 1
    
    def __init__(self, pipeline_name, file_path, pipeline_stage, data_dir = None, metric = 'accuracy', order = 'max', top_n=5 ):
        """
        pipeline_name: The name of the CMF Pipeline
        file_path: The path to metadata file
        pipeline_stage: The name for the stage of cmf_pipeline
        data_dir = Directory/File for data that is logged
        metric: The metric to track (e.g., 'accuracy', 'loss')
        order: 'max' for maximum, 'min' for minimum
        top_n: Number of top results to keep
        """
        self.pipeline_name = pipeline_name
        self.file_path = file_path
        self.pipeline_stage = pipeline_stage
        self.cmf_obj = {}
        self.cmf_run = {}
        self.data_dir = data_dir
        self.metric = metric
        self.order = order
        self.top_n = top_n
        
        # Initialize heap based on user-defined order
        self.heap = []
        self.heap_comparator = -1 if self.order == 'max' else 1
        
        # Dictionary to track best metric and model for each trial
        self.best_metric_values = {}
        self.best_models = {}
        self.execution_ids = {}

    def on_trial_start(self, iteration, trials, trial, **info):
        trial_id = trial.trial_id
        trial_config = trial.config
        print(f"CMF Logging Started for Trial {trial_id}")
        self.cmf_obj[trial_id] = cmf.Cmf(filepath = self.file_path, pipeline_name = self.pipeline_name)
        _ = self.cmf_obj[trial_id].create_context(pipeline_stage = self.pipeline_stage)
        execution_id = self.cmf_obj[trial_id].create_execution(execution_type=f"Trial_{trial_id}",
                                            create_new_execution = False,
                                            custom_properties = {'Configuration': trial_config})
        
        # Store the execution_type which will be used to update the execution later
        self.execution_ids[trial_id] = execution_id.id

        if self.data_dir:
            _ = self.cmf_obj[trial_id].log_dataset(url = str(self.data_dir), event = 'input')
        
        self.best_metric_values[trial_id] = None
        self.best_models[trial_id] = None

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
        
        # Track the current metric value and model path (if available)
        metric_value = curr_res.get(self.metric, None)
        model_path = curr_res.get('model_path', None) # Track the model path if available
        
        
        # Update best metric and model for the trial if necessary
        if metric_value is not None:
            if self.best_metric_values[trial_id] is None:
                self.best_metric_values[trial_id] = metric_value
                self.best_models[trial_id] = model_path
            else:
                # Update best metric based on order (max/min)
                if ((self.order == 'max' and metric_value > self.best_metric_values[trial_id]) or 
                    (self.order == 'min' and metric_value < self.best_metric_values[trial_id])):
                    self.best_metric_values[trial_id] = metric_value
                    self.best_models[trial_id] = model_path
        
    def on_trial_complete(self, iteration, trials, trial, **info):
        trial_id = trial.trial_id
        trial_config = trial.config
        trial_result = trial.last_result

        best_metric_value = self.best_metric_values.get(trial_id, None)
        best_model_path = self.best_models.get(trial_id, None)
        execution_id = self.execution_ids[trial_id]
        
        if best_metric_value is not None:
            # Push the best value of the trial and its corresponding model into the heap
            heapq.heappush(self.heap, (self.heap_comparator * best_metric_value, trial_id, best_metric_value, best_model_path,
                                       execution_id))
            if len(self.heap) > self.top_n:
                heapq.heappop(self.heap)  # Maintain top_n elements in the heap
        
            
            _ = self.cmf_obj[trial_id].log_execution_metrics(metrics_name=f"Best_{self.metric}_Trial_{trial_id}",
                                                             custom_properties={f'Best_{self.metric}': best_metric_value,
                                                                                'execution_id': execution_id}
                                                            )

        # Commit the metrics for the trial and log its final state
        print(f"Trial {trial_id} completed, Commiting to CMF: with name Trial_{trial_id}_metrics")
        print()

        _ = self.cmf_obj[trial_id].commit_metrics(f"Trial_{trial_id}_metrics")
        
        if best_model_path:
            _ = self.cmf_obj[trial_id].log_model(path=best_model_path, 
                                                 event='input', 
                                                 model_name=f"{trial_id}_model")
        
    def on_trial_error(self, iteration, trials, trial, **info):
        trial_id = trial.trial_id
        trial_config = trial.config
        trial_result = trial.last_result

        print(f"An error occured with Trial {trial_id}, Not commiting anything to cmf")
        if self.cmf_run[trial_id]:
            _ = self.cmf_obj[trial_id].commit_metrics(f"Trial_{trial_id}_metrics")
            _ = self.cmf_obj[trial_id].log_execution_metrics(metrics_name = f"Trial_{trial_id}_Result",
                                      custom_properties = {'Result': '-inf'})
            
    def on_experiment_end(self, trials, **info):
        """
        This function is called at the end of the experiment to log the top 'n' results and update execution
        with {'in_top_n': True} for each of the top trials.
        """
        print(f"Marking top {self.top_n} trials with 'in_top_n = True' at experiment end.")

        # Log the top 'n' trials from the heap
        while self.heap:
            _, top_trial_id, top_metric_value, top_model_path, top_execution_id = heapq.heappop(self.heap)
            print(f"Top trial: {top_trial_id} with {self.metric}: {top_metric_value}")

            # Update the execution for this trial with 'in_top_n = True'
            _ = self.cmf_obj[top_trial_id].update_execution(
                execution_id=top_execution_id,
                custom_properties={'in_top_n': True}
            )

            print(f"Execution {top_execution_id} for Trial {top_trial_id} updated with 'in_top_n = True'.")