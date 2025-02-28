"""Generate configuration template specific to leaf."""

from ipaddress import IPv4Interface

from yang_srlab.compute.container import ComputeContainer
from yang_srlab.compute.template_scanner import template_group
from yang_srlab.dataclass.interface import Interface, InterfaceKind
from yang_srlab.dataclass.routing import VRFInfo


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


@template_group("leaf")
def compute_clients(sto: ComputeContainer) -> None:
    """Compute uplink to spine.

    Args:
        sto (ComputeContainer): container.
    """
    clients: dict[str, int] = {}
    vlans: dict[str, int] = {}
    subnets: dict[int, VRFInfo] = {}

    for port in sto.switch.ports.values():
        for client in port.template.clients:
            clients[client.name] = client.id
            for vlan in client.networks.values():
                vlans[vlan.name] = vlan.vlan_id
                subnets[vlan.vlan_id] = VRFInfo(vlan.subnet, client.name)

    sto.container.router.clients = clients
    sto.container.router.vlans = vlans
    sto.container.router.subnets = subnets


@template_group("leaf")
def compute_interface(sto: ComputeContainer) -> None:
    """Compute interface.

    Args:
        sto (ComputeContainer): container.
    """
    for port in sto.switch.ports.values():
        sw1, sw2 = port.switch
        if sw1 != sw2:
            sto.container.interfaces.lags[port.iface] = [f"ethernet-1/{port.iface}"]
            iface_name = f"lag{port.iface}"
            sto.container.interfaces.interfaces[iface_name] = Interface(iface_name)
        else:
            iface_name = f"ethernet-1/{port.iface}"
        iface_model = sto.container.interfaces.interfaces[iface_name]
        iface_model.admin_state = True
        iface_model.description = port.description
        iface_model.kind = InterfaceKind.L2
        for client in port.template.clients:
            iface_model.vlans = [network.vlan_id for network in client.networks.values()]


@template_group("leaf")
def compute_system_id(sto: ComputeContainer) -> None:
    """Compute the lacp systemid.

    Args:
        sto (ComputeContainer): container
    """
    leaf_id = sto.switch.fabric.lifs.index(sto.switch)  # type: ignore[arg-type]
    if leaf_id % 2 == 1:
        leaf_id -= 1

    site_id = sto.switch.fabric.id
    system_id = f"65:00:01:{site_id % 255:02x}:00:{leaf_id:02x}"
    sto.container.system_id = system_id
