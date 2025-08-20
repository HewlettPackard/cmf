#include "log_metric.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// Example to use log_metric_lib
int main() {
    cmf_init("/tmp/test/mlmd", "testsk", "testsk", "testsk");

    if (!is_cmf_initialized()) {
        printf("CMF initialization failed.\n");
        return 1;
    }

    srand(time(NULL));

    const char *keys[] = {"train_loss"};
    const char *values[] = {"10"};

    // Log training metric
    log_metric("test_metrics", keys, values, 1);

    // Commit metrics
    commit_metrics("test_metrics");

    const char *keys1[] = {"train1_loss","train2_loss","train3_loss"};
    const char *values1[] = {"10","10.12","[10,10.00,12]"};

    log_metric("test1_metrics", keys1, values1, 3);

    // Commit metrics
    commit_metrics("test1_metrics");

    // Finalize
    cmf_finalize();

    return 0;
}
