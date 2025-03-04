"""Define srlinux storage class."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

from pydantic_srlinux.models.interfaces import InterfaceListEntry
from pydantic_srlinux.models.interfaces import Model as InterfacesModel
from pydantic_srlinux.models.network_instance import Model as NEModel
from pydantic_srlinux.models.network_instance import NetworkInstanceListEntry
from pydantic_srlinux.models.routing_policy import Model as RPModel
from pydantic_srlinux.models.system import Model as SysModel
from pydantic_srlinux.models.tunnel_interfaces import Model as TunnelModel

from .interface import YangInterafece
from .templates import TemplateGroup

if TYPE_CHECKING:
    from collections.abc import Callable

srlinux_templates: TemplateGroup[SRLinuxYang] = TemplateGroup()


def srlinux_template(func: Callable[[SRLinuxYang], None]) -> Callable[[SRLinuxYang], None]:
    """Decorator for SRLinuxYang templating functions."""
    return srlinux_templates.register(func)


@dataclass
class SRLinuxYang(YangInterafece):
    """Define SRLinuxYang Model."""

    vrfs: NEModel = field(default_factory=NEModel)
    tunnel: TunnelModel = field(default_factory=TunnelModel)
    interfaces: InterfacesModel = field(default_factory=InterfacesModel)
    routing_policy: RPModel = field(default_factory=RPModel)
    system: SysModel = field(default_factory=SysModel)
    vrfs_objs: dict[str, NetworkInstanceListEntry] = field(default_factory=dict)
    interfaces_objs: dict[str, InterfaceListEntry] = field(default_factory=dict)
    tls: dict = field(default_factory=dict)
    logging: dict = field(default_factory=dict)
    snmp: dict = field(default_factory=dict)

    def __post_init__(self: Self) -> None:
        """Set kind."""
        self.kind = "srlinux"

    def run(self: Self) -> None:
        """Run all methods against object.

        Args:
            self (Self): self
        """
        srlinux_templates.run(self)

    def _fix_yang_model(self: Self, data: dict) -> dict:
        """Fix part of yang model that is not manageble."""
        # ssh
        system = data["srl_nokia-system:system"]
        ssh_server = system["srl_nokia-ssh:ssh-server"]
        for i in ssh_server:
            i["srl_nokia-ssh:network-instance"] = "mgmt"

        # grpc
        grpc = system["srl_nokia-grpc:grpc-server"]
        for i in grpc:
            if i["srl_nokia-grpc:name"] == "eda-insecure-mgmt":
                continue
            i["srl_nokia-grpc:network-instance"] = "mgmt"

        # dns
        dns = system["srl_nokia-dns:dns"]
        dns["srl_nokia-dns:network-instance"] = "mgmt"

        # tls
        system["srl_nokia-tls:tls"] = self.tls

        # logging
        system["srl_nokia-logging:logging"] = self.logging

        # snmp
        system["srl_nokia-snmp:snmp"] = self.snmp

        # netconf
        system["srl_nokia-netconf-server:netconf-server"][0][
            "srl_nokia-netconf-server:ssh-server"
        ] = "mgmt-netconf"

        # esi fix
        paths = [
            "srl_nokia-system-network-instance:network-instance",
            "srl_nokia-system-network-instance:protocols",
            "srl_nokia-system-network-instance:evpn",
            "srl_nokia-system-network-instance-bgp-evpn-ethernet-segments:ethernet-segments",
            "srl_nokia-system-network-instance-bgp-evpn-ethernet-segments:bgp-instance",
        ]
        bgp_instances = system
        for path in paths:
            bgp_instances = bgp_instances.get(path, {})

        basepath = "srl_nokia-system-network-instance-bgp-evpn-ethernet-segments:"
        for instance in bgp_instances:
            for segment in instance.get(f"{basepath}ethernet-segment", []):
                assoc = segment[f"{basepath}interface-association"]
                del segment[f"{basepath}interface-association"]
                segment[f"{basepath}interface"] = assoc[f"{basepath}interface"]
        return data

    def to_yang(self: Self) -> dict:
        """Convert internal model into yang.

        Args:
            self (Self): self

        Returns:
            dict: converted yang model
        """
        tmp_dict = {
            **self.vrfs.model_dump(
                mode="json",
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
            **self.tunnel.model_dump(
                mode="json",
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
            **self.interfaces.model_dump(
                mode="json",
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
            **self.routing_policy.model_dump(
                mode="json",
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
            **self.system.model_dump(
                mode="json",
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
        }
        return self._fix_yang_model(tmp_dict)
