"""Make conputation to transform meta model into Yang represantation."""

from typing import Self

from .dataclass.interface import InterfaceContainer
from .metamodel import Metamodel, Switch


class YangController:
    """Define yang controller that in charge of generating the corresponding yang config."""

    def __init__(self: Self, model: Metamodel) -> None:
        """Constructor.

        Args:
            self (Self): self
            model (Metamodel): base metamodel.
        """
        self._model: Metamodel = model

    def compute_all(self: Self, allowed_switch: list[str]) -> list[tuple[Switch, dict]]:
        """Generate yang for all site and switchs.

        Args:
            self (Self): self
            allowed_switch (list[str]): list of allowed switch, empty list will run on all switchs.

        Return:
            list[tuple[Switch, dict]]: computed config.
        """
        computed_switch = []
        for site in self._model.fabrics:
            for leaf in site.lifs:
                if leaf.name not in allowed_switch and allowed_switch != []:
                    continue
                computed_switch.append((leaf, self.compute_leaf(leaf)))
        return computed_switch

    def compute_leaf(self: Self, switch: Switch) -> dict:
        """Compute configuration for leaf.

        Args:
            self (Self): Self.
            switch (Switch): switch object to compute.
        """
        ifaces = InterfaceContainer(20)
        ifaces.shutdown_all_interface()

        return ifaces.to_yang().model_dump(
            mode="json",
            exclude_none=True,
            exclude_unset=True,
            by_alias=True,
        )
