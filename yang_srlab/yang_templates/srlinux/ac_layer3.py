"""Configure basic L3 for clients."""

from typing import cast

import pydantic_srlinux.models.interfaces as mif
from pydantic_srlinux.models.network_instance import (
    EnumerationEnum,
    NetworkInstanceListEntry,
    VxlanInterfaceListEntry,
)
from pydantic_srlinux.models.tunnel_interfaces import IngressContainer
from pydantic_srlinux.models.tunnel_interfaces import (
    VxlanInterfaceListEntry as TunnelVxlanInterfaceListEntry,
)

from yang_srlab.yang_model.srlinux import SRLinuxYang, srlinux_template


@srlinux_template
def layer3_vrfs(model: SRLinuxYang) -> None:
    """Define layer3 vrfs for clients."""
    for client_name, client_id in model.sw.router.clients.items():
        vrf_name = f"CLIENT_{client_name.upper()}"
        vrf = NetworkInstanceListEntry(
            name=vrf_name,
            admin_state=EnumerationEnum.enable,
            type="ip-vrf",
            interface=[],
            vxlan_interface=[
                VxlanInterfaceListEntry(name=f"vxlan1.{client_id+10000}"),
            ],
        )
        model.vrfs_objs[vrf_name] = vrf


@srlinux_template
def layer3_evpn(model: SRLinuxYang) -> None:
    """Define VXLAN tunnel interface for VRF."""
    vxlan_intefaces: list[TunnelVxlanInterfaceListEntry] = []
    for client_id in model.sw.router.clients.values():
        iface = TunnelVxlanInterfaceListEntry(
            index=client_id + 10000,
            type="routed",
            ingress=IngressContainer(vni=client_id + 10000),
        )
        vxlan_intefaces.append(iface)
    tun_iface = cast(list[TunnelVxlanInterfaceListEntry], model.tunnel.tunnel_interface)
    tun_iface += vxlan_intefaces


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
