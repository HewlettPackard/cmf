#ifndef LOG_METRIC_LIB_H
#define LOG_METRIC_LIB_H

void cmf_init(const char *mlmd_path, const char *pipeline_name, const char *context_name, const char *execution_name);
int is_cmf_initialized(void);
void log_metric(const char *key, const char **dict_keys, const char **dict_values, int dict_size);
void commit_metrics(const char *metrics_name);
void cmf_finalize(void);

#endif
