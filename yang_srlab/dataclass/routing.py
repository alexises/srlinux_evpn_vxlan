"""Generate common info for routing protocol."""

from dataclasses import dataclass, field
from ipaddress import IPv4Address
from typing import Self

from pydantic_srlinux.models.network_instance import (
    AreaListEntry,
    EnumerationEnum,
    EnumerationEnum223,
    InstanceListEntry6,
    InterfaceListEntry,
    InterfaceListEntry11,
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

    def _get_ospf(self: Self) -> OspfContainer:
        iface = [
            InterfaceListEntry11(
                interface_name=i,
                interface_type=EnumerationEnum223.point_to_point,
            )
            for i in self.interfaces
        ]

        return OspfContainer(
            instance=[
                InstanceListEntry6(
                    name="EVPN-UNDERLAY",
                    admin_state=EnumerationEnum.enable,
                    router_id=str(self.router_id),
                    version="ospf-v2",
                    max_ecmp_paths=4,
                    area=[
                        AreaListEntry(area_id=str(self.area), interface=iface),
                    ],
                ),
            ],
        )

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
                    protocols=ProtocolsContainer(
                        ospf=self._get_ospf(),
                    ),
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
                    ),
                ),
            ],
        )
