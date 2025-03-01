"""Define configuration for all switches."""

import pathlib
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


@template_group("common")
def get_ssh_keys(sto: ComputeContainer) -> None:
    """Define ssh keys."""
    ssh_base = pathlib.Path.home() / ".ssh"
    for file in ssh_base.iterdir():
        if not file.name.endswith(".pub"):
            continue
        with file.open() as f:
            lines = f.readlines()
            sto.container.ssh_keys.append(lines[0].strip())


@template_group("common")
def set_creedentials(sto: ComputeContainer) -> None:
    """Set credentials for users."""
    sto.container.password = sto.switch.password
    sto.container.username = sto.switch.username
    sto.container.address = str(sto.switch.address)
