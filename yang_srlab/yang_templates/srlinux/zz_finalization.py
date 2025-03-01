"""Finalize yang object."""

from yang_srlab.yang import SRClient
from yang_srlab.yang_model.srlinux import SRLinuxYang, srlinux_template


@srlinux_template
def merge_vrf(model: SRLinuxYang) -> None:
    """Merge vrfs list into their model."""
    model.interfaces_objs["system0"].vlan_tagging = None
    model.vrfs.network_instance = list(model.vrfs_objs.values())
    model.interfaces.interface = list(model.interfaces_objs.values())


@srlinux_template
def collect_non_manged_yang(model: SRLinuxYang) -> None:
    """Set non managed yang models."""
    cli = SRClient(str(model.sw.address), model.sw.username, model.sw.password)

    model.logging = cli.get_running_config("/system/logging")
    model.tls = cli.get_running_config("/system/tls")
    model.snmp = cli.get_running_config("/system/snmp")
