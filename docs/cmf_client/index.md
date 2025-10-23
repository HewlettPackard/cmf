# Quick start with cmf-client [NEEDS TO BE UPDATED]
Common metadata framework (`cmf`) has the following components:

- **Metadata Library**: exposes APIs for tracking pipeline metadata and provides endpoints to query stored metadata.
- **cmf-client**: handles metadata exchange with the `cmf-server`, pushes and pulls artifacts from the artifact repository, and syncs code to and from GitHub.
- **cmf-server**: interacts with all the remote clients and is responsible for merging the metadata transferred by the `cmf-client` and manage the consolidated metadata.
- **Central Artifact Repositories**: host the code and data.

This tutorial walks you through the process of setting up the `cmf-client`.

## Prerequisites 
Before proceeding with the setup, ensure the following components are up and running:

- [cmflib](../setup/index.md/#install-cmf-library-ie-cmflib)
- [cmf-server](../setup/index.md/#install-cmf-server-with-gui)

Make sure there are no errors during their startup, as `cmf-client` depends on both of these components.

## Setup a `cmf-client`
`cmf-client` is a command-line tool that facilitates metadata collaboration between different teams or two team members. It allows users to pull/push metadata from or to the `cmf-server` with similar functionalities for artifact repositories and other commands. 
** NEEDS TO BE UPDATED **
