"""Define srlinux storage class."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

from pydantic_srlinux.models.interfaces import InterfaceListEntry
from pydantic_srlinux.models.interfaces import Model as InterfacesModel
from pydantic_srlinux.models.network_instance import Model as NEModel
from pydantic_srlinux.models.network_instance import NetworkInstanceListEntry
from pydantic_srlinux.models.routing_policy import Model as RPModel
from pydantic_srlinux.models.tunnel_interfaces import Model as TunnelModel

from .interface import YangInterafece
from .templates import TemplateGroup

if TYPE_CHECKING:
    from collections.abc import Callable

srlinux_templates: TemplateGroup[SRLinuxYang] = TemplateGroup()


def srlinux_template(func: Callable[[SRLinuxYang], None]) -> Callable[[SRLinuxYang], None]:
    """Decorator for SRLinuxYang templating functions."""
    return srlinux_templates.register(func)


@dataclass
class SRLinuxYang(YangInterafece):
    """Define SRLinuxYang Model."""

    vrfs: NEModel = field(default_factory=NEModel)
    tunnel: TunnelModel = field(default_factory=TunnelModel)
    interfaces: InterfacesModel = field(default_factory=InterfacesModel)
    routing_policy: RPModel = field(default_factory=RPModel)
    vrfs_objs: dict[str, NetworkInstanceListEntry] = field(default_factory=dict)
    interfaces_objs: dict[str, InterfaceListEntry] = field(default_factory=dict)

    def __post_init__(self: Self) -> None:
        """Set kind."""
        self.kind = "srlinux"

    def run(self: Self) -> None:
        """Run all methods against object.

        Args:
            self (Self): self
        """
        srlinux_templates.run(self)

    def to_yang(self: Self) -> dict:
        """Convert internal model into yang.

        Args:
            self (Self): self

        Returns:
            dict: converted yang model
        """
        return {
            **self.vrfs.model_dump(
                mode="json",
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
            **self.tunnel.model_dump(
                mode="json",
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
            **self.interfaces.model_dump(
                mode="json",
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
            **self.routing_policy.model_dump(
                mode="json",
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
        }
