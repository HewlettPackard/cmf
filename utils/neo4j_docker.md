#### Pre requisite 
Docker should be installed.

#### Command to start neo4j docker container
```
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
The docker run command creates and starts a container. On the next line, --name testneo4j defines the name we want to use for the container as testneo4j.
Using the -p option with ports 7474 and 7687 allows us to expose and listen for traffic on both the HTTP and Bolt ports. Having the HTTP port means we can connect to our database with Neo4j Browser, and the Bolt port means efficient and type-safe communication requests between other layers and the database.

Next, we have -d. This detaches the container to run in the background, meaning we can access the container separately and see into all of its processes.
The next several lines start with the -v option. These lines define volumes we want to bind in our local directory structure so we can access certain files locally.

The first one is for our /data directory, which stores the system information and graph data.

The second -v option is for the /logs directory. Outputting the Neo4j logs to a place outside the container ensures we can troubleshoot any errors in Neo4j, even if the container crashes.

The third line with the -v option binds the import directory, so we can copy CSV or other flat files into that directory for importing into Neo4j. Load scripts for importing that data can also be placed in this folder for us to execute.

The next -v option line sets up our plugins directory.
On the next line with the --env parameter, we initiate our Neo4j instance with a username and password. Neo4j automatically sets up basic authentication with the neo4j username as a foundation for security. Since it will initiate authentication and require a password change when first connecting, we can handle all of that in this parameter.

Finally, the last line of the command above references the Docker image we want to pull from DockerHub (neo4j), as well as any specified version (in this case, just the latest edition).
<br>

[More details](https://neo4j.com/developer/docker-run-neo4j/)

#### Some useful Neo4j cypher queries
To access neo4j from browser, open http://IP:7474/

Queries
<br> Replace "pipelinename" with your pipeline name

1. Artifact Lineage with processing steps (all artifact types)

```
MATCH (a:Execution{pipeline_name:'<pipelinename>'})-[r]-(b) WHERE (b:Dataset or b:Model or b:Metrics or b:Step_Metrics or b:Environment or b:Dataslice) RETURN a,r, b 
```

2. Artifact Lineage with processing steps and Labels

```
MATCH (a:Execution{pipeline_name:'<pipelinename>'})-[r]-(b) WHERE (b:Dataset or b:Model or b:Metrics or b:Step_Metrics or b:Environment) OPTIONAL MATCH (b)-[r2:has_label]->(label:Label) RETURN a, r, b, label, r2
```

3. All Artifacts with their relationships (including Label connections to Datasets)

```
MATCH (b) where (b:Dataset or b:Model or b:Metrics or b:Step_Metrics or b:Environment or b:Dataslice or b:Label) and '<pipelinename>' in b.pipeline_name OPTIONAL MATCH (b)-[r]-(c:Label) RETURN b, r, c
```

4. Dataset Lineage with Labels and Dataslices

```
MATCH (d:Dataset) WHERE '<pipelinename>' in d.pipeline_name OPTIONAL MATCH (d)-[r1:has_label]->(l:Label) OPTIONAL MATCH (d)-[r2:contains]->(ds:Dataslice) RETURN d, r1, l, r2, ds
```

5. Lineage of processing steps (Execution nodes only)

```
MATCH (n:Execution{pipeline_name:'<pipelinename>'}) return n
```

6. Step Metrics associated with specific execution

```
MATCH (e:Execution{pipeline_name:'<pipelinename>'})-[r]->(m:Step_Metrics) RETURN e, r, m
```

7. Environment artifacts for a pipeline

```
MATCH (env:Environment) WHERE '<pipelinename>' in env.pipeline_name RETURN env
```

8. clean up <br>
> All execution/stage/pipeline nodes related to a pipeline

 ```
 MATCH (n{pipeline_name:'<pipelinename>'}) detach delete n
 ```
  
  > All artifact nodes (Dataset, Model, Metrics, Step_Metrics, Environment, Dataslice, Label)
 
  ```
  MATCH (n) where '<pipelinename>' in n.pipeline_name detach delete n
  ```



