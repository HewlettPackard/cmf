#include "log_metric.h"
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

// Define CMF struct (private to this file)
static struct {
    PyObject* cmf_pyobject;
} Cmf = {NULL}; // Initialize to NULL

// Initialize CMF
void cmf_init(const char *mlmd_path,const char *pipeline_name, const char *context_name, const char *execution_name) {
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
    PyObject *args = PyTuple_Pack(2, PyUnicode_FromString(mlmd_path), PyUnicode_FromString(pipeline_name));
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
    PyObject_CallMethod(Cmf.cmf_pyobject, "create_context", "s", context_name);
    PyObject_CallMethod(Cmf.cmf_pyobject, "create_execution", "s", execution_name);
}

// Check if CMF is initialized
int is_cmf_initialized(void) {
    return Cmf.cmf_pyobject != NULL;
}

// Log metric function
void log_metric(const char *key, const char **dict_keys, const char **dict_values, int dict_size) {
    if (!Cmf.cmf_pyobject) {
        printf("CMF not initialized!\n");
        return;
    }

    // Create a Python dictionary
    PyObject *pDict = PyDict_New();
    if (!pDict) {
        printf("Failed to create Python dictionary!\n");
        return;
    }

    // Populate the dictionary
    for (int i = 0; i < dict_size; i++) {
        PyObject *pValue = NULL;

        // Check if the value is an integer
        int is_integer = 1;
        for (const char *ch = dict_values[i]; *ch != '\0'; ch++) {
            if (!isdigit(*ch) && *ch != '-') {  // Allow negative numbers
                is_integer = 0;
                break;
            }
        }

        if (is_integer) {
            pValue = PyLong_FromLong(atoi(dict_values[i]));  // Convert to Python integer
        } else {
            pValue = PyUnicode_FromString(dict_values[i]);   // Convert to Python string
        }

        if (!pValue) {
            printf("Failed to convert value to Python object!\n");
            Py_DECREF(pDict);
            return;
        }

        PyDict_SetItemString(pDict, dict_keys[i], pValue);
        Py_DECREF(pValue);  // Reduce reference count as PyDict_SetItemString doesn't steal it
    }

    // Call Python function with key and dictionary as arguments
    PyObject *result = PyObject_CallMethod(Cmf.cmf_pyobject, "log_metric", "sO", key, pDict);
    
    // Clean up
    Py_DECREF(pDict);
    
    if (!result) {
        PyErr_Print();
    } else {
        Py_DECREF(result);
    }
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
