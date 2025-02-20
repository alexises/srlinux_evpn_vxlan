"""Make conputation to transform meta model into Yang represantation."""

from collections.abc import Sequence
from typing import Self

from yang_srlab.metamodel import Metamodel, Switch

from .container import ComputeContainer


class YangController:
    """Define yang controller that in charge of generating the corresponding yang config."""

    def __init__(self: Self, model: Metamodel) -> None:
        """Constructor.

        Args:
            self (Self): self
            model (Metamodel): base metamodel.
        """
        self._model: Metamodel = model

    def _compute_switches(
        self,
        switches: Sequence[Switch],
        allowed_switch: list[str],
        switch_category: str,
    ) -> list[tuple[Switch, dict]]:
        """Compute configuration for a list of switches based on their category.

        Args:
            switches (Sequence[Switch]): list of switches (e.g., leafs or spines).
            allowed_switch (list[str]): list of allowed switch names; if empty, all are allowed.
            switch_category (str): type/category of the switch ("leaf" or "spine").

        Returns:
            list[tuple[Switch, dict]]: computed configuration for the switches.
        """
        computed = []
        for switch in switches:
            # Only compute for allowed switches (if the allowed_switch list is not empty)
            if allowed_switch and switch.name not in allowed_switch:
                continue
            container = ComputeContainer(["common", switch_category], switch)
            container.run()
            computed.append((switch, container.container.to_yang()))
        return computed

    def compute_all(self, allowed_switch: list[str]) -> list[tuple[Switch, dict]]:
        """Generate yang configuration for all sites and switches.

        Args:
            allowed_switch (list[str]): list of allowed switch names; empty list means all switches.

        Returns:
            list[tuple[Switch, dict]]: computed configurations.
        """
        computed_switches = []
        for site in self._model.fabrics:
            computed_switches += self._compute_switches(site.lifs, allowed_switch, "leaf")
            computed_switches += self._compute_switches(site.spines, allowed_switch, "spine")
        return computed_switches
