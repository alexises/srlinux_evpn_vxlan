"""Configuration related to the clients."""

from typing import cast

import pydantic_srlinux.models.interfaces as mif
import pydantic_srlinux.models.network_instance as ni
import pydantic_srlinux.models.tunnel_interfaces as tun

from yang_srlab.yang_model.srlinux import SRLinuxYang, srlinux_template


@srlinux_template
def layer2_vrfs(model: SRLinuxYang) -> None:
    """Configure L2 VRF."""
    for vlan_name, vlan_id in model.sw.router.vlans.items():
        vrf_name = f"VLAN_{vlan_name.upper()}"
        vxlan_iface = f"vxlan1.{vlan_id}"
        evpn_proto = ni.BgpEvpnContainer(
            bgp_instance=[
                ni.BgpInstanceListEntry(
                    id=1,
                    ecmp=4,
                    evi=vlan_id,
                    admin_state=ni.EnumerationEnum.enable,
                    vxlan_interface=vxlan_iface,
                ),
            ],
        )
        rt = f"target:{model.sw.router.asn}:{vlan_id}"
        vpn_proto = ni.BgpVpnContainer2(
            bgp_instance=[
                ni.BgpInstanceListEntry3(
                    id=1,
                    route_target=(
                        ni.RouteTargetContainer3(
                            export_rt=ni.BgpExtCommunityTypeType1(rt),
                            import_rt=ni.BgpExtCommunityTypeType1(rt),
                        )
                    ),
                ),
            ],
        )

        vrf = ni.NetworkInstanceListEntry(
            name=vrf_name,
            admin_state=ni.EnumerationEnum.enable,
            type="mac-vrf",
            interface=[ni.InterfaceListEntry(name=f"irb0.{vlan_id}")],
            vxlan_interface=[
                ni.VxlanInterfaceListEntry(name=vxlan_iface),
            ],
            protocols=ni.ProtocolsContainer(bgp_evpn=evpn_proto, bgp_vpn=vpn_proto),
        )
        model.vrfs_objs[vrf_name] = vrf


@srlinux_template
def layer2_evpn(model: SRLinuxYang) -> None:
    """Define layer 2 EVPN tunnel inteface."""
    vxlan_interfaces: list[tun.VxlanInterfaceListEntry] = []
    for vlan_id in model.sw.router.vlans.values():
        iface = tun.VxlanInterfaceListEntry(
            index=vlan_id,
            type="bridged",
            ingress=tun.IngressContainer(vni=vlan_id),
        )
        vxlan_interfaces.append(iface)

    tun_iface = cast(list[tun.TunnelInterfaceListEntry], model.tunnel.tunnel_interface)
    vxlan_iface = cast(list[tun.VxlanInterfaceListEntry], tun_iface[0].vxlan_interface)
    vxlan_iface += vxlan_interfaces


@srlinux_template
def layer2_subintefaces(model: SRLinuxYang) -> None:
    """Define layer 2 subinterfaces."""
    for iface_name, iface in model.sw.interfaces.interfaces.items():
        subinterfaces: list[mif.SubinterfaceListEntry] = []
        for vlan_id in iface.vlans:
            subif = mif.SubinterfaceListEntry(
                index=vlan_id,
                admin_state=mif.EnumerationEnum.enable,
                type="bridged",
                vlan=mif.VlanContainer(
                    encap=mif.EncapContainer(
                        single_tagged=mif.SingleTaggedContainer(vlan_id=mif.VlanIdType(vlan_id)),
                    ),
                ),
            )
            subinterfaces.append(subif)
        subinterfaces_obj = cast(
            list[mif.SubinterfaceListEntry],
            model.interfaces_objs[iface_name].subinterface,
        )
        subinterfaces_obj += subinterfaces


@srlinux_template
def layer2_vrf_subinterfaces_member(model: SRLinuxYang) -> None:
    """Define association with l2 vrf subinterfaces."""
    reverse_vlan = model.sw.router.reverse_vlan
    for iface_name, iface in model.sw.interfaces.interfaces.items():
        for vlan_id in iface.vlans:
            vrf_name = f"VLAN_{reverse_vlan[vlan_id].upper()}"
            interfaces = cast(list[ni.InterfaceListEntry], model.vrfs_objs[vrf_name].interface)
            interfaces.append(ni.InterfaceListEntry(name=f"{iface_name}.{vlan_id}"))
