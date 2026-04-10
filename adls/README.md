# ADLS2 SMCP Server

An MCP server for Azure Data Lake Storage Gen2 with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Overview

This server provides access to Azure Data Lake Storage Gen2 via the Model Context Protocol (MCP). Unlike traditional MCP servers that receive credentials via environment variables or config files, this server uses SMCP for secure credential injection at startup.

## Features

- **Secure Credentials**: Receives Azure credentials via SMCP handshake (no env vars, no config files, no disk)
- **Blob Container Operations**: List, create, delete blob containers
- **Blob Operations**: List, upload, download, delete blobs; get blob properties
- **SAS URL Generation**: Generate time-limited, permission-scoped SAS URLs for blob download/access
- **Filesystem Operations**: List, create, delete ADLS2 filesystems
- **Directory Operations**: Create, delete, rename, list directories
- **File Operations**: Upload, download, rename files; get/set properties and metadata
- **Read-Only Mode**: Optional read-only mode for safe browsing

## SMCP Credentials

The server accepts the following credentials via SMCP JSON:

| Credential | Required | Description |
|------------|----------|-------------|
| `AZURE_STORAGE_ACCOUNT_NAME` | Yes | Azure storage account name |
| `AZURE_STORAGE_ACCOUNT_KEY` | No | Storage account key (uses DefaultAzureCredential if not provided) |
| `READ_ONLY_MODE` | No | Set to "true" to disable write operations (default: "false") |
| `LOG_LEVEL` | No | Logging level: DEBUG, INFO, WARNING, ERROR (default: "INFO") |

## Quick Start with Shepherd

```bash
shepherd smcp add adls --command "adls-smcp-server" --credential "AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount" --credential "AZURE_STORAGE_ACCOUNT_KEY=base64key..."
```

## Usage

```bash
adls-smcp-server
```

The server performs the SMCP handshake on startup:

```
← +READY
→ {"AZURE_STORAGE_ACCOUNT_NAME":"mystorageaccount","AZURE_STORAGE_ACCOUNT_KEY":"secret","READ_ONLY_MODE":"true"}
← +OK
→ {"jsonrpc":"2.0","method":"initialize",...}
(MCP JSON-RPC continues)
```

## MCP Tools

### Blob Container Tools

- **list_containers**: List all blob containers in the storage account
- **create_container**: Create a new blob container
- **delete_container**: Delete a blob container

### Blob Tools

- **list_blobs**: List blobs in a container, optionally filtered by prefix
- **get_blob_properties**: Get blob properties (size, timestamps, content type, etc.)
- **upload_blob**: Upload a local file as a blob
- **upload_blob_content**: Upload text or base64 content directly as a blob (no local file needed)
- **download_blob**: Download a blob
- **delete_blob**: Delete a blob

### SAS URL Tools

- **generate_sas_url**: Generate a time-limited SAS URL for a blob (parameters: container, blob_path, expiry_minutes, permissions)

### Filesystem Tools

- **list_filesystems**: List all filesystems in the storage account
- **create_filesystem**: Create a new filesystem (container)
- **delete_filesystem**: Delete a filesystem

### Directory Tools

- **create_directory**: Create a new directory
- **delete_directory**: Delete a directory
- **rename_directory**: Rename/move a directory
- **directory_get_paths**: List all paths under a directory

### File Tools

- **upload_file**: Upload a file to ADLS2
- **download_file**: Download a file from ADLS2
- **file_exists**: Check if a file exists
- **rename_file**: Rename/move a file
- **get_file_properties**: Get file properties (size, timestamps, etc.)
- **get_file_metadata**: Get file metadata
- **set_file_metadata**: Set a single metadata key-value pair
- **set_file_metadata_json**: Set multiple metadata key-value pairs

## Building

```bash
pip install -e ../lib  # Install shared smcp library
pip install -e .
```

## Example Parent Process (SMCP Launcher)

```python
import subprocess
import json

child = subprocess.Popen(
    ["adls-smcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Wait for +READY
assert child.stdout.readline().strip() == "+READY"

# Send credentials as JSON
creds = {
    "AZURE_STORAGE_ACCOUNT_NAME": "mystorageaccount",
    "AZURE_STORAGE_ACCOUNT_KEY": "mysecretkey",
    "READ_ONLY_MODE": "true"
}
child.stdin.write(json.dumps(creds) + "\n")
child.stdin.flush()

# Wait for +OK
assert child.stdout.readline().strip() == "+OK"

# MCP JSON-RPC begins on stdin/stdout
```

## Security

- Credentials exist only in process memory
- No environment variables exposed in `/proc/<pid>/environ`
- No config files written to disk
- Parent process controls credential distribution
- Uses Azure DefaultAzureCredential for flexible authentication

## License

MIT
