# SSH Remote Artifact Repo Setup
## Steps to set up a SSH Remote Repo
SSH (Secure Shell) remote storage refers to using the SSH protocol to securely access and manage files and data on a remote server or storage system over a network. SSH is a cryptographic network protocol that allows secure communication and data transfer between a local computer and a remote server.

Proceed with the following steps to set up a SSH Remote Repository:

1. Get started with initializing `project directory` with SSH repo.                                       
2. Check whether cmf is initialized in your project directory with following command.
   ```
   cmf init show
   ```
   If cmf is not initialized, the following message will appear on the screen.
   ```
   'cmf' is not configured.
   Execute the 'cmf init' command.
   ```

3.  Execute the following command to initialize the SSH remote storage as a CMF artifact repository.
    ```
    cmf init sshremote --path ssh://127.0.0.1/home/user/ssh-storage --user XXXXX --port 22 --password example@123 --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://127.0.0.1:80 
    ```
    > When running `cmf init sshremote`, please ensure that the specified IP address has the necessary permissions to allow access using the specified user ('XXXX'). If the IP address or user lacks the required permissions, the command will fail.

4. Execute `cmf init show` to check the CMF configuration.
5. To address permissions issues related to SSH, it is recommended to initiate troubleshooting by examining the `/etc/ssh/sshd_config file`. This configuration file serves as the primary starting point for diagnosing and resolving SSH permission-related challenges.
