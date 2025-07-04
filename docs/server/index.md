# CMF Server

The CMF Server provides centralized metadata storage, artifact management, and web-based visualization capabilities for distributed ML teams. Built on FastAPI, it offers REST APIs for metadata synchronization and a React-based web interface for exploring pipeline lineage.

## FastAPI Server and APIs

The CMF server is built using FastAPI and provides comprehensive REST APIs for metadata and artifact management.

### Server Architecture

```mermaid
graph TB
    subgraph "CMF Server Components"
        FASTAPI["FastAPI Application<br/>Port 8080"]
        METADATA_API["Metadata APIs<br/>/mlmd_push, /mlmd_pull"]
        ARTIFACT_API["Artifact APIs<br/>/artifact_push, /artifact_pull"]
        QUERY_API["Query APIs<br/>/executions, /artifacts"]
        LINEAGE_API["Lineage APIs<br/>/lineage, /display_lineage"]
    end
    
    subgraph "Storage Layer"
        POSTGRES[("PostgreSQL<br/>Metadata Storage")]
        ARTIFACT_STORE[("Artifact Storage<br/>S3/MinIO/SSH")]
        NEO4J[("Neo4j<br/>Graph Database")]
    end
    
    subgraph "External Services"
        TENSORBOARD["TensorBoard<br/>Port 6006"]
        JUPYTER["Jupyter Integration"]
    end
    
    FASTAPI --> METADATA_API
    FASTAPI --> ARTIFACT_API
    FASTAPI --> QUERY_API
    FASTAPI --> LINEAGE_API
    
    METADATA_API --> POSTGRES
    ARTIFACT_API --> ARTIFACT_STORE
    QUERY_API --> POSTGRES
    LINEAGE_API --> NEO4J
    
    FASTAPI --> TENSORBOARD
    FASTAPI --> JUPYTER
```

### Core API Endpoints

| Endpoint | Method | Purpose | Parameters |
|----------|--------|---------|------------|
| `/mlmd_push` | POST | Upload metadata to server | `pipeline_name`, `execution_id` |
| `/mlmd_pull/{pipeline_name}` | GET | Download metadata from server | `pipeline_name` |
| `/artifact_push` | POST | Upload artifacts to storage | `pipeline_name`, `artifact_name` |
| `/artifact_pull` | GET | Download artifacts from storage | `pipeline_name`, `artifact_name` |
| `/executions` | GET | List pipeline executions | `pipeline_name`, `limit` |
| `/artifacts` | GET | List pipeline artifacts | `pipeline_name`, `type` |
| `/lineage/{artifact_id}` | GET | Get artifact lineage | `artifact_id` |
| `/display_lineage` | GET | Lineage visualization data | `pipeline_name` |

### API Usage Examples

```bash
# Push metadata to server
curl -X POST "http://cmf-server:8080/mlmd_push" \
  -H "Content-Type: application/json" \
  -d '{"pipeline_name": "mnist_pipeline", "execution_id": "123"}'

# Pull metadata from server
curl "http://cmf-server:8080/mlmd_pull/mnist_pipeline"

# Get executions for a pipeline
curl "http://cmf-server:8080/executions?pipeline_name=mnist_pipeline&limit=10"

# Get lineage for an artifact
curl "http://cmf-server:8080/lineage/456"
```

## Lineage Query System

The lineage query system provides powerful capabilities for exploring ML pipeline relationships and dependencies.

### Graph-Based Lineage

CMF uses Neo4j to store and query complex pipeline relationships:

```mermaid
graph LR
    subgraph "Pipeline Lineage"
        DATA1["Raw Dataset<br/>train_data.csv"]
        EXEC1["Data Processing<br/>preprocess_execution"]
        DATA2["Processed Dataset<br/>clean_data.csv"]
        EXEC2["Model Training<br/>train_execution"]
        MODEL1["Trained Model<br/>model.pkl"]
        EXEC3["Model Evaluation<br/>eval_execution"]
        METRICS1["Evaluation Metrics<br/>accuracy: 0.95"]
    end
    
    DATA1 --> EXEC1
    EXEC1 --> DATA2
    DATA2 --> EXEC2
    EXEC2 --> MODEL1
    MODEL1 --> EXEC3
    EXEC3 --> METRICS1
```

