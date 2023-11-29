# Sanity Testing

## Description

The "Sanity Testing" focuses on performing sanity testing for basic functionalities of the server, client, and public API. This type of testing ensures that the essential features of your application are working as expected after changes or updates.

## Features

- Testing of essential functionalities of the server.
- Testing of basic client interactions.
- Testing of public API endpoints.

## Installation
### Install [cmf](../docs/index.md#installation)
### Install pytest to Run Tests

To run the tests, you'll need to have pytest installed. If you haven't already installed pytest, you can do so using pip:

```bash
pip install pytest
```

To get started with the sanity testing project, follow these steps:
### Feature 1: Server
### Feature 2: Client Interactions

In the "Client Interactions" feature, we perform a variety of tasks related to initializing repositories, managing artifacts, and handling metadata using the command-line client. This section outlines the specific commands and interactions involved.

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
To test the `CMF Client`, follow these steps:

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
   "cmf_server_url": "http://10.10.200.200:8080",
   "ssh_path": "ssh://10.10.200.200/home/hpe-user/ssh-storage",
   ```
5. **Run the Sanity Testing Script:** Execute the sanity testing script using the following command:
   ```bash
   python sanity_testing.py
   ```
   > Ensure you are running `sanity_testing.py` from the `cmf/test` folder.
