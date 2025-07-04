# Documentation System

## Purpose and Scope

The CMF documentation system provides automated building and deployment of project documentation using MKDocs. This system handles the generation of API documentation, deployment to GitHub Pages, and local development workflows for documentation contributors.

## MKDocs-Based Documentation

CMF uses [MKDocs](https://www.mkdocs.org/) as its primary documentation framework with the Material theme. The documentation system automatically generates API documentation and maintains a comprehensive wiki-style documentation site.

### Documentation Architecture

```mermaid
graph TB
    subgraph "Source Files"
        DOCS_DIR["docs/"]
        README["docs/README.md"]
        REQUIREMENTS["docs/requirements.txt"]
        CONFIG["mkdocs.yml"]
    end
    
    subgraph "Build Process"
        MKDOCS["mkdocs build"]
        MATERIAL_THEME["--theme material"]
        SITE_DIR["--site-dir ../site/"]
    end
    
    subgraph "Generated Output"
        SITE["../site/"]
        API_DOCS["Auto-generated API docs"]
        STATIC_ASSETS["Static assets"]
    end
    
    subgraph "Deployment Target"
        GH_PAGES["gh-pages branch"]
        GITHUB_PAGES["GitHub Pages"]
    end
    
    DOCS_DIR --> MKDOCS
    REQUIREMENTS --> MKDOCS
    CONFIG --> MKDOCS
    MKDOCS --> MATERIAL_THEME
    MATERIAL_THEME --> SITE_DIR
    SITE_DIR --> SITE
    SITE --> API_DOCS
    SITE --> STATIC_ASSETS
    SITE --> GH_PAGES
    GH_PAGES --> GITHUB_PAGES
```

## Local Development Workflow

Developers can build and serve documentation locally using the following process:

### Prerequisites and Commands

| Command | Purpose |
|---------|---------|
| `pip install -r docs/requirements.txt` | Install documentation dependencies |
| `mkdocs serve` | Start local development server |

### Local Build Process

```mermaid
graph LR
    subgraph "Developer Environment"
        DEV["Developer"]
        INSTALL["pip install -r docs/requirements.txt"]
        SERVE["mkdocs serve"]
    end
    
    subgraph "MKDocs Process"
        HTTP_SERVER["HTTP Server"]
        LIVE_RELOAD["Live Reload"]
        LOCAL_BUILD["Local Build"]
    end
    
    subgraph "Output"
        BROWSER["Browser localhost:8000"]
        PREVIEW["Documentation Preview"]
    end
    
    DEV --> INSTALL
    INSTALL --> SERVE
    SERVE --> HTTP_SERVER
    HTTP_SERVER --> LIVE_RELOAD
    HTTP_SERVER --> LOCAL_BUILD
    LOCAL_BUILD --> BROWSER
    BROWSER --> PREVIEW
```

## GitHub Actions Deployment Pipeline

The documentation system uses GitHub Actions for automated deployment to GitHub Pages through the workflow defined in `.github/workflows/deploy_docs_to_gh_pages.yaml`.

### Deployment Workflow

```mermaid
graph TB
    subgraph "Trigger Conditions"
        PUSH["Push to master"]
        WORKFLOW_CHANGE["deploy_docs_to_gh_pages.yaml"]
        DOCS_CHANGE["docs/**"]
        API_CHANGE["cmflib/cmf.py"]
    end
    
    subgraph "GitHub Actions Jobs"
        JOB["deploy-docs-to-gh-pages"]
        CHECKOUT["actions/checkout@v3"]
        PYTHON_SETUP["actions/setup-python@v3"]
        DEPS_INSTALL["pip install -r docs/requirements.txt"]
        BUILD["mkdocs build --theme material --site-dir ../site/"]
        CLEANUP["rm -r ../site/_src"]
        DEPLOY["peaceiris/actions-gh-pages@v3.9.0"]
    end
    
    subgraph "Deployment Target"
        GH_PAGES_BRANCH["gh-pages branch"]
        PAGES_SITE["GitHub Pages Site"]
    end
    
    PUSH --> JOB
    WORKFLOW_CHANGE --> JOB
    DOCS_CHANGE --> JOB
    API_CHANGE --> JOB
    
    JOB --> CHECKOUT
    CHECKOUT --> PYTHON_SETUP
    PYTHON_SETUP --> DEPS_INSTALL
    DEPS_INSTALL --> BUILD
    BUILD --> CLEANUP
    CLEANUP --> DEPLOY
    DEPLOY --> GH_PAGES_BRANCH
    GH_PAGES_BRANCH --> PAGES_SITE
```

### Workflow Configuration Details

The deployment workflow includes specific configuration parameters:

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `python-version` | `'3.10'` | Python environment version |
| `working-directory` | `'./'` | Build execution directory |
| `site-dir` | `../site/` | Output directory for built docs |
| `publish_dir` | `../site` | Directory published to GitHub Pages |
| `github_token` | `${{ secrets.GITHUB_TOKEN }}` | Authentication for deployment |

### Build Trigger Paths

The workflow is triggered by changes to these specific paths:

- `.github/workflows/deploy_docs_to_gh_pages.yaml` - The workflow file itself
- `docs/**` - Documentation source files (excluding `docs/_src/**`)
- `cmflib/cmf.py` - Public API documentation source

## Repository Access Control

The deployment workflow includes security measures to prevent execution on forked repositories:

```yaml
if: github.repository_owner == 'HewlettPackard'
```

This condition ensures the workflow only runs on the official HPE repository, preventing unauthorized deployments from forks.

## File Cleanup Process

The build process includes automatic cleanup of raw documentation assets:

```bash
rm -r ../site/_src
```

This removes the `_src` directory containing raw files that are not needed for the deployed documentation site, optimizing the final deployment size.

## Best Practices

### Documentation Writing

1. **Use Mermaid diagrams** for architectural and flow diagrams
2. **Include code examples** with proper syntax highlighting
3. **Cross-reference sections** using internal links
4. **Keep content modular** with focused, single-purpose pages

### File Organization

1. **Group related content** in subdirectories
2. **Use descriptive filenames** that match navigation structure
3. **Include assets** in the `assets/` directory
4. **Maintain consistent** markdown formatting

### Development Workflow

1. **Test locally** before committing changes
2. **Use live reload** during development with `mkdocs serve`
3. **Check build logs** in GitHub Actions for deployment issues
4. **Review generated site** after deployment
