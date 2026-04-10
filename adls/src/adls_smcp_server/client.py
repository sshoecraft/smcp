"""Azure Data Lake Storage Gen2 client wrapper."""

import base64
import logging
import json
from dataclasses import dataclass
from typing import List, Optional, Dict
from pathlib import Path

from datetime import datetime, timedelta, timezone

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.storage.filedatalake import DataLakeServiceClient

logger = logging.getLogger(__name__)


@dataclass
class ADLS2Config:
    """Configuration for Azure Data Lake Storage Gen2 client."""
    storage_account_name: str
    read_only: bool = False
    storage_account_key: Optional[str] = None

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "ADLS2Config":
        """Create config from SMCP credentials."""
        storage_account_name = creds.get("AZURE_STORAGE_ACCOUNT_NAME")
        if not storage_account_name:
            raise ValueError("AZURE_STORAGE_ACCOUNT_NAME credential is required")

        return cls(
            storage_account_name=storage_account_name,
            storage_account_key=creds.get("AZURE_STORAGE_ACCOUNT_KEY"),
            read_only=creds.get("READ_ONLY_MODE", "false").lower() == "true",
        )


class ADLS2Client:
    """Azure Data Lake Storage Gen2 client wrapper."""

    def __init__(self, config: ADLS2Config):
        """Initialize the ADLS2 client.

        Args:
            config: ADLS2Config instance with credentials
        """
        self._config = config
        self.client = self._create_client()
        self.blob_client = self._create_blob_client()
        self._read_only = config.read_only

    @property
    def read_only(self) -> bool:
        """Whether the client is in read-only mode."""
        return self._read_only

    @property
    def config(self) -> ADLS2Config:
        """The configuration for the client."""
        return self._config

    def _create_client(self) -> DataLakeServiceClient:
        """Create the DataLakeServiceClient."""
        account_url = f"https://{self._config.storage_account_name}.dfs.core.windows.net"
        if self._config.storage_account_key:
            credential = self._config.storage_account_key
        else:
            credential = DefaultAzureCredential()
        return DataLakeServiceClient(account_url=account_url, credential=credential)

    def _create_blob_client(self) -> BlobServiceClient:
        """Create the BlobServiceClient."""
        account_url = f"https://{self._config.storage_account_name}.blob.core.windows.net"
        if self._config.storage_account_key:
            credential = self._config.storage_account_key
        else:
            credential = DefaultAzureCredential()
        return BlobServiceClient(account_url=account_url, credential=credential)

    async def list_containers(self) -> List[str]:
        """List all blob containers in the storage account."""
        try:
            return [container.name for container in self.blob_client.list_containers()]
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []

    async def create_blob_container(self, name: str) -> bool:
        """Create a new blob container in the storage account."""
        try:
            self.blob_client.create_container(name)
            return True
        except Exception as e:
            logger.error(f"Error creating container {name}: {e}")
            return False

    async def delete_blob_container(self, name: str) -> bool:
        """Delete a blob container from the storage account."""
        try:
            self.blob_client.delete_container(name)
            return True
        except Exception as e:
            logger.error(f"Error deleting container {name}: {e}")
            return False

    async def list_blobs(self, container: str, prefix: str = "") -> List[Dict[str, str]]:
        """List blobs in a container, optionally filtered by prefix."""
        try:
            container_client = self.blob_client.get_container_client(container)
            blobs = []
            for blob in container_client.list_blobs(name_starts_with=prefix if prefix else None):
                blobs.append({
                    "name": blob.name,
                    "size": str(blob.size),
                    "last_modified": blob.last_modified.isoformat() if blob.last_modified else "",
                    "content_type": blob.content_settings.content_type if blob.content_settings else "",
                })
            return blobs
        except Exception as e:
            logger.error(f"Error listing blobs in {container}: {e}")
            return []

    async def get_blob_properties(self, container: str, blob_path: str) -> Optional[Dict[str, str]]:
        """Get properties of a blob."""
        try:
            blob_client = self.blob_client.get_blob_client(container, blob_path)
            props = blob_client.get_blob_properties()
            return {
                "name": blob_path,
                "size": str(props.size),
                "creation_time": props.creation_time.isoformat() if props.creation_time else "",
                "last_modified": props.last_modified.isoformat() if props.last_modified else "",
                "content_type": props.content_settings.content_type if props.content_settings else "",
                "etag": props.etag if props.etag else "",
                "blob_type": str(props.blob_type) if props.blob_type else "",
            }
        except Exception as e:
            logger.error(f"Error getting blob properties for {blob_path}: {e}")
            return None

    async def upload_blob(self, upload_file: str, container: str, destination: str) -> bool:
        """Upload a local file as a blob."""
        try:
            source_path = Path(upload_file)
            if not source_path.exists():
                logger.error(f"Source file does not exist: {source_path}")
                return False
            blob_client = self.blob_client.get_blob_client(container, destination)
            with open(source_path, "rb") as file:
                blob_client.upload_blob(file.read(), overwrite=True)
            return True
        except Exception as e:
            logger.error(f"Error uploading blob {upload_file} to {destination}: {e}")
            return False

    async def upload_blob_content(self, content: str, container: str, destination: str,
                                    encoding: str = "utf-8") -> None:
        """Upload text or base64 content directly as a blob.

        Args:
            content: The content to upload (text string or base64-encoded string)
            container: Target container name
            destination: Blob path in the container
            encoding: "utf-8" for text content, "base64" for binary content

        Raises:
            ValueError: If encoding is invalid
            Exception: On upload failure
        """
        if encoding == "base64":
            data = base64.b64decode(content)
        elif encoding == "utf-8":
            data = content.encode("utf-8")
        else:
            raise ValueError(f"Unsupported encoding: {encoding}. Use 'utf-8' or 'base64'.")

        blob_client = self.blob_client.get_blob_client(container, destination)
        blob_client.upload_blob(data, overwrite=True)

    async def download_blob(self, container: str, source: str, download_path: str) -> bool:
        """Download a blob to a local file."""
        try:
            dest_path = Path(download_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            blob_client = self.blob_client.get_blob_client(container, source)
            download = blob_client.download_blob()
            with open(dest_path, "wb") as file:
                file.write(download.readall())
            return True
        except Exception as e:
            logger.error(f"Error downloading blob {source} to {download_path}: {e}")
            return False

    async def delete_blob(self, container: str, blob_path: str) -> bool:
        """Delete a blob from a container."""
        try:
            blob_client = self.blob_client.get_blob_client(container, blob_path)
            blob_client.delete_blob()
            return True
        except Exception as e:
            logger.error(f"Error deleting blob {blob_path}: {e}")
            return False

    async def generate_sas_url(self, container: str, blob_path: str, expiry_minutes: int = 60,
                               permissions: str = "r") -> Optional[str]:
        """Generate a SAS URL for a blob.

        Args:
            container: Container name
            blob_path: Path to the blob
            expiry_minutes: Minutes until the SAS token expires
            permissions: Permission string (r=read, w=write, d=delete, l=list)

        Returns:
            Full SAS URL string, or None on failure
        """
        if not self._config.storage_account_key:
            logger.error("Storage account key is required to generate SAS URLs")
            return None

        try:
            start_time = datetime.now(timezone.utc)
            expiry_time = start_time + timedelta(minutes=expiry_minutes)

            sas_token = generate_blob_sas(
                account_name=self._config.storage_account_name,
                container_name=container,
                blob_name=blob_path,
                account_key=self._config.storage_account_key,
                permission=BlobSasPermissions(
                    read="r" in permissions,
                    write="w" in permissions,
                    delete="d" in permissions,
                    list="l" in permissions,
                ),
                start=start_time,
                expiry=expiry_time,
            )

            url = (
                f"https://{self._config.storage_account_name}.blob.core.windows.net"
                f"/{container}/{blob_path}?{sas_token}"
            )
            return url
        except Exception as e:
            logger.error(f"Error generating SAS URL for {container}/{blob_path}: {e}")
            return None

    async def create_container(self, container: str) -> bool:
        """Create a new container (filesystem) in the storage account."""
        try:
            _ = self.client.create_file_system(file_system=container)
            return True
        except Exception as e:
            logger.error(f"Error creating container {container}: {e}")
            return False

    async def list_filesystems(self) -> List[str]:
        """List all filesystems in the storage account."""
        try:
            return [container.name for container in self.client.list_file_systems()]
        except Exception as e:
            logger.error(f"Error listing filesystems: {e}")
            return []

    async def delete_filesystem(self, name: str) -> bool:
        """Delete a filesystem from the storage account."""
        try:
            file_system_client = self.client.get_file_system_client(name)
            file_system_client.delete_file_system()
            return True
        except Exception as e:
            logger.error(f"Error deleting filesystem {name}: {e}")
            return False

    async def create_directory(self, filesystem: str, directory: str) -> bool:
        """Create a new directory in the specified filesystem."""
        try:
            file_system_client = self.client.get_file_system_client(filesystem)
            file_system_client.create_directory(directory)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")
            return False

    async def delete_directory(self, filesystem: str, directory: str) -> bool:
        """Delete a directory from the specified filesystem."""
        try:
            file_system_client = self.client.get_file_system_client(filesystem)
            directory_client = file_system_client.get_directory_client(directory)
            directory_client.delete_directory()
            return True
        except Exception as e:
            logger.error(f"Error deleting directory {directory}: {e}")
            return False

    async def rename_directory(self, filesystem: str, source_path: str, destination_path: str) -> bool:
        """Rename/move a directory within the specified filesystem."""
        try:
            file_system_client = self.client.get_file_system_client(filesystem)
            directory_client = file_system_client.get_directory_client(source_path)
            new_name = f"{file_system_client.file_system_name}/{destination_path}"
            directory_client.rename_directory(new_name)
            return True
        except Exception as e:
            logger.error(f"Error renaming directory {source_path} to {destination_path}: {e}")
            return False

    async def directory_get_paths(self, filesystem: str, directory: str = "/", recursive: bool = True) -> List[str]:
        """Get files and directories under the specified path."""
        try:
            file_system_client = self.client.get_file_system_client(filesystem)
            directory_client = file_system_client.get_directory_client(directory)

            paths = []
            paths_iter = directory_client.get_paths(recursive=recursive)

            for path in paths_iter:
                paths.append(path.name)

            return paths
        except Exception as e:
            logger.error(f"Error getting paths for directory {directory}: {e}")
            return []

    async def upload_file(self, upload_file: str, filesystem: str, destination: str) -> bool:
        """Upload a file to ADLS2."""
        try:
            source_path = Path(upload_file)
            if not source_path.exists():
                logger.error(f"Source file does not exist: {source_path}")
                return False

            file_system_client = self.client.get_file_system_client(filesystem)
            file_client = file_system_client.get_file_client(destination)

            with open(source_path, "rb") as file:
                file_client.upload_data(file.read(), overwrite=True)

            return True
        except Exception as e:
            logger.error(f"Error uploading file {upload_file} to {destination}: {e}")
            return False

    async def download_file(self, filesystem: str, source: str, download_path: str) -> bool:
        """Download a file from ADLS2."""
        try:
            dest_path = Path(download_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            file_system_client = self.client.get_file_system_client(filesystem)
            file_client = file_system_client.get_file_client(source)

            download = file_client.download_file()
            with open(dest_path, "wb") as file:
                file.write(download.readall())

            return True
        except Exception as e:
            logger.error(f"Error downloading file {source} to {download_path}: {e}")
            return False

    async def file_exists(self, filesystem: str, file_path: str) -> bool:
        """Check if a file exists in the specified filesystem."""
        try:
            file_system_client = self.client.get_file_system_client(filesystem)
            file_client = file_system_client.get_file_client(file_path)
            file_client.get_file_properties()
            return True
        except Exception as e:
            logger.debug(f"File {file_path} does not exist in filesystem {filesystem}: {e}")
            return False

    async def rename_file(self, filesystem: str, source_path: str, destination_path: str) -> bool:
        """Rename/move a file within the specified filesystem."""
        try:
            file_system_client = self.client.get_file_system_client(filesystem)
            file_client = file_system_client.get_file_client(source_path)
            new_name = f"{file_system_client.file_system_name}/{destination_path}"
            file_client.rename_file(new_name)
            return True
        except Exception as e:
            logger.error(f"Error renaming file {source_path} to {destination_path}: {e}")
            return False

    async def get_file_properties(self, filesystem: str, file_path: str) -> Optional[Dict[str, str]]:
        """Get properties of a file in the specified filesystem."""
        try:
            file_system_client = self.client.get_file_system_client(filesystem)
            file_client = file_system_client.get_file_client(file_path)

            properties = file_client.get_file_properties()

            return {
                "name": file_path,
                "size": str(properties.size),
                "creation_time": properties.creation_time.isoformat() if properties.creation_time else "",
                "last_modified": properties.last_modified.isoformat() if properties.last_modified else "",
                "content_type": properties.content_settings.content_type if properties.content_settings else "",
                "etag": properties.etag if properties.etag else ""
            }
        except Exception as e:
            logger.error(f"Error getting properties for file {file_path}: {e}")
            return None

    async def get_file_metadata(self, filesystem: str, file_path: str) -> Optional[Dict[str, str]]:
        """Get metadata of a file in the specified filesystem."""
        try:
            file_system_client = self.client.get_file_system_client(filesystem)
            file_client = file_system_client.get_file_client(file_path)

            properties = file_client.get_file_properties()
            return dict(properties.metadata) if properties.metadata else {}
        except Exception as e:
            logger.error(f"Error getting metadata for file {file_path}: {e}")
            return None

    async def set_file_metadata(self, filesystem: str, file_path: str, key: str, value: str) -> bool:
        """Set a single metadata key-value pair for a file."""
        if self.read_only:
            return False

        try:
            file_system_client = self.client.get_file_system_client(filesystem)
            file_client = file_system_client.get_file_client(file_path)

            properties = file_client.get_file_properties()
            metadata = dict(properties.metadata) if properties.metadata else {}
            metadata[key] = value
            file_client.set_metadata(metadata)
            return True
        except Exception as e:
            logger.error(f"Error setting metadata for file {file_path}: {e}")
            return False

    async def set_file_metadata_json(self, filesystem: str, file_path: str, metadata_json: str) -> bool:
        """Set multiple metadata key-value pairs for a file using JSON."""
        if self.read_only:
            return False

        try:
            new_metadata = json.loads(metadata_json)
            if not isinstance(new_metadata, dict):
                logger.error("Metadata JSON must be an object")
                return False

            file_system_client = self.client.get_file_system_client(filesystem)
            file_client = file_system_client.get_file_client(file_path)

            properties = file_client.get_file_properties()
            metadata = dict(properties.metadata) if properties.metadata else {}
            metadata.update(new_metadata)
            file_client.set_metadata(metadata)
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format for metadata: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting metadata for file {file_path}: {e}")
            return False
