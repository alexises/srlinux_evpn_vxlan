"""Configuration related to the clients."""

from typing import cast

import pydantic_srlinux.models.interfaces as mif
from pydantic_srlinux.models.network_instance import (
    EnumerationEnum,
    InterfaceListEntry,
    NetworkInstanceListEntry,
    VxlanInterfaceListEntry,
)
from pydantic_srlinux.models.tunnel_interfaces import IngressContainer
from pydantic_srlinux.models.tunnel_interfaces import (
    VxlanInterfaceListEntry as TunnelVxlanInterfaceListEntry,
)

from yang_srlab.yang_model.srlinux import SRLinuxYang, srlinux_template


@srlinux_template
def layer2_vrfs(model: SRLinuxYang) -> None:
    """Configure L2 VRF."""
    for vlan_name, vlan_id in model.sw.router.vlans.items():
        vrf_name = f"VLAN_{vlan_name.upper()}"
        vrf = NetworkInstanceListEntry(
            name=vrf_name,
            admin_state=EnumerationEnum.enable,
            type="mac-vrf",
            interface=[InterfaceListEntry(name=f"irb0.{vlan_id}")],
            vxlan_interface=[
                VxlanInterfaceListEntry(name=f"vxlan1.{vlan_id}"),
            ],
        )
        model.vrfs_objs[vrf_name] = vrf


@srlinux_template
def layer2_evpn(model: SRLinuxYang) -> None:
    """Define layer 2 EVPN tunnel inteface."""
    vxlan_interfaces: list[TunnelVxlanInterfaceListEntry] = []
    for vlan_id in model.sw.router.vlans.values():
        iface = TunnelVxlanInterfaceListEntry(
            index=vlan_id,
            type="bridged",
            ingress=IngressContainer(vni=vlan_id),
        )
        vxlan_interfaces.append(iface)

    tun_iface = cast(list[TunnelVxlanInterfaceListEntry], model.tunnel.tunnel_interface)
    tun_iface += vxlan_interfaces


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
