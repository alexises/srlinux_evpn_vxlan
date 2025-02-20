"""Define compute container."""

from typing import TYPE_CHECKING, Self

from yang_srlab.dataclass import SwitchContainer
from yang_srlab.metamodel import Switch

if TYPE_CHECKING:
    from collections.abc import Callable


class ComputeContainer:
    """Define compute container."""

    def __init__(self: Self, groups: list[str], switch: Switch) -> None:
        """Constructor.

        Args:
            self (Self): self
            groups (list[str]): list of template groups
            switch (Switch): switch to manage.
        """
        from .template_scanner import get_func_from_group

        self._switch = switch
        self._container = SwitchContainer()
        self._callbacks: list[Callable[[ComputeContainer], None]] = []
        for group in groups:
            self._callbacks += get_func_from_group(group)

    def run(self: Self) -> None:
        """Run templating callback stack against switch.

        Args:
            self (Self): self.
        """
        for callback in self._callbacks:
            callback(self)

    @property
    def switch(self: Self) -> Switch:
        """Get switch.

        Args:
            self (Self): self

        Returns:
            Switch: switch obj
        """
        return self._switch

    @property
    def container(self: Self) -> SwitchContainer:
        """Get container obj.

        Args:
            self (Self): self

        Returns:
            SwitchContainer: container obj
        """
        return self._container
