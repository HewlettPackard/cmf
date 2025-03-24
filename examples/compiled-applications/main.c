#include "log_metric.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// Example to use log_metric_lib
int main() {
    cmf_init("/home/kulkashr/test/mlmd", "testsk", "testsk", "testsk");

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

    const char *keys1[] = {"train1_loss"};
    const char *values1[] = {"10"};

    log_metric("test1_metrics", keys1, values1, 1);

    // Commit metrics
    commit_metrics("test1_metrics");

    // Finalize
    cmf_finalize();

    return 0;
}

/*
Compilation command
gcc -o main main.c log_metric_lib.c     -I$(python -c "from sysconfig import get_path; print(get_path('include'))")     -L$(python -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")     -lpython$(python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")     -lpthread     -Wl,-rpath,$(python -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")

export LD_LIBRARY_PATH=$(python -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))"):$LD_LIBRARY_PATH
*/
