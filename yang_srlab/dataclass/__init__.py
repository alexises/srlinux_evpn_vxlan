"""This module represent the mapping of cli configuration."""

from typing import Self

from .interface import InterfaceContainer
from .routing import RoutingContainer


class SwitchContainer:
    """Define the whole switch configuration AST."""

    def __init__(self: Self) -> None:
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

    def to_yang(self: Self) -> dict:
        """Get yang model.

        Args:
            self (Self): self.

        Returns:
            dict: yang model.
        """
        interface = self._interfaces.to_yang()
        router = self._routing.to_yamg()
        tunnel = self._routing.to_yang_tunnel()

        return {
            **interface.model_dump(
                mode="json",
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
            **router.model_dump(mode="json", exclude_none=True, exclude_unset=True, by_alias=True),
            **tunnel.model_dump(mode="json", exclude_none=True, exclude_unset=True, by_alias=True),
        }
