# CMF Server & GUI Installation Guide

This document describes the process of launching the centralized CMF tracking backend using Docker Compose infrastructure.

## Infrastructure Prerequisites

### 1. Modern Docker Container Engine
* Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) with [non-root user](https://docs.docker.com/engine/install/linux-postinstall/) privileges.
* Install [Docker Compose Plugin](https://docs.docker.com/compose/install/linux/)

In earlier versions of Docker Compose, `docker compose` was independent of Docker. Hence, `docker-compose` was the command. However, after the introduction of Docker Compose Desktop V2, the compose command became part of Docker Engine. The recommended way to install Docker Compose is by installing a Docker Compose plugin on Docker Engine. For more information - [Docker Compose Reference](https://docs.docker.com/compose/reference/).

### 2. Enterprise Proxy Configuration
If your enterprise routes egress server traffic through a proxy network, you must inject these routing rules into your container runtime engine. Follow the official guide: Refer to the official Docker documentation for comprehensive instructions: [Configure the Docker Client for Proxy](https://docs.docker.com/network/proxy/#configure-the-docker-client).

---

### Installation Steps
**Step 1: Clone the GitHub Repository**

```bash
$ git clone https://github.com/HewlettPackard/cmf
```
**Output:** Cloning into 'cmf'...<br />
Resolving deltas: 100% (4632/4632), done.
   
---

**Step 2: Navigate to the CMF Directory**

```bash
$ cd cmf
```
**Output:** (cmf_env) /cmf$

---

**Step 3: Create Environment Configuration**

create a `.env` file using the `nano .env` command in the same directory as `docker-compose-server.yml` and add the following environmental parameters:

```env
CMF_DATA_DIR=./data                    
NGINX_HTTP_PORT=80                  
NGINX_HTTPS_PORT=443
REACT_APP_CMF_API_URL=http://your-server-ip:80
```

```bash
$ nano .env
```
**Output:** creates env file, add the above 3-4 lines and save it using (CTRL+O, ENTER, CTRL+X)

!!! warning "Production Note"
    * Avoid relative definitions for `CMF_DATA_DIR` in active production environments; define absolute system file paths to prevent accidental data loss.
    * Do not leave `REACT_APP_CMF_API_URL` set to a local loopback reference (`localhost` / `127.0.0.1`) if external client nodes need to transmit metadata over the local area network.

> 📝 **Note:** 
> - `CMF_DATA_DIR` controls where all data (PostgreSQL, TensorBoard logs, etc.) is stored. Use an absolute path for better control.
> - `REACT_APP_CMF_API_URL` should point to your server's accessible address.

---

**Step 4: Start the Containers**

> 💡 **Recommended Approach:** Using `docker compose` starts the `CMF Server`, PostgreSQL database, and `CMF UI` together.
> 
> **Note:** It's essential to start the PostgreSQL database before the `CMF Server`.

```bash
$ docker compose -f docker-compose-server.yml up
```
**Output:** It start your server, Visit to browser at `localshot / 127.0.0.1`

> 📝 **Note:** Replace `docker compose` with `docker-compose` if you're using an older version of Docker.

This command starts all services:

- **PostgreSQL**: Database backend for metadata storage
- **CMF Server**: API server for metadata management
- **UI**: Web interface for visualization
- **TensorBoard**: For viewing ML training metrics
- **Nginx**: Reverse proxy serving all components

#### Accessing the CMF UI

Once the containers are successfully started, the CMF UI will be available at the URL specified in your `.env` file:

```
http://your-server-ip:80
```

Replace `your-server-ip` with the actual IP address or hostname configured in the `REACT_APP_CMF_API_URL` environment variable.

> 📝 **Note:** Ensure that port 80 (or your configured `NGINX_HTTP_PORT`) is accessible and not blocked by firewall rules.

---

**Step 5: Stop the Containers**

```bash
$ docker compose -f docker-compose-server.yml stop
```

#### Important Notes

> 💡 **Rebuild Required:** 
> Rebuild the images for `CMF Server` and `CMF UI` after a CMF version update or pulling the latest changes from Git to ensure compatibility.
>
> ```bash
> docker compose -f docker-compose-server.yml build --no-cache
> docker compose -f docker-compose-server.yml up
> ```

---