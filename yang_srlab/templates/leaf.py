"""Generate configuration template specific to leaf."""

from ipaddress import IPv4Interface

from yang_srlab.compute.container import ComputeContainer
from yang_srlab.compute.template_scanner import template_group
from yang_srlab.dataclass.interface import Interface, InterfaceKind


@template_group("leaf")
def compute_spine_link(sto: ComputeContainer) -> None:
    """Compute uplink to spine.

    Args:
        sto (ComputeContainer): container.
    """
    container = sto.container
    spines = sto.switch.fabric.spines
    lifs = sto.switch.fabric.lifs
    links = sto.switch.fabric.pool.links
    loopbacks = sto.switch.fabric.pool.loopbacks

    for spine_index, spine in enumerate(sto.switch.fabric.spines):
        port_index = len(container.interfaces.interfaces) - len(spines) + spine_index
        port_name = f"ethernet-1/{port_index+1}"
        port = container.interfaces.interfaces[port_name]
        leaf_index = lifs.index(sto.switch)  # type: ignore[arg-type]

        subnet = list(links.subnets(new_prefix=31))
        subnet_count = len(subnet) // len(spines)
        subnet_index = subnet_count * spine_index + leaf_index
        leaf_spine_subnet = subnet[subnet_index]
        leaf_spine_interface = list(leaf_spine_subnet.hosts())[1]

        port.description = f"{spine.name} ethernet-1/{leaf_index+1}"
        port.admin_state = True
        port.kind = InterfaceKind.L3
        port.ips[0] = IPv4Interface(f"{leaf_spine_interface}/31")
        port.mtu = 9000

        # add port to routing instance
        container.router.interfaces.append(f"{port_name}.0")
        # add evpn peer
        spine_loopback = list(loopbacks.hosts())[spine_index]
        container.router.evpn_peers[spine.name] = spine_loopback


@template_group("leaf")
def compute_loopback(sto: ComputeContainer) -> None:
    """Compute EVPN/Underlay loopback.

    Args:
        sto (ComputeContainer): container.
    """
    lifs = sto.switch.fabric.lifs
    loopbacks = sto.switch.fabric.pool.loopbacks

    iface = Interface("system0")
    sto.container.interfaces.interfaces[iface.name] = iface

    leaf_index = lifs.index(sto.switch)  # type: ignore[arg-type]
    subnet = list(loopbacks.hosts())
    loopback = subnet[32 + leaf_index]

    iface.admin_state = True
    iface.kind = InterfaceKind.L3
    iface.description = "EVPN TEP/OSPF loopback"
    iface.ips[0] = IPv4Interface(f"{loopback}/32")

    # also set router_id conviniently
    sto.container.router.router_id = loopback
    sto.container.router.interfaces.append("system0.0")
