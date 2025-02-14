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
