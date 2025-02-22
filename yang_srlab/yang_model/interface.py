"""Define interface for vendor neutral yang manipulation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Self

from yang_srlab.dataclass import SwitchContainer
from yang_srlab.yang_model.templates import get_yang_func_from_group


@dataclass
class YangInterafece(ABC):
    """Yang interface."""

    sw: SwitchContainer
    kind: str = ""

    @abstractmethod
    def to_yang(self: Self) -> dict:
        """Get dict representation from yang object.

        Args:
            self (self): self

        Returns:
            dict: yang representation
        """

    @abstractmethod
    def run(self: Self) -> None:
        """Run job.

        Args:
            self (Self): self.
        """
        for callback in get_yang_func_from_group(self.kind):
            callback(self)
