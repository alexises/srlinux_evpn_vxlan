"""Define configuration for all switches."""

from ipaddress import IPv4Address, IPv4Interface

from yang_srlab.compute.container import ComputeContainer
from yang_srlab.compute.template_scanner import template_group


@template_group("dci")
def compute_switch(sto: ComputeContainer) -> None:
    """Compute common configuration for switch.

    Args:
        sto (ComputeContainer): container.
    """
    sto.container.interfaces.shutdown_all_interface()
    sto.container.router.area = IPv4Address("0.0.0.0")  # noqa: S104
    sto.container.router.asn = 65000

    sto.container.router.router_id = sto.switch.address


@template_group("dci")
def compute_interface(sto: ComputeContainer) -> None:
    """Compute interfaces for DCI switches.

    Args:
        sto (ComputeContainer): sto
    """
    leaf_id = 0
    dci_id = sto.switch.config.dci.index(sto.switch)
    for fabric in sto.switch.config.fabrics:
        subnet = list(fabric.pool.dci.subnets(new_prefix=31))
        subnet_count = len(subnet) // 2
        for spine_id, spine in enumerate(fabric.spines):
            subnet_index = subnet_count * dci_id + spine_id
            address = list(subnet[subnet_index].hosts())[1]
            leaf_id += 1
            iface = f"ethernet-1/{leaf_id}"

            iface_obj = sto.container.interfaces.interfaces[iface]
            iface_obj.description = f"{spine.name} ethernet1/{19 + dci_id}"
            iface_obj.admin_state = True
            iface_obj.mtu = 9000
            iface_obj.ips[0] = IPv4Interface(f"{address!s}/31")

            sto.container.router.interfaces.append(f"{iface}.0")
