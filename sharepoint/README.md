# SharePoint SMCP Server

An MCP server for SharePoint via Microsoft Graph API with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Overview

This server provides access to SharePoint Online via the Model Context Protocol (MCP) using Microsoft Graph REST API. Unlike traditional MCP servers that receive credentials via environment variables or config files, this server uses SMCP for secure credential injection at startup.

## Features

- **Secure Credentials**: Receives Azure AD credentials via SMCP handshake (no env vars, no config files, no disk)
- **Site Discovery**: List, search, and get SharePoint sites
- **Document Libraries**: List and inspect drives (document libraries)
- **File & Folder Operations**: List, upload, download, create, delete, move, copy, and search files/folders
- **SharePoint Lists**: List, create, update, and delete list items with field values
- **Permissions & Sharing**: List permissions, create sharing links, remove permissions
- **Read-Only Mode**: Optional read-only mode for safe browsing

## SMCP Credentials

The server accepts the following credentials via SMCP JSON:

| Credential | Required | Description |
|------------|----------|-------------|
| `TENANT_ID` | Yes | Azure AD tenant ID |
| `CLIENT_ID` | Yes | Azure AD application (client) ID |
| `CLIENT_SECRET` | Yes | Azure AD application client secret |
| `SITE_URL` | No | SharePoint site URL to scope operations (e.g. `https://contoso.sharepoint.com/sites/TeamSite`) |
| `READ_ONLY_MODE` | No | Set to "true" to disable write operations (default: "false") |
| `LOG_LEVEL` | No | Logging level: DEBUG, INFO, WARNING, ERROR (default: "INFO") |

### Azure AD App Registration

To use this server, you need an Azure AD app registration with Microsoft Graph API permissions:

- **Sites.Read.All** — for read-only access
- **Sites.ReadWrite.All** — for read-write access
- **Files.ReadWrite.All** — for file operations across all sites

Grant admin consent for these permissions in the Azure portal.

## Quick Start with Shepherd

```bash
shepherd smcp add sharepoint --command "sharepoint-smcp-server" --credential "TENANT_ID=your-tenant-id" --credential "CLIENT_ID=your-client-id" --credential "CLIENT_SECRET=your-secret" --credential "SITE_URL=https://contoso.sharepoint.com/sites/TeamSite"
```

## Usage

```bash
sharepoint-smcp-server
```

The server performs the SMCP handshake on startup:

```
← +READY
→ {"TENANT_ID":"...","CLIENT_ID":"...","CLIENT_SECRET":"...","SITE_URL":"https://contoso.sharepoint.com/sites/TeamSite","READ_ONLY_MODE":"true"}
← +OK
→ {"jsonrpc":"2.0","method":"initialize",...}
(MCP JSON-RPC continues)
```

## MCP Tools

### Site Tools

- **list_sites**: List all SharePoint sites accessible to the application
- **search_sites**: Search for sites by keyword
- **get_site**: Get details of a specific site by ID
- **get_site_by_url**: Get a site by its URL

### Drive Tools

- **list_drives**: List document libraries (drives) in a site
- **get_drive**: Get details of a specific drive

### File & Folder Tools

- **list_children**: List files and folders at a path in a document library
- **get_item**: Get properties of a file or folder
- **search_items**: Search for files within a document library
- **download_item_content**: Download file content as text or base64
- **upload_item_content**: Upload text or base64 content as a file (max 4MB)
- **create_folder**: Create a new folder
- **delete_item**: Delete a file or folder
- **move_item**: Move and/or rename a file or folder
- **copy_item**: Copy a file or folder

### List Tools

- **list_lists**: List SharePoint lists in a site
- **get_list**: Get details of a specific list
- **list_list_items**: Get items from a list with field values
- **get_list_item**: Get a specific list item
- **create_list_item**: Create a new item in a list
- **update_list_item**: Update fields of a list item
- **delete_list_item**: Delete an item from a list

### Permission Tools

- **list_permissions**: List permissions on a file or folder
- **create_sharing_link**: Create a sharing link (view/edit, anonymous/organization/users)
- **delete_permission**: Remove a permission from a file or folder

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
    ["sharepoint-smcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Wait for +READY
assert child.stdout.readline().strip() == "+READY"

# Send credentials as JSON
creds = {
    "TENANT_ID": "your-tenant-id",
    "CLIENT_ID": "your-client-id",
    "CLIENT_SECRET": "your-secret",
    "SITE_URL": "https://contoso.sharepoint.com/sites/TeamSite",
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
- Uses Azure AD client credentials flow via `azure-identity`

## License

MIT
