"""Describe interfaces."""

from dataclasses import InitVar, dataclass, field
from enum import Enum
from ipaddress import IPv4Interface
from typing import Self

DEFAULT_MTU = 1500


class InterfaceKind(Enum):
    """Define interface kind."""

    L2 = "l2"
    L3 = "l3"
    Undefined = ""


@dataclass
class Interface:
    """Define interface configuration."""

    name: str
    description: str = field(default="", init=False)
    admin_state: bool = field(default=False, init=False)
    kind: InterfaceKind = field(default=InterfaceKind.Undefined, init=False)
    ips: dict[int, IPv4Interface] = field(default_factory=dict)
    vlans: list[int] = field(default_factory=list)
    mtu: int = field(default=DEFAULT_MTU)
    with_tagging: bool = field(default=True)


@dataclass
class InterfaceContainer:
    """Store the whole interface block on a switch."""

    interfaces: dict[str, Interface] = field(default_factory=dict, init=False)
    interface_count: InitVar[int] = 20

    def __post_init__(self: Self, interface_count: int) -> None:
        """Constructor.

        Args:
            self (Self): self
            interface_count (int): Number of interface on the switch
        """
        for i in range(interface_count):
            iface_template = f"ethernet-1/{i+1}"
            self.interfaces[iface_template] = Interface(iface_template)

    def shutdown_all_interface(self: Self) -> None:
        """Shutdown all interface for basic configuration setup.

        Args:
            self (Self): self.
        """
        for interface in self.interfaces.values():
            interface.admin_state = False
