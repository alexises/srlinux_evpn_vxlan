"""Define configuration for all switches."""

from ipaddress import IPv4Address

from yang_srlab.compute.container import ComputeContainer
from yang_srlab.compute.template_scanner import template_group


@template_group("common")
def compute_switch(sto: ComputeContainer) -> None:
    """Compute common configuration for switch.

    Args:
        sto (ComputeContainer): container.
    """
    fabric = sto.switch.fabric
    sto.container.interfaces.shutdown_all_interface()
    sto.container.router.area = IPv4Address(fabric.id)
    sto.container.router.asn = 65100 + fabric.id // 100
