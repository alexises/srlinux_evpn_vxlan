"""Generate common info for routing protocol."""

from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Interface
from typing import Self


def _default_addr() -> IPv4Address:
    return IPv4Address("0.0.0.0")  # noqa: S104


@dataclass
class RoutingContainer:
    """Store info for routing protocol."""

    router_id: IPv4Address = field(default_factory=_default_addr)
    interfaces: list[str] = field(default_factory=list)
    area: IPv4Address = field(default_factory=_default_addr)
    asn: int = field(default=0)
    rr: bool = field(default=False)
    evpn_peers: dict[str, IPv4Address] = field(default_factory=dict)
    clients: dict[str, int] = field(default_factory=dict)
    vlans: dict[str, int] = field(default_factory=dict)
    subnets: dict[int, IPv4Interface] = field(default_factory=dict)

    @property
    def reverse_vlan(self: Self) -> dict[int, str]:
        """Get reverse association between vlan id and vlan.

        Returns:
            dict[int, str] association betwwe vlan id and vlan name
        """
        return {vlan_id: vlan_name for vlan_name, vlan_id in self.vlans.items()}
