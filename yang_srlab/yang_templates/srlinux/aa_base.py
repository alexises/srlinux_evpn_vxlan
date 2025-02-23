"""Base config."""

from typing import cast

import pydantic_srlinux.models.interfaces as mif
import pydantic_srlinux.models.tunnel_interfaces as tun
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
    NeighborListEntry,
    NetworkInstanceListEntry,
    OspfContainer,
    ProtocolsContainer,
    RouteReflectorContainer2,
    TransportContainer3,
)

from yang_srlab.yang_model.srlinux import SRLinuxYang, srlinux_template

DEFAULT_MTU = 1500


@srlinux_template
def prepare(model: SRLinuxYang) -> None:
    """Prepare model for other usages."""
    model.tunnel.tunnel_interface = [tun.TunnelInterfaceListEntry(name="vxlan1")]
    model.tunnel.tunnel_interface[0].vxlan_interface = []
    model.interfaces.interface = []


@srlinux_template
def base_vrfs(model: SRLinuxYang) -> None:
    """Set base configuration.

    Args:
        model (SRLinuxYang): model
    """
    interfaces = [InterfaceListEntry(name=i) for i in model.sw.router.interfaces]
    model.vrfs.network_instance = []
    model.vrfs_objs["default"] = NetworkInstanceListEntry(
        name="default",
        router_id=str(model.sw.router.router_id),
        interface=interfaces,
        protocols=ProtocolsContainer(),
    )

    model.vrfs_objs["mgmt"] = NetworkInstanceListEntry(
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
    )


@srlinux_template
def underlay(model: SRLinuxYang) -> None:
    """Deploy OSPF underlay.

    Args:
        model (SRLinuxYang): model.
    """
    iface = [
        InterfaceListEntry11(
            interface_name=i,
            interface_type=EnumerationEnum223.point_to_point,
        )
        for i in model.sw.router.interfaces
    ]

    protocols = cast(ProtocolsContainer, model.vrfs_objs["default"].protocols)
    protocols.ospf = OspfContainer(
        instance=[
            InstanceListEntry6(
                name="EVPN-UNDERLAY",
                admin_state=EnumerationEnum.enable,
                router_id=str(model.sw.router.router_id),
                version="ospf-v2",
                max_ecmp_paths=4,
                area=[
                    AreaListEntry(area_id=str(model.sw.router.area), interface=iface),
                ],
            ),
        ],
    )


@srlinux_template
def overlay(model: SRLinuxYang) -> None:
    """Deploy BGP EVPN overlay.

    Args:
        model (SRLinuxYang): model
    """
    rr_config = RouteReflectorContainer2(
        client=True,
        cluster_id=DottedQuadType(str(model.sw.router.area)),
    )
    neighs = [
        NeighborListEntry(
            peer_address=Ipv4AddressWithZoneType(str(peer_ip)),
            description=f"SPINE {peer_name}",
            peer_group="EVPN_OVERLAY",
            transport=TransportContainer3(
                local_address=Ipv4AddressType(str(model.sw.router.router_id)),
            ),
        )
        for peer_name, peer_ip in model.sw.router.evpn_peers.items()
    ]
    protocols = cast(ProtocolsContainer, model.vrfs_objs["default"].protocols)
    protocols.bgp = BgpContainer(
        admin_state=EnumerationEnum.enable,
        router_id=Ipv4AddressType(str(model.sw.router.router_id)),
        autonomous_system=model.sw.router.asn,
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
                peer_as=model.sw.router.asn,
                route_reflector=rr_config if model.sw.router.rr else None,
            ),
        ],
        neighbor=neighs,
    )


@srlinux_template
def management_interface(model: SRLinuxYang) -> None:
    """Configure management interface."""
    mgmt_iface = mif.InterfaceListEntry(
        name="mgmt0",
        admin_state=mif.EnumerationEnum.enable,
        subinterface=[
            mif.SubinterfaceListEntry(
                index=0,
                admin_state=mif.EnumerationEnum.enable,
                ipv4=mif.Ipv4Container(
                    admin_state=mif.EnumerationEnum.enable,
                    dhcp_client=mif.DhcpClientContainer(),
                ),
                ipv6=mif.Ipv6Container(
                    admin_state=mif.EnumerationEnum.enable,
                    dhcp_client=mif.DhcpClientContainer2(),
                ),
            ),
        ],
    )

    model.interfaces_objs["mgmt0"] = mgmt_iface


@srlinux_template
def base_interfaces(mode: SRLinuxYang) -> None:
    """Create basics interfaces."""
    for interface_name, interface in mode.sw.interfaces.interfaces.items():
        iface_obj = mif.InterfaceListEntry(
            name=interface_name,
            vlan_tagging=(True if "ethernet-" in interface_name else None),
            description=interface.description if interface.description else None,
            admin_state=(
                mif.EnumerationEnum.enable if interface.admin_state else mif.EnumerationEnum.disable
            ),
            subinterface=[],
            mtu=interface.mtu if interface.mtu != DEFAULT_MTU else None,
        )
        mode.interfaces_objs[interface_name] = iface_obj
