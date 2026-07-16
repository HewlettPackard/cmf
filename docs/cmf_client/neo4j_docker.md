# Start Neo4j with Docker

## 🛠️ Prerequisite  
Docker should be installed.


## 🚀 Command to Start Neo4j Docker Container

```bash
docker run     --name testneo4j \
        -p7474:7474 -p7687:7687  \
        -d   \
        -v $HOME/neo4j/data:/data  \
        -v $HOME/neo4j/logs:/logs     \
        -v $HOME/neo4j/import:/var/lib/neo4j/import   \
        -v $HOME/neo4j/plugins:/plugins   \
        --env NEO4J_AUTH=neo4j/test1234    \
        neo4j:latest
```

The `docker run` command creates and starts a container.
On the next line, `--name testneo4j` defines the name we want to use for the container as `testneo4j`.

Using the `-p` option with ports `7474` and `7687` allows us to expose and listen for traffic on both the **HTTP** and **Bolt** ports.
Having the HTTP port means we can connect to our database with Neo4j Browser, and the Bolt port means efficient and type-safe communication requests between other layers and the database.

Next, we have `-d`. This detaches the container to run in the background, meaning we can access the container separately and see into all of its processes.

The next several lines start with the `-v` option. These lines define **volumes** we want to bind in our local directory structure so we can access certain files locally.

* The first one is for our `/data` directory, which stores the system information and graph data.
* The second `-v` option is for the `/logs` directory. Outputting the Neo4j logs to a place outside the container ensures we can troubleshoot any errors in Neo4j, even if the container crashes.
* The third line with the `-v` option binds the import directory, so we can copy CSV or other flat files into that directory for importing into Neo4j. Load scripts for importing that data can also be placed in this folder for us to execute.
* The next `-v` option line sets up our plugins directory.

On the next line with the `--env` parameter, we initiate our Neo4j instance with a username and password. Neo4j automatically sets up basic authentication with the `neo4j` username as a foundation for security. Since it will initiate authentication and require a password change when first connecting, we can handle all of that in this parameter.

Finally, the last line of the command above references the Docker image we want to pull from DockerHub (`neo4j`), as well as any specified version (in this case, just the latest edition).

🔗 [More details](https://neo4j.com/developer/docker-run-neo4j/)

---

To access Neo4j from browser, open:
➡️ **[http://IP:7474/](http://IP:7474/)**
> Replace `IP` with your system IP address.

---

## 🧪 Some Useful Neo4j Cypher Queries
> Replace `<pipelinename>` with your actual pipeline name.

---

### 1. Artifact Lineage with Processing Steps

```cypher
MATCH (a:Execution{pipeline_name:'<pipelinename>'})-[r]-(b) 
WHERE (b:Dataset or b:Model or b:Metrics) 
RETURN a, r, b 
```

---

### 2. Artifact Lineage

```cypher
MATCH (b) 
WHERE (b:Dataset or b:Model or b:Metrics) 
AND '<pipelinename>' IN b.pipeline_name 
RETURN b
```

---

### 3. Lineage of Processing Steps

```cypher
MATCH (n:Execution{pipeline_name:'<pipelinename>'}) 
RETURN n
```

---

### 4. Clean Up

> All execution/stage nodes related to a pipeline

```cypher
MATCH (n {pipeline_name:'<pipelinename>'}) 
DETACH DELETE n
```

> All Dataset nodes

```cypher
MATCH (n) 
WHERE '<pipelinename>' IN n.pipeline_name 
DETACH DELETE n
```

