"""Make conputation to transform meta model into Yang represantation."""

from ipaddress import IPv4Address, IPv4Interface
from typing import Self

from .dataclass import SwitchContainer
from .dataclass.interface import Interface, InterfaceKind
from .metamodel import Fabric, Metamodel, Switch


class YangController:
    """Define yang controller that in charge of generating the corresponding yang config."""

    def __init__(self: Self, model: Metamodel) -> None:
        """Constructor.

        Args:
            self (Self): self
            model (Metamodel): base metamodel.
        """
        self._model: Metamodel = model

    def compute_all(self: Self, allowed_switch: list[str]) -> list[tuple[Switch, dict]]:
        """Generate yang for all site and switchs.

        Args:
            self (Self): self
            allowed_switch (list[str]): list of allowed switch, empty list will run on all switchs.

        Return:
            list[tuple[Switch, dict]]: computed config.
        """
        computed_switch = []
        for site in self._model.fabrics:
            for leaf in site.lifs:
                if leaf.name not in allowed_switch and allowed_switch != []:
                    continue
                container = SwitchContainer()
                self.compute_switch(container, site, leaf)
                self.compute_leaf(container, site, leaf)
                computed_switch.append((leaf, container.to_yang()))
            for spine in site.spines:
                if spine.name not in allowed_switch and allowed_switch != []:
                    continue
                container = SwitchContainer()
                self.compute_switch(container, site, spine)
                self.compute_spine(container, site, spine)
                computed_switch.append((spine, container.to_yang()))
        return computed_switch

    def compute_switch(
        self: Self,
        container: SwitchContainer,
        fabric: Fabric,
        switch: Switch,  # noqa: ARG002
    ) -> None:
        """Compute common configuration for switch.

        Args:
            self (Self): Self.
            container (SwitchContainer): container
            fabric (Fabric): fabric object of the switch
            switch (Switch): switch object to compute.
        """
        container.interfaces.shutdown_all_interface()
        container.router.area = IPv4Address(fabric.id)
        container.router.asn = 65100 + fabric.id // 100

    def compute_leaf(
        self: Self,
        container: SwitchContainer,
        fabric: Fabric,
        switch: Switch,
    ) -> None:
        """Compute configuration for leaf.

        Args:
            self (Self): Self.
            container (SwitchContainer): container
            fabric (Fabric): fabric object of the switch
            switch (Switch): switch object to compute.
        """
        self._compute_spine_link(fabric, switch, container)
        self._compute_leaf_loopback(fabric, switch, container)

    def compute_spine(
        self: Self,
        container: SwitchContainer,
        fabric: Fabric,
        switch: Switch,
    ) -> None:
        """Compute configuration for leaf.

        Args:
            self (Self): Self.
            container (SwitchContainer): container
            fabric (Fabric): fabric object of the switch
            switch (Switch): switch object to compute.
        """
        container.router.rr = True
        self._compute_leaf_link(fabric, switch, container)
        self._compute_spine_loopback(fabric, switch, container)

    def _compute_leaf_link(
        self: Self,
        fabric: Fabric,
        switch: Switch,
        container: SwitchContainer,
    ) -> None:
        for leaf_index, leaf in enumerate(fabric.lifs):
            port_index = leaf_index
            port_name = f"ethernet-1/{port_index+1}"
            port = container.interfaces.interfaces[port_name]
            spine_index = fabric.spines.index(switch)

            subnet = list(fabric.pool.links.subnets(new_prefix=31))
            subnet_count = len(subnet) // len(fabric.spines)
            subnet_index = subnet_count * spine_index + leaf_index
            leaf_spine_subnet = subnet[subnet_index]
            leaf_spine_interface = list(leaf_spine_subnet.hosts())[0]

            port.description = f"{leaf.name} ethernet-1/{20-spine_index-1}"
            port.admin_state = True
            port.kind = InterfaceKind.L3
            port.ips[0] = IPv4Interface(f"{leaf_spine_interface}/31")
            port.mtu = 9000

            # add port to routing interface
            container.router.interfaces.append(f"{port_name}.0")
            # add evpn peer
            leaf_loopback = list(fabric.pool.loopbacks.hosts())[32 + leaf_index]
            container.router.evpn_peers[leaf.name] = leaf_loopback

    def _compute_spine_link(
        self: Self,
        fabric: Fabric,
        switch: Switch,
        container: SwitchContainer,
    ) -> None:
        for spine_index, spine in enumerate(fabric.spines):
            port_index = len(container.interfaces.interfaces) - len(fabric.spines) + spine_index
            port_name = f"ethernet-1/{port_index+1}"
            port = container.interfaces.interfaces[port_name]
            leaf_index = fabric.lifs.index(switch)

            subnet = list(fabric.pool.links.subnets(new_prefix=31))
            subnet_count = len(subnet) // len(fabric.spines)
            subnet_index = subnet_count * spine_index + leaf_index
            leaf_spine_subnet = subnet[subnet_index]
            leaf_spine_interface = list(leaf_spine_subnet.hosts())[1]

            port.description = f"{spine.name} ethernet-1/{leaf_index+1}"
            port.admin_state = True
            port.kind = InterfaceKind.L3
            port.ips[0] = IPv4Interface(f"{leaf_spine_interface}/31")
            port.mtu = 9000

            # add port to routing instance
            container.router.interfaces.append(f"{port_name}.0")
            # add evpn peer
            spine_loopback = list(fabric.pool.loopbacks.hosts())[spine_index]
            container.router.evpn_peers[spine.name] = spine_loopback

    def _compute_leaf_loopback(
        self: Self,
        fabric: Fabric,
        switch: Switch,
        container: SwitchContainer,
    ) -> None:

        iface = Interface("system0")
        container.interfaces.interfaces[iface.name] = iface

        leaf_index = fabric.lifs.index(switch)
        subnet = list(fabric.pool.loopbacks.hosts())
        loopback = subnet[32 + leaf_index]

        iface.admin_state = True
        iface.kind = InterfaceKind.L3
        iface.description = "EVPN TEP/OSPF loopback"
        iface.ips[0] = IPv4Interface(f"{loopback}/32")

        # also set router_id conviniently
        container.router.router_id = loopback
        container.router.interfaces.append("system0.0")

    def _compute_spine_loopback(
        self: Self,
        fabric: Fabric,
        switch: Switch,
        container: SwitchContainer,
    ) -> None:

        iface = Interface("system0")
        container.interfaces.interfaces[iface.name] = iface

        spine_index = fabric.spines.index(switch)
        subnet = list(fabric.pool.loopbacks.hosts())
        loopback = subnet[spine_index]

        iface.admin_state = True
        iface.kind = InterfaceKind.L3
        iface.description = "EVPN TEP/OSPF loopback"
        iface.ips[0] = IPv4Interface(f"{loopback}/32")

        # also set router_id conviniently
        container.router.router_id = loopback
        container.router.interfaces.append("system0.0")
