"""Compute spine configuration."""

from ipaddress import IPv4Interface

from yang_srlab.compute.container import ComputeContainer
from yang_srlab.compute.template_scanner import template_group
from yang_srlab.dataclass.interface import Interface, InterfaceKind


@template_group("spine")
def compute_downlinks(sto: ComputeContainer) -> None:
    """Compute EVPN/Underlay downlinks.

    Args:
        sto (ComputeContainer): container.
    """
    lifs = sto.switch.fabric.lifs
    spines = sto.switch.fabric.spines
    links = sto.switch.fabric.pool.links
    loopbacks = sto.switch.fabric.pool.loopbacks

    for leaf_index, leaf in enumerate(lifs):
        port_index = leaf_index
        port_name = f"ethernet-1/{port_index+1}"
        port = sto.container.interfaces.interfaces[port_name]
        spine_index = spines.index(sto.switch)

        subnet = list(links.subnets(new_prefix=31))
        subnet_count = len(subnet) // len(spines)
        subnet_index = subnet_count * spine_index + leaf_index
        leaf_spine_subnet = subnet[subnet_index]
        leaf_spine_interface = list(leaf_spine_subnet.hosts())[0]

        port.description = f"{leaf.name} ethernet-1/{20-spine_index-1}"
        port.admin_state = True
        port.kind = InterfaceKind.L3
        port.ips[0] = IPv4Interface(f"{leaf_spine_interface}/31")
        port.mtu = 9000

        # add port to routing interface
        sto.container.router.interfaces.append(f"{port_name}.0")
        # add evpn peer
        leaf_loopback = list(loopbacks.hosts())[32 + leaf_index]
        sto.container.router.evpn_peers[leaf.name] = leaf_loopback


@template_group("spine")
def compute_loopback(sto: ComputeContainer) -> None:
    """Compute EVPN/Underlay loopback.

    Args:
        sto (ComputeContainer): container.
    """
    spines = sto.switch.fabric.spines
    loopbacks = sto.switch.fabric.pool.loopbacks

    iface = Interface("system0")
    sto.container.interfaces.interfaces[iface.name] = iface

    spine_index = spines.index(sto.switch)
    subnet = list(loopbacks.hosts())
    loopback = subnet[spine_index]

    iface.admin_state = True
    iface.kind = InterfaceKind.L3
    iface.description = "EVPN TEP/OSPF loopback"
    iface.ips[0] = IPv4Interface(f"{loopback}/32")

    # also set router_id conviniently
    sto.container.router.rr = True
    sto.container.router.router_id = loopback
    sto.container.router.interfaces.append("system0.0")
