# Sanity Testing

## Description

The "Sanity Testing" project focuses on performing sanity testing for basic functionalities of the server, client, and public API. This type of testing ensures that the essential features of your application are working as expected after changes or updates.

## Features

- Testing of essential functionalities of the server.
- Testing of basic client interactions.
- Testing of public API endpoints.

## Installation

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

1. `metadata push`: Push metadata to the repository.
2. `metadata pull`: Pull metadata from the repository.
3. `artifact pull`: Pull artifacts from the repository.
4. `artifact push`: Push artifacts to the repository.

These interactions with the client are crucial for ensuring the proper management and functioning of your content management system.
To test the `cmf` client, follow these additional steps:

1. **Copy `example-get-started` from `cmf/examples/` to your desired location outside the `cmf` folder.**

   You can use standard file operations to copy the folder. Here's an example command for Unix-based systems:

   ```bash
   cp -r /path/to/cmf/examples/example-get-started /path/to/destination/
   
2. **Copy a Test File `cmf/test/client/test_cmf.py` to the Copied `example-get-started` Folder:**
