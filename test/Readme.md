# Sanity Testing

## Description

The `Sanity Testing` focuses on performing sanity testing for basic functionalities of the cmf-server, cmf-client, and cmf metadata public API. This testing ensures that the essential features of your application are working as expected after development changes or updates.

## Features

- Testing of essential functionalities of the cmf-server.
- Testing of basic cmf-client interactions.
- Testing of cmf meatdata public API endpoints.

## Installation
### Install [cmf](../docs/index.md#installation)
### Install pytest to Run tests
To run the tests, you'll need to have pytest installed. If you haven't already installed pytest, you can do so using pip:
```bash
pip install pytest fastapi httpx matplotlib
```

To get started with the sanity testing project, follow these steps:
### Feature 1: Full Sanity Test Suite
In full sanity test suite, we are testing all the three components of the cmf i.e. cmf metadata library API, cmf-server, cmf-client.
To run the `full sanity test suite`, follow these steps:
1. Navigate to the `cmf` Directory
   ```bash
   cd cmf
   ```
2. **Edit the Docker Compose Configuration:** Open the `docker-compose-server.yml` file in your preferred text editor and make the necessary edits.
   ```bash
   nano docker-compose-server.yml
   ```
   For example:
   ```yaml
   volumes:
      - /home/hpe-user/cmf/test/cmf-server/data:/cmf-server/data
      - /home/hpe-user/cmf/test/cmf-server/data/static:/cmf-server/data/static
   ```
   > Ensure that you create the /server/data folder under cmf/test for a sandboxed testing environment.
3. Navigate to the `test` Directory
   ```bash
   cd test
   ```
4. **Edit the Configuration File:** Open the config.json file in your preferred text editor and make the necessary edits.
   ```bash
   nano config.json
   ```
   For example:
   ```json
   "cmf_server_url": "http://10.10.200.200:80",
   "ssh_path": "ssh://10.10.200.200/home/hpe-user/ssh-storage",
   "ssh_user": "xyz",
   "ssh_password": "wxyz"
   ```
5. **Run the client test suite:** Execute the sanity testing script using the following command:
   ```bash
   python sanity_testing.py
   ```
   > Ensure you are running `sanity_testing.py` from the `cmf/test` folder.

### Feature 2: `cmf-server` test suite
In the `cmf-server` test suite feature, we perform validaton of cmf-server api endpoints.
We are testing following cmf-server api commands:
1. `display_executions`: This api endpoint retrieves all the executions available on the cmf-server's master mlmd based on the pipeline-name provided.
2. `display_artifacts`: This api endpoint retrieves all the artifacts available on the cmf-server's master mlmd based on the pipeline-name provided.
3. `display_lineage`: This endpoint returns `artifact lineage` of the pipeline name passed.
4. `display_artifact_types`: This api endpoint retrieves `artifact types` as per the value of argument pipeline-name.
5. `display_pipelines`: This api endpoint retrieves all `pipeline names` available on the cmf-server's master mlmd.

To test the `cmf-server`, follow these steps:
1. Navigate to the `cmf` Directory
   ```bash
   cd cmf
   ```
2. Navigate to the `test` Directory
   ```bash
   cd test
   ```
3. **Edit the Configuration File:** Open the config.json file in your preferred text editor and make the necessary edits.
   ```bash
   nano config.json
   ```
   For example:
   ```json
   "cmf_server_url": "http://10.10.200.200:80",
   ```
5. **Run the client test suite:** Execute the sanity testing script using the following command:
   ```bash
   python server_api_endpoints_test_suite.py
   ```
   > Ensure you are running `python server_api_endpoints_test_suite.py` from the `cmf/test` folder.

### Feature 3: `cmf-client` test suite
In the "CMF Client Test Suite" feature, we perform a variety of tasks related to initializing repositories, managing artifacts, and handling metadata using the command-line client. This section outlines the specific commands and interactions involved.

**a) Initializing Repositories:**
We test the following repository initialization commands using the `cmf` client:
1. `cmf init show`: Initialize a repository for showing content.
2. `cmf init local`: Initialize a local repository.
3. `cmf init amazon S3`: Initialize a repository on Amazon S3.
4. `cmf init sshremote`: Initialize a repository for SSH remote access.
5. `cmf init minioS3`: Initialize a repository on Minio S3.

**b) Artifact and Metadata Commands:**
We test various artifact and metadata commands using the `cmf` client:
1. `metadata push`: Push metadata to the CMF server.
2. `metadata pull`: Pull metadata from the CMF server.
3. `artifact pull`: Pull artifacts from the repository.
4. `artifact push`: Push artifacts to the repository.

These interactions with the client are crucial for ensuring the proper management and functioning of your content management system.
To test the `cmf-client`, follow these steps:
1. Navigate to the `cmf` Directory
   ```bash
   cd cmf
   ```
2. **Edit the Docker Compose Configuration:** Open the `docker-compose-server.yml` file in your preferred text editor and make the necessary edits.
   ```bash
   nano docker-compose-server.yml
   ```
   For example:
   ```yaml
   volumes:
      - /home/hpe-user/cmf/test/cmf-server/data:/cmf-server/data
      - /home/hpe-user/cmf/test/cmf-server/data/static:/cmf-server/data/static
   ```
   > Ensure that you create the /server/data folder under cmf/test for a sandboxed testing environment.
3. Navigate to the `test` Directory
   ```bash
   cd test
   ```
4. **Edit the Configuration File:** Open the config.json file in your preferred text editor and make the necessary edits.
   ```bash
   nano config.json
   ```
   For example:
   ```json
   "cmf_server_url": "http://10.10.200.200:80",
   "ssh_path": "ssh://10.10.200.200/home/hpe-user/ssh-storage",
   "ssh_user": "xyz",
   "ssh_password": "wxyz"
   ```
5. **Run the client test suite:** Execute the sanity testing script using the following command:
   ```bash
   python client_test_suite.py
   ```
   > Ensure you are running `python client_test_suite.py` from the `cmf/test` folder.

### Feature 4: `cmf metadata` APIs test suite


