"""Define srlinux storage class."""

from dataclasses import field
from typing import Self

from pydantic_srlinux.models.interfaces import Model as InterfacesModel
from pydantic_srlinux.models.network_instance import Model as NEModel
from pydantic_srlinux.models.tunnel_interfaces import Model as TunnelModel

from .interface import YangInterafece


class SRLinuxYang(YangInterafece):
    """Define SRLinuxYang Model."""

    vrfs: NEModel = field(default_factory=NEModel)
    tunnel: TunnelModel = field(default_factory=TunnelModel)
    interfaces: InterfacesModel = field(default_factory=InterfacesModel)

    def __post_init__(self: Self) -> None:
        """Set kind."""
        self.kind = "srlinux"

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
        }
