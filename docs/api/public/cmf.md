# cmflib.cmf

::: cmflib.cmf.Cmf
    options:
      show_root_toc_entry: false
      merge_init_into_class: true
      docstring_style: google
      members:
        - __init__
        - create_context
        - create_execution
        - update_execution
        - log_dataset
        - log_model
        - log_execution_metrics
        - log_metric
        - create_dataslice
        - update_dataslice

::: cmflib.cmf
    options:
      show_root_toc_entry: false
      merge_init_into_class: true
      docstring_style: google
      members:
        - cmf_init_show
        - cmf_init
        - metadata_push
        - metadata_pull
        - metadata_export
        - artifact_pull
        - artifact_pull_single
        - artifact_push
        - artifact_list
        - pipeline_list
        - execution_list
        - repo_push
        - repo_pull
