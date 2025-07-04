# Development and Deployment

This section covers the development environment setup, deployment strategies, and documentation system for CMF. Whether you're contributing to CMF development or deploying it in production, this guide provides comprehensive information for all deployment scenarios.

## Development Environment

CMF provides a containerized development environment using Docker Compose that includes all necessary components for development and testing.

### Quick Start Development Setup

```bash
# Clone the repository
git clone https://github.com/HewlettPackard/cmf.git
cd cmf

# Create required directories
mkdir $HOME/workspace
mkdir $HOME/dvc_remote

# Create environment configuration
cat > .env << EOF
# AWS Configuration (optional)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
DVC_REMOTE_URL=s3://your-bucket/path

# Git Configuration
GIT_USER_NAME=your_name
GIT_USER_EMAIL=your_email@example.com
GIT_REMOTE_URL=git@github.com:your_username/cmf.git

# Neo4j Configuration
NEO4J_USER_NAME=neo4j
NEO4J_PASSWD=password
EOF

# Start development environment
docker-compose up
```

### Development Environment Architecture

```mermaid
graph TB
    subgraph "Host System"
        workspace["$HOME/workspace<br/>Local workspace directory"]
        dvc_remote["$HOME/dvc_remote<br/>DVC storage directory"]
        ssh_keys["$HOME/.ssh<br/>SSH keys"]
        env_file[".env<br/>Environment configuration"]
    end
    
    subgraph "Docker Compose Services"
        jupyter["jupyter-cmf-notebook<br/>Container: jupyter-cmf-notebook<br/>Port: 8888"]
        neo4j_service["neo4j<br/>Container: neo4j<br/>Ports: 7475, 7688"]
    end
    
    subgraph "External Services"
        aws_s3["AWS S3<br/>DVC Remote Storage"]
        git_remote["Git Remote Repository"]
        external_storage["SSH/MinIO Storage"]
    end
    
    workspace --> jupyter
    dvc_remote --> jupyter
    ssh_keys --> jupyter
    env_file --> jupyter
    env_file --> neo4j_service
    
    jupyter --> aws_s3
    jupyter --> git_remote
    jupyter --> external_storage
    jupyter --> neo4j_service
```

### Container Components

#### Jupyter CMF Notebook

The primary development container includes:

- **Base Image**: `jupyter/tensorflow-notebook`
- **CMF Installation**: Built from source with all dependencies
- **Port**: 8888 (Jupyter Lab interface)
- **Token**: `docker` (for development access)
- **Examples**: Pre-loaded example notebooks

#### Neo4j Database

Graph database for lineage visualization:

- **Image**: `neo4j:5.26`
- **Ports**: 7474 (HTTP), 7687 (Bolt)
- **Authentication**: Configured via environment variables
- **Data**: Persistent storage for graph data

### Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `$HOME/workspace` | `/home/jovyan/workspace` | Development workspace |
| `$HOME/dvc_remote` | `/home/jovyan/dvc_remote` | DVC storage directory |
| `$HOME/.ssh` | `/home/jovyan/.ssh` | SSH keys for Git/remote access |

### Environment Variables

Key configuration variables:

```bash
# Development Environment Variables
JUPYTER_TOKEN=docker                    # Jupyter access token
DOCKER_STACKS_JUPYTER_CMD=lab          # Use Jupyter Lab
NEO4J_URI=bolt://neo4j:7687            # Neo4j connection
NEO4J=TRUE                             # Enable Neo4j integration

# User Configuration
NB_USER=$USER                          # Match host user
NB_UID=$UID                           # Match host UID
NB_GID=$GID                           # Match host GID
GRANT_SUDO=yes                        # Enable sudo access
```

### Accessing the Development Environment

1. **Jupyter Lab**: http://localhost:8888 (token: `docker`)
2. **Neo4j Browser**: http://localhost:7475 (user: `neo4j`, password: from env)
3. **Example Notebooks**: Available in `/home/jovyan/example-get-started`

## Production Deployment

CMF supports multiple production deployment patterns from single-server setups to distributed enterprise deployments.

### Docker Compose Production Deployment

