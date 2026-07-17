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
Change into the compiled applications directory
```sh
cd ./examples/compiled-applications
```

### 6️⃣ **Compile the C Code**
Build the library and these example applications
```sh
mkdir build && cd build
cmake ../../../ && make
```

### 7️⃣ **Create the cmflib directory**
TODO: Include directions when we change the interface to allow cmf init to configure the
directories

### 8️⃣ **Run the Compiled Binaries**
Execute the **compiled C program** to log metrics via Python:
```sh
./cmf-c-example
./cmf-fortran-example
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
