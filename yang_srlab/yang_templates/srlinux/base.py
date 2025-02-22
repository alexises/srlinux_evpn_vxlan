"""Base config."""

from yang_srlab.yang_model.srlinux import SRLinuxYang, srlinux_template


@srlinux_template
def base(model: SRLinuxYang) -> None:
    """Set base configuration.

    Args:
        model (SRLinuxYang): model
    """
