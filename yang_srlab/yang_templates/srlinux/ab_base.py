"""Base config."""

from typing import cast

import pydantic_srlinux.models.interfaces as mif
import pydantic_srlinux.models.network_instance as ni
import pydantic_srlinux.models.routing_policy as rp
import pydantic_srlinux.models.tunnel_interfaces as tun

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
    interfaces = [ni.InterfaceListEntry(name=i) for i in model.sw.router.interfaces]
    model.vrfs.network_instance = []
    model.vrfs_objs["default"] = ni.NetworkInstanceListEntry(
        name="default",
        router_id=str(model.sw.router.router_id),
        interface=interfaces,
        protocols=ni.ProtocolsContainer(),
    )

    model.vrfs_objs["mgmt"] = ni.NetworkInstanceListEntry(
        name="mgmt",
        admin_state=ni.EnumerationEnum.enable,
        type="ip-vrf",
        description="Management network instance",
        interface=[ni.InterfaceListEntry(name="mgmt0.0")],
        protocols=ni.ProtocolsContainer(
            linux=ni.LinuxContainer(
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
        ni.InterfaceListEntry11(
            interface_name=i,
            interface_type=ni.EnumerationEnum223.point_to_point,
        )
        for i in model.sw.router.interfaces
    ]

    protocols = cast(ni.ProtocolsContainer, model.vrfs_objs["default"].protocols)
    protocols.ospf = ni.OspfContainer(
        instance=[
            ni.InstanceListEntry6(
                name="EVPN-UNDERLAY",
                admin_state=ni.EnumerationEnum.enable,
                router_id=str(model.sw.router.router_id),
                version="ospf-v2",
                max_ecmp_paths=4,
                area=[
                    ni.AreaListEntry(area_id=str(model.sw.router.area), interface=iface),
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
    rr_config = ni.RouteReflectorContainer2(
        client=True,
        cluster_id=ni.DottedQuadType(str(model.sw.router.area)),
    )
    neighs = [
        ni.NeighborListEntry(
            peer_address=ni.Ipv4AddressWithZoneType(str(peer_ip)),
            description=f"SPINE {peer_name}",
            peer_group="EVPN_OVERLAY",
            transport=ni.TransportContainer3(
                local_address=ni.Ipv4AddressType(str(model.sw.router.router_id)),
            ),
        )
        for peer_name, peer_ip in model.sw.router.evpn_peers.items()
    ]
    protocols = cast(ni.ProtocolsContainer, model.vrfs_objs["default"].protocols)
    protocols.bgp = ni.BgpContainer(
        admin_state=ni.EnumerationEnum.enable,
        router_id=ni.Ipv4AddressType(str(model.sw.router.router_id)),
        autonomous_system=model.sw.router.asn,
        afi_safi=[
            ni.AfiSafiListEntry(
                afi_safi_name="evpn",
                admin_state=ni.EnumerationEnum.enable,
                evpn=ni.EvpnContainer(),
            ),
        ],
        group=[
            ni.GroupListEntry(
                group_name="EVPN_OVERLAY",
                description="EVPN overlay",
                next_hop_self=True,
                peer_as=model.sw.router.asn,
                route_reflector=rr_config if model.sw.router.rr else None,
                export_policy=[ni.ExportPolicyLeafList3("all")],
                import_policy=[ni.ImportPolicyLeafList3("all")],
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
            vlan_tagging=(
                True if "ethernet-" in interface_name or "lag" in interface_name else None
            ),
            description=interface.description if interface.description else None,
            admin_state=(
                mif.EnumerationEnum.enable if interface.admin_state else mif.EnumerationEnum.disable
            ),
            subinterface=[],
            mtu=interface.mtu if interface.mtu != DEFAULT_MTU else None,
        )
        mode.interfaces_objs[interface_name] = iface_obj


@srlinux_template
def lag_child_interface(node: SRLinuxYang) -> None:
    """Link child interface into LACP interface.

    Args:
        node (SRLinuxYang): node
    """
    for lag_id, lag_members in node.sw.interfaces.lags.items():
        for lag_member in lag_members:
            iface_object = node.interfaces_objs[lag_member]
            iface_object.admin_state = mif.EnumerationEnum.enable
            iface_object.vlan_tagging = None
            iface_object.ethernet = mif.EthernetContainer(aggregate_id=f"lag{lag_id}")


@srlinux_template
def lag_parent_interface(node: SRLinuxYang) -> None:
    """Define LAG for parent interfaces."""
    for lag_id in node.sw.interfaces.lags:
        lag_iface_name = f"lag{lag_id}"
        iface_object = node.interfaces_objs[lag_iface_name]
        iface_object.lag = mif.LagContainer(
            lag_type=mif.EnumerationEnum86.lacp,
            lacp_fallback_mode=mif.EnumerationEnum88.static,
            lacp=mif.LacpContainer3(
                lacp_mode=mif.EnumerationEnum90.active,
                interval=mif.EnumerationEnum93.fast,
                system_id_mac=node.sw.system_id,
                admin_key=lag_id,
                system_priority=lag_id,
            ),
        )


@srlinux_template
def routing_policy(mode: SRLinuxYang) -> None:
    """Define base routing policy."""
    mode.routing_policy.routing_policy = rp.RoutingPolicyContainer(
        policy=[
            rp.PolicyListEntry(
                name="all",
                default_action=rp.DefaultActionContainer(policy_result=rp.EnumerationEnum2.accept),
            ),
        ],
    )
