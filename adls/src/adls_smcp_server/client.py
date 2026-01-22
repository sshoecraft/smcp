"""Azure Data Lake Storage Gen2 client wrapper."""

import logging
import json
from dataclasses import dataclass
from typing import List, Optional, Dict
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

logger = logging.getLogger(__name__)


@dataclass
class ADLS2Config:
    """Configuration for Azure Data Lake Storage Gen2 client."""
    storage_account_name: str
    read_only: bool = True
    storage_account_key: Optional[str] = None
    upload_root: str = "./uploads"
    download_root: str = "./downloads"

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "ADLS2Config":
        """Create config from SMCP credentials."""
        storage_account_name = creds.get("AZURE_STORAGE_ACCOUNT_NAME")
        if not storage_account_name:
            raise ValueError("AZURE_STORAGE_ACCOUNT_NAME credential is required")

        return cls(
            storage_account_name=storage_account_name,
            storage_account_key=creds.get("AZURE_STORAGE_ACCOUNT_KEY"),
            read_only=creds.get("READ_ONLY_MODE", "true").lower() == "true",
            upload_root=creds.get("UPLOAD_ROOT", "./uploads"),
            download_root=creds.get("DOWNLOAD_ROOT", "./downloads"),
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
        self._read_only = config.read_only
        self.upload_root = config.upload_root
        self.download_root = config.download_root

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
        credential = DefaultAzureCredential()
        return DataLakeServiceClient(account_url=account_url, credential=credential)

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
            source_path = Path(self.upload_root) / upload_file

            if not source_path.exists():
                logger.error(f"Source file does not exist: {source_path}")
                return False

            if not str(source_path.absolute()).startswith(str(Path(self.upload_root).absolute())):
                logger.error(f"Source file must be within UPLOAD_ROOT: {self.upload_root}")
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
            dest_path = Path(self.download_root) / download_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            if not str(dest_path.absolute()).startswith(str(Path(self.download_root).absolute())):
                logger.error(f"Destination path must be within DOWNLOAD_ROOT: {self.download_root}")
                return False

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
