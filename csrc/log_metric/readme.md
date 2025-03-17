# 🚀 CMF C Library: Python Wrappers for C-based Metric Logging  

This project provides **C-based Python wrappers** for **logging and committing metrics** using the [CMF Library](https://github.com/HewlettPackard/cmf). It enables seamless integration between **C programs and CMF’s Python-based metric tracking**.  

## 🔧 Installation & Usage  

Follow these steps to **set up the environment and compile the C code**:  

### 1️⃣ **Create a Conda Environment**  
Create a new Conda environment with **Python 3.10** and **libsqlite**:  
```sh
conda create -n cmf python=3.10 libsqlite=3.48.0
```  

### 2️⃣ **Activate the Environment**  
Activate the newly created **`cmf`** environment:  
```sh
conda activate cmf
```  

### 3️⃣ **Clone the CMF Repository**  
Download the CMF source code from GitHub:  
```sh
git clone https://github.com/HewlettPackard/cmf.git
```  

### 4️⃣ **Install CMF Python Package**  
Navigate to the **CMF root directory** and install it using `pip`:  
```sh
cd cmf
pip install .
```  

### 5️⃣ **Navigate to the `log_metric` Directory**  
Change into the CMF's C source directory:  
```sh
cd ./csrc/log_metric
```  

### 6️⃣ **Compile the C Code**  
Use `gcc` to compile the **C wrapper and main program** with **Python and pthread** support:  
```sh
gcc -o main main.c log_metric_lib.c \
    -I$(python -c "from sysconfig import get_path; print(get_path('include'))") \
    -L$(python -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))") \
    -lpython$(python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))") \
    -lpthread \
    -Wl,-rpath,$(python -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")
```  

### 7️⃣ **Set Library Path for Execution**  
Ensure the **Python shared libraries** are accessible at runtime:  
```sh
export LD_LIBRARY_PATH=$(python -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))"):$LD_LIBRARY_PATH
```  

### 8️⃣ **Run the Compiled Binary**  
Execute the **compiled C program** to log metrics via Python:  
```sh
./main
```  

---

## 📌 Example Output  
If everything is set up correctly, you should see logs similar to:  
```
*** Note: CMF will check out a new branch in git to commit the metadata files ***
*** The checked out branch is mlmd. ***
fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
IN commit output  cmf_artifacts/d5cda2ca-035e-11f0-9440-88e9a48ad2e2/metrics/test_metrics 19
if one
100% Adding...|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████|1/1 [00:00, 77.98file/s]
IN commit output  cmf_artifacts/d5cda2ca-035e-11f0-9440-88e9a48ad2e2/metrics/test1_metrics 19                                                                   
if one
100% Adding...|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████|1/1 [00:00, 68.58file/s]
```  

## 📖 How It Works  
- The **C wrapper (`log_metric_lib.c`)** initializes CMF in Python.  
- Logs and commits metrics using **Python API calls** from C.  
- Supports **multi-threaded execution with `pthread`** for performance.  

---
