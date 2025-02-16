"""Generate common info for routing protocol."""

from dataclasses import dataclass, field
from ipaddress import IPv4Address
from typing import Self

from pydantic_srlinux.models.network_instance import (
    AfiSafiListEntry,
    AreaListEntry,
    BgpContainer,
    DottedQuadType,
    EnumerationEnum,
    EnumerationEnum223,
    EvpnContainer,
    GroupListEntry,
    InstanceListEntry6,
    InterfaceListEntry,
    InterfaceListEntry11,
    Ipv4AddressType,
    Ipv4AddressWithZoneType,
    LinuxContainer,
    Model,
    NeighborListEntry,
    NetworkInstanceListEntry,
    OspfContainer,
    ProtocolsContainer,
    RouteReflectorContainer2,
    TransportContainer3,
)


def _default_addr() -> IPv4Address:
    return IPv4Address("0.0.0.0")  # noqa: S104


@dataclass
class RoutingContainer:
    """Store info for routing protocol."""

    router_id: IPv4Address = field(default_factory=_default_addr)
    interfaces: list[str] = field(default_factory=list)
    area: IPv4Address = field(default_factory=_default_addr)
    asn: int = field(default=0)
    rr: bool = field(default=False)
    evpn_peers: dict[str, IPv4Address] = field(default_factory=dict)

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

    def _get_bgp(self: Self) -> BgpContainer:
        rr_config = RouteReflectorContainer2(
            client=True,
            cluster_id=DottedQuadType(str(self.area)),
        )
        neighs = [
            NeighborListEntry(
                peer_address=Ipv4AddressWithZoneType(str(peer_ip)),
                description=f"SPINE {peer_name}",
                peer_group="EVPN_OVERLAY",
                transport=TransportContainer3(local_address=Ipv4AddressType(str(self.router_id))),
            )
            for peer_name, peer_ip in self.evpn_peers.items()
        ]
        return BgpContainer(
            admin_state=EnumerationEnum.enable,
            router_id=Ipv4AddressType(str(self.router_id)),
            autonomous_system=self.asn,
            afi_safi=[
                AfiSafiListEntry(
                    afi_safi_name="evpn",
                    admin_state=EnumerationEnum.enable,
                    evpn=EvpnContainer(),
                ),
            ],
            group=[
                GroupListEntry(
                    group_name="EVPN_OVERLAY",
                    description="EVPN overlay",
                    next_hop_self=True,
                    peer_as=self.asn,
                    route_reflector=rr_config if self.rr else None,
                ),
            ],
            neighbor=neighs,
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
                        bgp=self._get_bgp(),
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
