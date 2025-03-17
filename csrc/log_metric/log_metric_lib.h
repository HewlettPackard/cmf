#ifndef LOG_METRIC_LIB_H
#define LOG_METRIC_LIB_H

void cmf_init(void);
void log_metric(const char *key, const char *value);
void commit_metrics(const char *metrics_name);
int is_cmf_initialized(void);
void cmf_finalize(void);

#endif
