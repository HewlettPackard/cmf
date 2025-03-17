#include "log_metric_lib.h"
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>

// Define CMF struct (private to this file)
static struct {
    PyObject* cmf_pyobject;
} Cmf = {NULL}; // Initialize to NULL

// Initialize CMF
void cmf_init(void) {
    Py_Initialize();
    
    PyObject *cmflib_module = PyImport_ImportModule("cmflib.cmf");
    if (!cmflib_module) {
        PyErr_Print();
        return;
    }

    PyObject *cmf_class = PyObject_GetAttrString(cmflib_module, "Cmf");
    if (!cmf_class) {
        PyErr_Print();
        Py_DECREF(cmflib_module);
        return;
    }

    // Initialize Cmf object with Params
    // 1. mlmd file path
    // 2. pipeline name
    PyObject *args = PyTuple_Pack(2, PyUnicode_FromString("/home/kulkashr/testcmf/mlmd"), PyUnicode_FromString("test_pipeline"));
    Cmf.cmf_pyobject = PyObject_CallObject(cmf_class, args);

    Py_DECREF(args);
    Py_DECREF(cmf_class);
    Py_DECREF(cmflib_module);

    if (!Cmf.cmf_pyobject) {
        printf("Failed to initialize CMF.\n");
        PyErr_Print();
        return;
    }

    // Create context and execution
    PyObject_CallMethod(Cmf.cmf_pyobject, "create_context", "s", "Train-test");
    PyObject_CallMethod(Cmf.cmf_pyobject, "create_execution", "s", "Train-test-execution");
}

// Check if CMF is initialized
int is_cmf_initialized(void) {
    return Cmf.cmf_pyobject != NULL;
}

// Log metric function
void log_metric(const char *key, const char *value) {
    if (!Cmf.cmf_pyobject) {
        printf("CMF not initialized!\n");
        return;
    }

    PyObject *result = PyObject_CallMethod(Cmf.cmf_pyobject, "log_metric", "ss", key, value);
    if (!result) PyErr_Print();
    else Py_DECREF(result);
}

// Commit metrics function
void commit_metrics(const char *metrics_name) {
    if (!Cmf.cmf_pyobject) {
        printf("CMF not initialized!\n");
        return;
    }

    PyObject *result = PyObject_CallMethod(Cmf.cmf_pyobject, "commit_metrics", "s", metrics_name);
    if (!result) PyErr_Print();
    else Py_DECREF(result);
}

// Finalize CMF and Python
void cmf_finalize(void) {
    if (Cmf.cmf_pyobject) {
        Py_DECREF(Cmf.cmf_pyobject);
        Cmf.cmf_pyobject = NULL;
    }
    Py_Finalize();
}
