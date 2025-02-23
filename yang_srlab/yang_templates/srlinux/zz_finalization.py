"""Finalize yang object."""

from yang_srlab.yang_model.srlinux import SRLinuxYang, srlinux_template


@srlinux_template
def merge_vrf(model: SRLinuxYang) -> None:
    """Merge vrfs list into their model."""
    model.interfaces_objs["system0"].vlan_tagging = None
    model.vrfs.network_instance = list(model.vrfs_objs.values())
    model.interfaces.interface = list(model.interfaces_objs.values())
