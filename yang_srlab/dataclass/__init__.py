"""This module represent the mapping of cli configuration."""

from dataclasses import dataclass, field
from typing import Self

from .interface import InterfaceContainer
from .routing import RoutingContainer


@dataclass
class SwitchContainer:
    """Define the whole switch configuration AST."""

    system_id: str = ""
    ssh_keys: list[str] = field(default_factory=list)

    def __post_init__(self: Self) -> None:
        """Constructor.

        Args:
            self (Self): self.
        """
        self._interfaces = InterfaceContainer(20)
        self._routing = RoutingContainer()

    @property
    def interfaces(self: Self) -> InterfaceContainer:
        """Get interface container.

        Args:
            self (Self): self
        Returns:
            InterfaceContainer: interface container
        """
        return self._interfaces

    @property
    def router(self: Self) -> RoutingContainer:
        """Get routing container.

        Args:
            self (Self): self

        Returns:
            RoutingContainer: routing container
        """
        return self._routing
