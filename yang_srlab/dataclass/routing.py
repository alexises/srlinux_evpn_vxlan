"""Generate common info for routing protocol."""

from ipaddress import IPv4Address
from typing import Self

from pydantic_srlinux.models.network_instance import (
    EnumerationEnum,
    InterfaceListEntry,
    LinuxContainer,
    Model,
    NetworkInstanceListEntry,
    ProtocolsContainer,
)


class RoutingContainer:
    """Store info for routing protocol."""

    def __init__(self: Self) -> None:
        """Constructor.

        Args:
            self (Self): self
        """
        self._router_id: IPv4Address = IPv4Address("0.0.0.0")  # noqa: S104
        self._interfaces: list[str] = []

    @property
    def router_id(self: Self) -> IPv4Address:
        """Get router id.

        Args:
            self (Self): self.

        Returns:
            IPv4Address : router id
        """
        return self._router_id

    @router_id.setter
    def router_id(self: Self, router_id: IPv4Address) -> None:
        """Set router id.

        Args:
            self (Self): self
            router_id (IPv4Address): store router id
        """
        self._router_id = router_id

    @property
    def interface(self: Self) -> list[str]:
        """Get interface on the vrf.

        Args:
            self (Self): self

        Returns:
            list[str]: interface config
        """
        return self._interfaces

    def to_yamg(self: Self) -> Model:
        """Get yang model associated with this model.

        Args:
            self (Self): self

        Returns:
            Model: yang model.
        """
        interfaces = [InterfaceListEntry(name=i) for i in self._interfaces]

        return Model(
            network_instance=[
                NetworkInstanceListEntry(
                    name="default",
                    router_id=str(self.router_id),
                    interface=interfaces,
                ),
                NetworkInstanceListEntry(
                    name="mgmt",
                    admin_state=EnumerationEnum.enable,
                    type="ip-vrf",
                    description="Management network instance",
                    interface=[InterfaceListEntry(name="mgmt0.0")],
                    protocols=ProtocolsContainer(
                        linux=LinuxContainer(
                            import_routes=True,
                            export_routes=True,
                            export_neighbors=True,
                        ),
                    ),
                ),
            ],
        )
