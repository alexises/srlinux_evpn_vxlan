"""Generate common info for routing protocol."""

from dataclasses import dataclass, field
from ipaddress import IPv4Address
from typing import Self

from pydantic_srlinux.models.network_instance import (
    EnumerationEnum,
    InstanceListEntry6,
    InterfaceListEntry,
    LinuxContainer,
    Model,
    NetworkInstanceListEntry,
    OspfContainer,
    ProtocolsContainer,
)


def _default_addr() -> IPv4Address:
    return IPv4Address("0.0.0.0")  # noqa: S104


@dataclass
class RoutingContainer:
    """Store info for routing protocol."""

    router_id: IPv4Address = field(default_factory=_default_addr)
    interfaces: list[str] = field(default_factory=list)
    area: IPv4Address = field(default_factory=_default_addr)

    def to_yamg(self: Self) -> Model:
        """Get yang model associated with this model.

        Args:
            self (Self): self

        Returns:
            Model: yang model.
        """
        interfaces = [InterfaceListEntry(name=i) for i in self.interfaces]

        return Model(
            network_instance=[
                NetworkInstanceListEntry(
                    name="default",
                    router_id=str(self.router_id),
                    interface=interfaces,
                ),
                NetworkInstanceListEntry(
                    name="mgmt",
                    admin_state=EnumerationEnum.enable,
                    type="ip-vrf",
                    description="Management network instance",
                    interface=[InterfaceListEntry(name="mgmt0.0")],
                    protocols=ProtocolsContainer(
                        linux=LinuxContainer(
                            import_routes=True,
                            export_routes=True,
                            export_neighbors=True,
                        ),
                        ospf=OspfContainer(
                            instance=[
                                InstanceListEntry6(
                                    name="EVPN-UNDERLAY",
                                    admin_state=EnumerationEnum.enable,
                                    router_id=str(self.router_id),
                                    version="ospf-v2",
                                    max_ecmp_paths=4,
                                    area=None,
                                ),
                            ],
                        ),
                    ),
                ),
            ],
        )
