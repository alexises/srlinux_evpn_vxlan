"""Define common elems."""

import pathlib

from yang_srlab.compute.container import ComputeContainer
from yang_srlab.compute.template_scanner import template_group


@template_group("common_all")
def get_ssh_keys(sto: ComputeContainer) -> None:
    """Define ssh keys."""
    ssh_base = pathlib.Path.home() / ".ssh"
    for file in ssh_base.iterdir():
        if not file.name.endswith(".pub"):
            continue
        with file.open() as f:
            lines = f.readlines()
            sto.container.ssh_keys.append(lines[0].strip())


@template_group("common_all")
def set_creedentials(sto: ComputeContainer) -> None:
    """Set credentials for users."""
    sto.container.password = sto.switch.password
    sto.container.username = sto.switch.username
    sto.container.address = str(sto.switch.address)
