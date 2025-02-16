"""Describe interfaces."""

from dataclasses import InitVar, dataclass, field
from enum import Enum
from ipaddress import IPv4Interface
from typing import Self

from pydantic_srlinux.models.interfaces import (
    AddressListEntry,
    DhcpClientContainer,
    DhcpClientContainer2,
    EnumerationEnum,
    InterfaceListEntry,
    Ipv4Container,
    Ipv6Container,
    Model,
    SubinterfaceListEntry,
)

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
    mtu: int = field(default=DEFAULT_MTU)

    def to_yang(self: Self) -> InterfaceListEntry:
        """Return yang object suitable for seralization.

        Args:
            self (Self): self

        Returns:
            InterfaceListEntry: YangObject
        """
        subinterfaces: list[SubinterfaceListEntry] = []
        if self.kind == InterfaceKind.L3:
            for vlan_id, ip in self.ips.items():
                subif = SubinterfaceListEntry(
                    index=vlan_id,
                    admin_state=EnumerationEnum.enable,
                    ipv4=Ipv4Container(
                        admin_state=EnumerationEnum.enable,
                        address=[AddressListEntry(ip_prefix=str(ip))],
                    ),
                )
                subinterfaces.append(subif)

        return InterfaceListEntry(
            name=self.name,
            description=self.description if self.description else None,
            admin_state=EnumerationEnum.enable if self.admin_state else EnumerationEnum.disable,
            subinterface=subinterfaces if subinterfaces != [] else None,
            mtu=self.mtu if self.mtu != DEFAULT_MTU else None,
        )


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

    def to_yang(self: Self) -> Model:
        """Return yang object suitable for seralization.

        Args:
            self (Self): self

        Returns:
            InterfaceListEntry: YangObject
        """
        ifaces = [i.to_yang() for i in self.interfaces.values()]

        # manualy creating the management interface
        mgmt_iface = InterfaceListEntry(
            name="mgmt0",
            admin_state=EnumerationEnum.enable,
            subinterface=[
                SubinterfaceListEntry(
                    index=0,
                    admin_state=EnumerationEnum.enable,
                    ipv4=Ipv4Container(
                        admin_state=EnumerationEnum.enable,
                        dhcp_client=DhcpClientContainer(),
                    ),
                    ipv6=Ipv6Container(
                        admin_state=EnumerationEnum.enable,
                        dhcp_client=DhcpClientContainer2(),
                    ),
                ),
            ],
        )
        ifaces.append(mgmt_iface)
        return Model(interface=ifaces)