### Query Capabilities

The lineage system supports various query patterns:

#### Upstream Lineage
Find all inputs that contributed to a specific artifact:

```python
from cmflib import cmfquery

query = cmfquery.CmfQuery(mlmd_path="postgresql://user:pass@server/mlmd")
upstream = query.get_upstream_artifacts_by_artifact_name("trained_model.pkl")
```

#### Downstream Lineage
Find all artifacts that depend on a specific input:

```python
downstream = query.get_downstream_artifacts_by_artifact_name("raw_data.csv")
```

#### Execution History
Get complete execution history for a pipeline:

```python
executions = query.get_all_executions_in_pipeline("mnist_pipeline")
```

### Lineage Visualization

The server provides D3.js-based interactive lineage visualization:

- **Interactive graphs**: Pan, zoom, and click to explore
- **Multi-level views**: Pipeline, stage, and artifact levels
- **Filtering**: Filter by artifact type, execution status, time range
- **Export**: Export lineage graphs as SVG or PNG

## Server Deployment

CMF Server supports multiple deployment patterns from development to production environments.

### Docker Compose Deployment

The recommended deployment uses Docker Compose with the following services:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: mlmd
      POSTGRES_USER: cmf_user
      POSTGRES_PASSWORD: cmf_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  cmf-server:
    image: cmf-server:latest
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://cmf_user:cmf_password@postgres:5432/mlmd
      NEO4J_URI: bolt://neo4j:7687
    depends_on:
      - postgres
      - neo4j

  neo4j:
    image: neo4j:5.26
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/password

  ui-server:
    image: cmf-ui:latest
    ports:
      - "3000:3000"
    environment:
      REACT_APP_CMF_SERVER_URL: http://cmf-server:8080
    depends_on:
      - cmf-server

  tensorboard:
    image: tensorflow/tensorflow:latest
    ports:
      - "6006:6006"
    command: tensorboard --logdir=/logs --host=0.0.0.0
    volumes:
      - tensorboard_logs:/logs
```

### Environment Configuration

Key environment variables for server configuration:

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/mlmd` |
| `NEO4J_URI` | Neo4j connection URI | `bolt://neo4j:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `password` |
| `ARTIFACT_STORAGE_TYPE` | Storage backend type | `s3`, `minio`, `local` |
| `S3_ENDPOINT_URL` | S3-compatible endpoint | `http://minio:9000` |
| `S3_ACCESS_KEY_ID` | S3 access key | `minioadmin` |
| `S3_SECRET_ACCESS_KEY` | S3 secret key | `minioadmin` |

### Health Checks and Monitoring

The server includes comprehensive health checks:

```bash
# Server health check
curl http://cmf-server:8080/health

# Database connectivity check
curl http://cmf-server:8080/health/database

# Neo4j connectivity check
curl http://cmf-server:8080/health/neo4j

# Storage backend check
curl http://cmf-server:8080/health/storage
```

### Scaling Considerations

For production deployments:

1. **Database**: Use managed PostgreSQL with read replicas
2. **Storage**: Use cloud storage (S3, GCS, Azure Blob) with CDN
3. **Caching**: Implement Redis for query result caching
4. **Load Balancing**: Use multiple server instances behind a load balancer
5. **Monitoring**: Implement comprehensive logging and metrics collection

### Security Configuration

Production security recommendations:

```yaml
# Use secrets management
secrets:
  db_password:
    external: true
  neo4j_password:
    external: true

# Enable TLS
services:
  cmf-server:
    environment:
      TLS_CERT_PATH: /certs/server.crt
      TLS_KEY_PATH: /certs/server.key
    volumes:
      - ./certs:/certs:ro
```

### Backup and Recovery

Implement regular backups:

```bash
# Database backup
pg_dump postgresql://user:pass@host:5432/mlmd > backup.sql

# Neo4j backup
neo4j-admin backup --backup-dir=/backups --name=graph.db

# Artifact storage backup (S3)
aws s3 sync s3://cmf-artifacts s3://cmf-artifacts-backup
```
