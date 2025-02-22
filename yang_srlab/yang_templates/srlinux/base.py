"""Base config."""

from yang_srlab.yang_model.srlinux import SRLinuxYang
from yang_srlab.yang_model.templates import template_group


@template_group("srlinux")
def base(model: SRLinuxYang) -> None:
    """Set base configuration.

    Args:
        model (SRLinuxYang): model
    """
