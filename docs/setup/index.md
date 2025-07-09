# Product Installation & Setup Guide

## **Overview**

This guide provides step-by-step instructions for installing and setting up cmf. The installation process consists of three main components:

1. **cmflib: \[Name or Description]**
2. **cmf-client: \[Name or Description]**
3. **cmf-server C: \[Name or Description]**

### **1. Prerequisites**

* System requirements
* Required software or dependencies
* Administrator access or permissions

---

### **2. Installation Components**

#### **2.1 Install Component A: \[Name or Description]**

* **Purpose**: Briefly describe what this component does.
* **Steps**:

  1. Download the installer or package.
  2. Run the installer and follow on-screen instructions.
  3. Configure \[relevant settings].

#### **2.2 Install Component B: \[Name or Description]**

* **Purpose**: Briefly describe what this component does.
* **Steps**:

  1. Set up required environment (e.g., database, service).
  2. Install the component.
  3. Verify installation using \[command/tool].

#### **2.3 Install Component C: \[Name or Description]**

* **Purpose**: Briefly describe what this component does.
* **Steps**:

  1. Install the component.
  2. Configure \[settings or files].
  3. Confirm successful integration with A and B.

---

### **3. Configuration & Setup**

* Connect components if needed (e.g., APIs, databases).
* Apply initial configuration settings.
* Run initial test to verify system integrity.

---

### **4. Post-Installation Checklist**

* ✅ All components installed
* ✅ Services running
* ✅ Configuration complete
* ✅ Product tested successfully

---

### **5. Troubleshooting**

* Common issues and fixes for each component
* Log file locations
* Support contact information

---

Let me know the names of your components if you'd like this tailored to your specific product.


## Install cmf library i.e. cmflib
Before proceeding, ensure that the CMF library is installed on your system. If not, follow the installation instructions provided in the [Installation & Setup](../setup/index.md) page.

## Install cmf-server
cmf-server is a key interface for the user to explore and track their ML training runs. It allows users to store the metadata file on the cmf-server. The user can retrieve the saved metadata file and can view the content of the saved metadata file using the UI provided by the cmf-server.

Follow the instructions on the [Installation & Setup](../setup/index.md) page for details on how to setup a cmf-server.

## Setup a cmf-client
cmf-client is a tool that facilitates metadata collaboration between different teams or two team members. It allows users to pull or push metadata from or to the cmf-server.

Follow the below-mentioned steps for the end-to-end setup of cmf-client:-

## Pre-Requisites:
* 3.9 >= Python < 3.11
* Git latest version

!!! warning "Python 3.9 Installation Issue on Ubuntu"

    **Issue**: When creating Python 3.9 virtual environments, you may encounter:
    ```
    ModuleNotFoundError: No module named 'distutils.cmd'
    ```

    **Root Cause**: Python 3.9 may be missing required modules like `distutils` or `venv` when installed on Ubuntu systems.

    **Resolution**:

    1. Add the deadsnakes PPA (provides newer Python versions):
       ```bash
       sudo add-apt-repository ppa:deadsnakes/ppa
       sudo apt-get update
       ```

    2. Install Python 3.9 with required modules:
       ```bash
       sudo apt install python3.9 python3.9-dev python3.9-distutils
       ```

    This ensures Python 3.9 and its essential modules are fully installed.

#### 2. Set up Python Virtual Environment:

=== "Using Conda"
    ```shell
    conda create -n cmf python=3.10
    conda activate cmf
    ```

=== "Using VirtualEnv"
    ```shell
    virtualenv --python=3.10 .cmf
    source .cmf/bin/activate
    ```

#### 3. Install CMF:

=== "Latest version from GitHub"
    ```shell
    pip install git+https://github.com/HewlettPackard/cmf
    ```

=== "Stable version from PyPI"
    ```shell
    # pip install cmflib
    ```

## Next Steps

After installing CMF, proceed to configure the CMF server and client. For detailed configuration instructions, refer to the [Quick start with cmf-client](./cmf_client/step-by-step.md) page.
