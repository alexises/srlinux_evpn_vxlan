"""Define metamodel class used as source of preprocessing."""

from enum import Enum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, PrivateAttr, field_validator, model_validator
from pydantic_yaml import parse_yaml_raw_as


class SwitchKind(Enum):
    """Describe switch kind."""

    srlinux = "srlinux"


class Default(BaseModel):
    """Describe default option for configuration."""

    username: str = ""
    password: str = ""


class Switch(BaseModel):
    """Representation of switch config."""

    name: str
    kind: SwitchKind
    address: IPv4Address
    username: str = Field(default="")
    password: str = Field(default="")
    _ports: dict[int, "Port"] = PrivateAttr(default_factory=dict)
    _fabric: "Fabric"

    def __eq__(self: Self, other: object) -> bool:
        """Check equity.

        Args:
            self (Self): self
            other (object): other

        Returns:
            bool: true if object had the same description, false otherwise
        """
        if not isinstance(other, Switch):
            return False
        return other.name == self.name

    @property
    def ports(self: Self) -> dict[int, "Port"]:
        """Get ports associated to this switch.

        Returns:
            dict[int, Port] port associated with this switch
        """
        return self._ports

    @ports.setter
    def ports(self: Self, ports: dict[int, "Port"]) -> None:
        """Set port associated to this switch.

        Args:
            self (Self): self
            ports (dict[int, Port]): ports.
        """
        self._ports = ports

    @property
    def fabric(self: Self) -> "Fabric":
        """Get associated fabric of this switch.

        Args:
            self (Self): self

        Returns:
            Fabric: fabric.
        """
        return self._fabric

    @fabric.setter
    def fabric(self: Self, fabric: "Fabric") -> None:
        """Get associated fabric of this switch.

        Args:
            self (Self): self
            fabric (Fabric): fabric to set

        Returns:
            Fabric: fabric.
        """
        self._fabric = fabric


class LeafSwitch(Switch):
    """Describe a leaf switch."""

    id: int


class FabricPool(BaseModel):
    """Representation of ip ressource pool used inside the fabric."""

    loopbacks: IPv4Network
    links: IPv4Network


class Port(BaseModel):
    """Representation of port."""

    iface: int = Field(alias="if")
    switch_str: tuple[int, int] = Field(alias="sw")
    _switch: tuple[Switch, Switch]
    template_str: str = Field(alias="tpl")
    _template: "InterfaceTemplate"
    description: str = Field(alias="desc")

    @field_validator("switch_str", mode="before")
    @classmethod
    def process_switch(cls, value: int | tuple) -> tuple[int, int]:
        """Transform switch str into a tuple.

        Args:
            value (dict): The input value for the switch field, expected to be a dictionary mapping string keys
                         to client data.

        Returns:
            list: The modified field.
        """
        if isinstance(value, int):
            return (value, value)
        return value

    @property
    def template(self: Self) -> "InterfaceTemplate":
        """Get interface template associated with this interface.

        Args:
            self (Self): self.

        Returns:
            InterfaceTemplate: template associated with these interface.
        """
        return self._template

    @template.setter
    def template(self: Self, template: "InterfaceTemplate") -> None:
        """Interface template setter.

        Args:
            self (Self): self
            template (InterfaceTemplate): interface template.
        """
        self._template = template

    @property
    def switch(self: Self) -> tuple[Switch, Switch]:
        """Get switch associated with interface.

        Args:
            self (Self): self

        Returns:
            tuple[Switch, Switch]: switch tuple, the same switch are on both position for individual port.
        """
        return self._switch

    @switch.setter
    def switch(self: Self, switch: tuple[Switch, Switch]) -> None:
        """Set switch associated with interface.

        Args:
            self (Self): self.
            switch (tuple[Switch, Switch]): switch.
        """
        self._switch = switch
        switch1, switch2 = switch
        switch1.ports[self.iface] = self
        switch2.ports[self.iface] = self


class Fabric(BaseModel):
    """Representation of an evpn fabric."""

    spines: list[Switch]
    lifs: list[LeafSwitch]
    pool: FabricPool
    site: str
    id: int
    ports: list[Port] = Field(default_factory=list)
    _leaf_index: dict[int, Switch]

    @model_validator(mode="after")
    def check_duplicate_ports(self: Self) -> Self:
        """Ensure that no two ports are declared on the same switch with the same iface.
        Each port is identified uniquely by (switch_name, iface), where switch_name is
        extracted from the first element of the port's switch_str.
        """  # noqa: D205
        checked_port: set[tuple[int, int]] = set()
        for port in self.ports:
            sw1, sw2 = port.switch_str
            porttuple1 = (sw1, port.iface)
            porttuple2 = (sw2, port.iface)
            if porttuple1 in checked_port:
                msg = f"{porttuple1} already defined"
                raise ValueError(msg)
            checked_port.add(porttuple1)
            if porttuple1 == porttuple2:
                continue
            if porttuple2 in checked_port:
                msg = f"{porttuple2} already defined"
                raise ValueError(msg)
        return self

    def resolve_switch(self: Self, templates: dict[str, "InterfaceTemplate"]) -> None:
        """Resolve switch for ports."""
        for port in self.ports:
            port.template = templates[port.template_str]
            self._leaf_index = {leaf.id: leaf for leaf in self.lifs}
            sw1, sw2 = port.switch_str
            port.switch = (self._leaf_index[sw1], self._leaf_index[sw2])
        for switch in self.lifs + self.spines:
            switch.fabric = self


