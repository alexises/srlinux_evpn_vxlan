"""Configure basic L3 for clients."""

from typing import cast

import pydantic_srlinux.models.interfaces as mif
import pydantic_srlinux.models.network_instance as ni
import pydantic_srlinux.models.tunnel_interfaces as tun

from yang_srlab.yang_model.srlinux import SRLinuxYang, srlinux_template


@srlinux_template
def layer3_vrfs(model: SRLinuxYang) -> None:
    """Define layer3 vrfs for clients."""
    for client_name, client_id in model.sw.router.clients.items():
        vrf_name = f"CLIENT_{client_name.upper()}"
        vrf = ni.NetworkInstanceListEntry(
            name=vrf_name,
            admin_state=ni.EnumerationEnum.enable,
            type="ip-vrf",
            interface=[],
            vxlan_interface=[
                ni.VxlanInterfaceListEntry(name=f"vxlan1.{client_id+10000}"),
            ],
        )
        model.vrfs_objs[vrf_name] = vrf


@srlinux_template
def layer3_evpn(model: SRLinuxYang) -> None:
    """Define VXLAN tunnel interface for VRF."""
    vxlan_intefaces: list[tun.VxlanInterfaceListEntry] = []
    for client_id in model.sw.router.clients.values():
        iface = tun.VxlanInterfaceListEntry(
            index=client_id + 10000,
            type="routed",
            ingress=tun.IngressContainer(vni=client_id + 10000),
        )
        vxlan_intefaces.append(iface)
    tun_iface = cast(list[tun.TunnelInterfaceListEntry], model.tunnel.tunnel_interface)
    vxlan_iface = cast(list[tun.VxlanInterfaceListEntry], tun_iface[0].vxlan_interface)
    vxlan_iface += vxlan_intefaces


@srlinux_template
def layer3_subinterfaces(model: SRLinuxYang) -> None:
    """Define layer 3 subinterfaces."""
    for iface_name, iface in model.sw.interfaces.interfaces.items():
        subinterfaces: list[mif.SubinterfaceListEntry] = []
        for vlan_id, ip in iface.ips.items():
            model.interfaces_objs[iface_name].vlan_tagging = False
            subif = mif.SubinterfaceListEntry(
                index=vlan_id,
                admin_state=mif.EnumerationEnum.enable,
                ipv4=mif.Ipv4Container(
                    admin_state=mif.EnumerationEnum.enable,
                    address=[mif.AddressListEntry(ip_prefix=str(ip))],
                ),
            )
            subinterfaces.append(subif)
        subinterfaces_obj = cast(
            list[mif.SubinterfaceListEntry],
            model.interfaces_objs[iface_name].subinterface,
        )
        subinterfaces_obj += subinterfaces


@srlinux_template
def layer3_irb_mapping(model: SRLinuxYang) -> None:
    """Set IRB interface mapping."""
    for vlan_id, subnet_info in model.sw.router.subnets.items():
        vrf_name = f"CLIENT_{subnet_info.vrf.upper()}"
        iface = f"irb0.{vlan_id}"
        ifaces = cast(list[ni.InterfaceListEntry], model.vrfs_objs[vrf_name].interface)
        ifaces.append(ni.InterfaceListEntry(name=iface))


@srlinux_template
def anycast_gw_svi(model: SRLinuxYang) -> None:
    """Define anycast gateway interface."""
    irb_iface = mif.InterfaceListEntry(
        name="irb0",
        admin_state=mif.EnumerationEnum.enable,
    )
    irb_iface.subinterface = []

    reverse_vlan = model.sw.router.reverse_vlan

    for vlan_id, vrf_info in model.sw.router.subnets.items():
        subinterface = mif.SubinterfaceListEntry(
            index=vlan_id,
            description=f"SVI {reverse_vlan[vlan_id].upper()}",
            anycast_gw=mif.AnycastGwContainer(),
            ipv4=mif.Ipv4Container(
                admin_state=mif.EnumerationEnum.enable,
                address=[mif.AddressListEntry(ip_prefix=str(vrf_info.subnet), anycast_gw=True)],
            ),
        )
        irb_iface.subinterface.append(subinterface)

    model.interfaces_objs["irb0"] = irb_iface
