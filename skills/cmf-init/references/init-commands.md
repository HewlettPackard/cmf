# CMF Init Command Reference

## Local storage
```bash
cmf init local \
  --path <dir> \
  --git-remote-url <url> \
  [--cmf-server-url <url>] \
  [--neo4j-user <user> --neo4j-password <pw> --neo4j-uri bolt://localhost:7687]
```

## MinIO (minios3)
```bash
cmf init minios3 \
  --url http://<host>:9000 \
  --endpoint-url http://<host>:9000 \
  --access-key-id <key> \
  --secret-access-key <secret> \
  --git-remote-url <url> \
  [--cmf-server-url <url>]
```

## Amazon S3 (amazons3)
```bash
cmf init amazons3 \
  --url s3://<bucket>/<path> \
  --access-key-id <key> \
  --secret-access-key <secret> \
  --git-remote-url <url> \
  [--cmf-server-url <url>]
```

## SSH remote (sshremote)
```bash
cmf init sshremote \
  --path ssh://user@host:/path/to/storage \
  --git-remote-url <url> \
  [--cmf-server-url <url>]
```

## OSDF remote (osdfremote)

### Option 1 — Pre-generated token
```bash
cmf init osdfremote \
  --path <origin-url> \
  --cache <cache-url> \
  --access-token <token-file-or-string> \
  --git-remote-url <url>
```

### Option 2 — Key-based dynamic token
```bash
cmf init osdfremote \
  --path <origin-url> \
  --cache <cache-url> \
  --key-id <id> \
  --key-path <pem-file> \
  --key-issuer <issuer-url> \
  --git-remote-url <url>
```

### Option 3 — Default token location
Place token at `~/.fdp/osdf_token`, then:
```bash
cmf init osdfremote \
  --path <origin-url> \
  --cache <cache-url> \
  --git-remote-url <url>
```

### OSDF parameters

| Parameter | Required | Purpose |
|-----------|----------|---------|
| `--path` | Yes | OSDF origin server URL (writes go here) |
| `--git-remote-url` | Yes | Git repository URL |
| `--cache` | No | OSDF cache/director URL — improves read performance |
| `--access-token` | No* | Pre-generated token file path or value |
| `--key-id` | No* | Key identifier for dynamic token generation |
| `--key-path` | No* | Private key file for dynamic token generation |
| `--key-issuer` | No* | Token issuer URL |

\* Provide `--access-token` OR all three `--key-*` params, or place token at `~/.fdp/osdf_token`.

## Verify
```bash
cmf init show
```