#### Complete Production Stack

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:13
    container_name: cmf-postgres
    environment:
      POSTGRES_DB: mlmd
      POSTGRES_USER: cmf_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -d mlmd -U cmf_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # CMF Server
  cmf-server:
    image: cmf-server:latest
    container_name: cmf-server
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://cmf_user:${POSTGRES_PASSWORD}@postgres:5432/mlmd
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: ${NEO4J_PASSWORD}
      S3_ENDPOINT_URL: ${S3_ENDPOINT_URL}
      S3_ACCESS_KEY_ID: ${S3_ACCESS_KEY_ID}
      S3_SECRET_ACCESS_KEY: ${S3_SECRET_ACCESS_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      neo4j:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 15s
      timeout: 10s
      retries: 32

  # Neo4j Graph Database
  neo4j:
    image: neo4j:5.26
    container_name: cmf-neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs

  # Web UI
  ui-server:
    image: cmf-ui:latest
    container_name: cmf-ui
    ports:
      - "3000:3000"
    environment:
      REACT_APP_CMF_SERVER_URL: http://${HOST_IP}:8080
      REACT_APP_CMF_SERVER_HOST: ${HOST_IP}
    depends_on:
      cmf-server:
        condition: service_healthy

  # TensorBoard
  tensorboard:
    image: tensorflow/tensorflow:latest
    container_name: cmf-tensorboard
    ports:
      - "6006:6006"
    command: tensorboard --logdir=/logs --host=0.0.0.0 --port=6006
    volumes:
      - tensorboard_logs:/logs

volumes:
  postgres_data:
  neo4j_data:
  neo4j_logs:
  tensorboard_logs:
```

#### Environment Configuration

Create a `.env` file for production:

```bash
# Database Configuration
POSTGRES_PASSWORD=secure_postgres_password
NEO4J_PASSWORD=secure_neo4j_password

# Server Configuration
HOST_IP=your.server.ip.address
HOSTNAME=your.server.hostname

# Storage Configuration
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY_ID=your_access_key
S3_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=cmf-production-artifacts

# Security Configuration
JWT_SECRET_KEY=your_jwt_secret_key
ENCRYPTION_KEY=your_encryption_key
```

### Kubernetes Deployment

For enterprise-scale deployments, CMF can be deployed on Kubernetes:

```yaml
# cmf-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cmf-production

---
# cmf-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cmf-config
  namespace: cmf-production
data:
  DATABASE_URL: "postgresql://cmf_user:password@postgres:5432/mlmd"
  NEO4J_URI: "bolt://neo4j:7687"
  S3_ENDPOINT_URL: "https://s3.amazonaws.com"

---
# cmf-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cmf-server
  namespace: cmf-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cmf-server
  template:
    metadata:
      labels:
        app: cmf-server
    spec:
      containers:
      - name: cmf-server
        image: cmf-server:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: cmf-config
        - secretRef:
            name: cmf-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"

---
# cmf-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: cmf-server-service
  namespace: cmf-production
spec:
  selector:
    app: cmf-server
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: LoadBalancer
```

### Scaling Considerations

#### Database Scaling

- **Read Replicas**: Use PostgreSQL read replicas for query workloads
- **Connection Pooling**: Implement PgBouncer for connection management
- **Partitioning**: Partition large tables by pipeline or date

#### Application Scaling

- **Horizontal Scaling**: Deploy multiple CMF server instances
- **Load Balancing**: Use NGINX or cloud load balancers
- **Caching**: Implement Redis for query result caching

#### Storage Scaling

- **Object Storage**: Use cloud storage (S3, GCS, Azure Blob)
- **CDN**: Implement CDN for artifact distribution
- **Backup Strategy**: Automated backups with retention policies

### Monitoring and Observability

#### Health Checks

```bash
# Server health
curl http://cmf-server:8080/health

# Database connectivity
curl http://cmf-server:8080/health/database

# Storage backend
curl http://cmf-server:8080/health/storage
```

#### Metrics Collection

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cmf-server'
    static_configs:
      - targets: ['cmf-server:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

#### Logging Configuration

```yaml
# logging-config.yaml
version: 1
formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
  file:
    class: logging.FileHandler
    filename: /logs/cmf-server.log
    level: DEBUG
    formatter: default
root:
  level: INFO
  handlers: [console, file]
```

## Documentation System

CMF uses MKDocs with the Material theme for documentation generation and deployment.

### Local Documentation Development

```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build --theme material --site-dir ../site/
```

### Documentation Structure

```
docs/
├── index.md                    # Main overview page
├── getting-started/            # Getting started guides
├── cmflib/                     # Core library documentation
├── server/                     # Server documentation
├── ui/                         # Web UI documentation
├── development/                # Development guides
├── assets/                     # Images and diagrams
├── requirements.txt            # Documentation dependencies
└── extra.css                   # Custom styling
```

### Automated Deployment

Documentation is automatically deployed to GitHub Pages via GitHub Actions:

```yaml
# .github/workflows/deploy_docs_to_gh_pages.yaml
name: Deploy Documentation
on:
  push:
    branches: [master]
    paths:
      - 'docs/**'
      - 'cmflib/cmf.py'
      - '.github/workflows/deploy_docs_to_gh_pages.yaml'

jobs:
  deploy-docs:
    runs-on: ubuntu-latest
    if: github.repository_owner == 'HewlettPackard'
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v3
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r docs/requirements.txt
      - name: Build documentation
        run: mkdocs build --theme material --site-dir ../site/
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3.9.0
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ../site
```

### Documentation Best Practices

1. **Use Mermaid diagrams** for architecture and flow visualization
2. **Include code examples** with proper syntax highlighting
3. **Cross-reference sections** using internal links
4. **Keep content modular** with focused, single-purpose pages
5. **Test locally** before committing changes
6. **Use consistent formatting** and follow style guidelines
