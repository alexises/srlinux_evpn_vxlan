"""Define yang access."""

from datetime import UTC, datetime
from typing import Self

from requests import Session


class SRClient:
    """Define srclient."""

    def __init__(self: Self, host: str, username: str, password: str) -> None:
        """Constructor.

        Args:
            self (Self): self
            host (str): host
            username (str): username
            password (str): password
        """
        self._url = f"http://{host}/jsonrpc"
        self._client = Session()
        self._client.auth = (username, password)

    def diff(self: Self, path: str, data: dict) -> dict:
        """Get diff from command and path.

        Args:
            self (Self): self
            path (str): path to where performing the diff
            data (dict): data to compare
        """
        query = {
            "jsonrpc": "2.0",
            "id": datetime.now(tz=UTC).isoformat(),
            "method": "diff",
            "params": {"commands": [{"action": "replace", "path": path, "value": data}]},
        }
        response = self._client.post(self._url, json=query)
        return response.json()

    def validate(self: Self, path: str, data: dict) -> dict:
        """Validate from command and path.

        Args:
            self (Self): self
            path (str): path to where performing the diff
            data (dict): data to compare
        """
        query = {
            "jsonrpc": "2.0",
            "id": datetime.now(tz=UTC).isoformat(),
            "method": "validate",
            "params": {"commands": [{"action": "replace", "path": path, "value": data}]},
        }
        response = self._client.post(self._url, json=query)
        return response.json()

    def commit(self: Self, path: str, data: dict) -> dict:
        """Commit from command and path.

        Args:
            self (Self): self
            path (str): path to where performing the diff
            data (dict): data to compare
        """
        query = {
            "jsonrpc": "2.0",
            "id": datetime.now(tz=UTC).isoformat(),
            "method": "set",
            "params": {"commands": [{"action": "replace", "path": path, "value": data}]},
        }
        response = self._client.post(self._url, json=query)
        return response.json()

    def get_running_config(self: Self) -> dict:
        """Get running config.

        Args:
            self (Self): self

        Returns:
            dict: running_config
        """
        query = {
            "jsonrpc": "2.0",
            "id": datetime.now(tz=UTC).isoformat(),
            "method": "get",
            "params": {"commands": [{"path": "/", "datastore": "running"}]},
        }
        response = self._client.post(self._url, json=query)
        return response.json()["result"][0]
