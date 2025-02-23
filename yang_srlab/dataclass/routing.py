"""Generate common info for routing protocol."""

from dataclasses import dataclass, field
from ipaddress import IPv4Address


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
