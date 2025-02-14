"""Describe interfaces."""

from typing import Self

from pydantic_srlinux.models.interfaces import (
    DhcpClientContainer,
    DhcpClientContainer2,
    EnumerationEnum,
    InterfaceListEntry,
    Ipv4Container,
    Ipv6Container,
    Model,
    SubinterfaceListEntry,
)


class Interface:
    """Define interface configuration."""

    def __init__(self: Self, name: str) -> None:
        """Base container for interface.

        Args:
            self (Self): self
            name (str): name of interface
        """
        self._name: str = name
        self._description: str = ""
        self._admin_state: bool = False

    @property
    def name(self: Self) -> str:
        """Get interface name.

        Args:
            self (Self): _description_

        Returns:
            str: _description_
        """
        return self._name

    @property
    def description(self: Self) -> str:
        """Get interface description.

        Args:
            self (Self): self

        Returns:
            str: interface description
        """
        return self._description

    @description.setter
    def description(self: Self, description: str) -> None:
        """Set interface description.

        Args:
            self (Self): self
            description (str): description to set.
        """
        self._description = description

    @property
    def admin_state(self: Self) -> bool:
        """Get admin state of interface.

        Args:
            self (Self): self

        Returns:
            bool: true if state is up, false if down
        """
        return self._admin_state

    @admin_state.setter
    def admin_state(self: Self, admin_state: bool) -> None:
        """Set admin state of interface.

        Args:
            self (Self): self
            admin_state (bool): state of interface to set.
        """
        self._admin_state = admin_state

    def to_yang(self: Self) -> InterfaceListEntry:
        """Return yang object suitable for seralization.

        Args:
            self (Self): self

        Returns:
            InterfaceListEntry: YangObject
        """
        return InterfaceListEntry(
            name=self.name,
            description=self.description if self.description else None,
            admin_state=EnumerationEnum.enable if self.admin_state else EnumerationEnum.disable,
        )


class InterfaceContainer:
    """Store the whole interface block on a switch."""

    def __init__(self: Self, interface_count: int = 20) -> None:
        """Constructor.

        Args:
            self (Self): self
            interface_count (int): Number of interface on the switch
        """
        self._interfaces: dict[str, Interface] = {}
        for i in range(interface_count):
            iface_template = f"ethernet-1/{i+1}"
            self._interfaces[iface_template] = Interface(iface_template)

    @property
    def interfaces(self: Self) -> dict[str, Interface]:
        """Get interface list.

        Args:
            self (Self): self

        Returns:
            dict[str, Interface]: desc.
        """
        return self._interfaces

    def shutdown_all_interface(self: Self) -> None:
        """Shutdown all interface for basic configuration setup.

        Args:
            self (Self): self.
        """
        for interface in self._interfaces.values():
            interface.admin_state = False

    def to_yang(self: Self) -> Model:
        """Return yang object suitable for seralization.

        Args:
            self (Self): self

        Returns:
            InterfaceListEntry: YangObject
        """
        ifaces = [i.to_yang() for i in self._interfaces.values()]

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
                )
            ],
        )
        ifaces.append(mgmt_iface)
        return Model(interface=ifaces)
