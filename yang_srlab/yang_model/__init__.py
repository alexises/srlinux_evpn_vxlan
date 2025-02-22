"""Define vendor specific yang models."""

from .interface import YangInterafece
from .srlinux import SRLinuxYang, srlinux_templates


def model_from_kind(kind: str) -> type[YangInterafece]:
    """Build model from kind of object.

    Args:
        kind (str): kind to check.

    Returns:
        type[YangInterafece]: yang interface
    """
    if kind == "srlinux":
        return SRLinuxYang
    return SRLinuxYang


def scan_yang(module: str) -> None:
    """Scan modules for all vendors.

    Args:
        module (str): module to scan
    """
    srlinux_templates.scan(f"{module}.srlinux")