class ClientNetwork(BaseModel):
    """List of client network."""

    name: str
    vlan_id: int
    subnet: IPv4Interface
    _client: "Client"

    @property
    def client(self: Self) -> "Client":
        """Get client.

        Args:
            self (Self): self

        Returns:
            Client: client
        """
        return self._client

    @client.setter
    def client(self: Self, client: "Client") -> None:
        """Set client.

        Args:
            self (Self): self
            client (Client): client to set./
        """
        self._client = client

    def network_name(self: Self) -> str:
        """Get network name."""
        return f"{self.client.name.upper()}_{self.name.upper()}"


class InterfaceKind(Enum):
    """Describe interface kind."""

    lag_appliance = "appliance"
    esx = "esx"


class Client(BaseModel):
    """Define client infrastructure."""

    id: int
    name: str
    networks: dict[str, ClientNetwork]

    @field_validator("networks", mode="before")
    @classmethod
    def process_network(cls, value: dict) -> dict:
        """Injects the network name into each ClientNetwork instance based on the dictionary key.

        If the input dictionary for the network field does not have a 'name' key in the client network data,
        this validator sets the 'name' key to the dictionary key.

        Args:
            value (dict): The input value for the network field, expected to be a dictionary mapping string keys
                         to network data.

        Returns:
            dict: The modified dictionary with the network name injected.
        """
        for net_name, net_data in value.items():
            net_data["name"] = net_name
        return value

    @model_validator(mode="after")
    def inject_client_reference(self: Self) -> Self:
        """Inject the parent's client name into each network."""
        for network in self.networks.values():
            network.client = self
        return self


class InterfaceTemplate(BaseModel):
    """Define templete for interface."""

    name: str
    type: InterfaceKind
    clients_str: list[str] = Field(alias="clients")
    _clients_obj: list[Client]

    @property
    def clients(self: Self) -> list[Client]:
        """Get client list.

        Args:
            self (Self): self

        Returns:
            list[str]: list of clients.
        """
        return self._clients_obj

    @clients.setter
    def clients(self: Self, clients: list[Client]) -> None:
        """Return list of clients.

        Args:
            self (Self): self
            clients (list[Client]): list of clients
        """
        self._clients_obj = clients


class Metamodel(BaseModel):
    """Define metamodel main class that store all config."""

    default: Default
    fabrics: list[Fabric] = Field(default_factory=list)
    clients: dict[str, Client] = Field(default_factory=dict)
    templates_list: list[InterfaceTemplate] = Field(default_factory=list, alias="templates")
    _templates: dict[str, InterfaceTemplate]

    @field_validator("clients", mode="before")
    @classmethod
    def process_client(cls, value: dict) -> dict:
        """Injects the client name into each Client instance based on the dictionary key.

        Args:
            value (dict): The input value for the client field, expected to be a dictionary mapping string keys
                         to client data.

        Returns:
            dict: The modified dictionary with the client name injected.
        """
        for client_name, client_data in value.items():
            client_data["name"] = client_name
        return value

    @model_validator(mode="after")
    def process_templates(self: Self) -> Self:
        """Resolve client str into client object.

        Args:
            self (Self): self.
        """
        self._templates = {template.name: template for template in self.templates_list}
        for template in self.templates_list:
            template.clients = [self.clients[client_str] for client_str in template.clients_str]
        for fabric in self.fabrics:
            fabric.resolve_switch(self.templates)
        return self

    @property
    def templates(self: Self) -> dict[str, InterfaceTemplate]:
        """Get template dict.

        Args:
            self (Self): self

        Returns:
            dict[str, InterfaceTemplate]: interface templates
        """
        return self._templates

    def propagate_default(self: Self) -> None:
        """Propagate default value.

        Args:
            self (Self): self
        """
        for fabric in self.fabrics:
            for leaf in fabric.lifs:
                leaf.username = self.default.username if not leaf.username else leaf.username
                leaf.password = self.default.password if not leaf.password else leaf.password
            for spine in fabric.spines:
                spine.username = self.default.username if not spine.username else spine.username
                spine.password = self.default.password if not spine.password else spine.password


def get_model(filename: str) -> Metamodel:
    """Parse model from filename.

    Args:
        filename (str): filmename to parse

    Returns:
        Metamodel: parsed metamodel
    """
    path = Path(filename)
    with path.open() as f:
        model = parse_yaml_raw_as(Metamodel, f)
        model.propagate_default()
        return model
