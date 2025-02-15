"""This module represent the mapping of cli configuration."""

from typing import Self

from .interface import InterfaceContainer


class SwitchContainer:
    """Define the whole switch configuration AST."""

    def __init__(self: Self) -> None:
        """Constructor.

        Args:
            self (Self): self.
        """
        self._interfaces = InterfaceContainer(20)

    @property
    def interfaces(self: Self) -> InterfaceContainer:
        """Get interface container.

        Args:
            self (Self): self
        Returns:
            InterfaceContainer: interface container
        """
        return self._interfaces

    def to_yang(self: Self) -> dict:
        """Get yang model.

        Args:
            self (Self): self.

        Returns:
            dict: yang model.
        """
        output = self._interfaces.to_yang()
        return output.model_dump(
            mode="json",
            exclude_none=True,
            exclude_unset=True,
            by_alias=True,
        )
