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
    VxlanInterfaceListEntry,
)
from pydantic_srlinux.models.tunnel_interfaces import (
    IngressContainer,
    TunnelInterfaceListEntry,
)
from pydantic_srlinux.models.tunnel_interfaces import Model as TunnelModel
from pydantic_srlinux.models.tunnel_interfaces import (
    VxlanInterfaceListEntry as TunnelVxlanInterfaceListEntry,
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
    clients: dict[str, int] = field(default_factory=dict)
    vlans: dict[str, int] = field(default_factory=dict)

    def _get_l2_tunnel(self: Self) -> list[TunnelVxlanInterfaceListEntry]:
        vxlan_interface: list[TunnelVxlanInterfaceListEntry] = []
        for vlan_id in self.vlans.values():
            iface = TunnelVxlanInterfaceListEntry(
                index=vlan_id,
                type="bridged",
                ingress=IngressContainer(vni=vlan_id),
            )
            vxlan_interface.append(iface)
        return vxlan_interface

    def _get_l3_tunnel(self: Self) -> list[TunnelVxlanInterfaceListEntry]:
        vxlan_intefaces: list[TunnelVxlanInterfaceListEntry] = []
        for client_id in self.clients.values():
            iface = TunnelVxlanInterfaceListEntry(
                index=client_id + 10000,
                type="routed",
                ingress=IngressContainer(vni=client_id + 10000),
            )
            vxlan_intefaces.append(iface)
        return vxlan_intefaces

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

    def _get_clients_vrf(self: Self) -> list[NetworkInstanceListEntry]:
        vrfs = []
        for client_name, client_id in self.clients.items():
            vrf = NetworkInstanceListEntry(
                name=f"CLIENT_{client_name.upper()}",
                admin_state=EnumerationEnum.enable,
                type="ip-vrf",
                interface=[],
                vxlan_interface=[
                    VxlanInterfaceListEntry(name=f"vxlan1.{client_id+10000}"),
                ],
            )
            vrfs.append(vrf)
        return vrfs

    def _get_layer2_vrf(self: Self) -> list[NetworkInstanceListEntry]:
        vrfs = []
        for vlan_name, vlan_id in self.vlans.items():
            vrf = NetworkInstanceListEntry(
                name=f"VLAN_{vlan_name.upper()}",
                admin_state=EnumerationEnum.enable,
                type="mac-vrf",
                interface=[InterfaceListEntry(name=f"irb0.{vlan_id}")],
                vxlan_interface=[
                    VxlanInterfaceListEntry(name=f"vxlan1.{vlan_id}"),
                ],
            )
            vrfs.append(vrf)
        return vrfs

    def _get_default_vrf(self: Self) -> list[NetworkInstanceListEntry]:
        interfaces = [InterfaceListEntry(name=i) for i in self.interfaces]
        return [
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
        ]

    def to_yang_tunnel(self: Self) -> TunnelModel:
        """Get yang tunnel model.

        Args:
            self (Self): self.

        Returns:
            TunnelModel: tunnel model
        """
        l3tunnel = self._get_l3_tunnel()
        l2tunnel = self._get_l2_tunnel()
        return TunnelModel(
            tunnel_interface=[
                TunnelInterfaceListEntry(name="vxlan1", vxlan_interface=l3tunnel + l2tunnel),
            ],
        )

    def to_yamg(self: Self) -> Model:
        """Get yang model associated with this model.

        Args:
            self (Self): self

        Returns:
            Model: yang model.
        """
        default_vrfs = self._get_default_vrf()
        clients = self._get_clients_vrf()
        l2 = self._get_layer2_vrf()

        vrfs = default_vrfs + clients + l2
        return Model(
            network_instance=vrfs,
        )
