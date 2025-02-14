"""Define metamodel class used as source of preprocessing."""

from ipaddress import IPv4Address
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field
from pydantic_yaml import parse_yaml_raw_as


class Default(BaseModel):
    """Describe default option for configuration."""

    username: str = ""
    password: str = ""


class Switch(BaseModel):
    """Representation of switch config."""

    name: str
    address: IPv4Address
    username: str = Field(default="")
    password: str = Field(default="")


class Fabric(BaseModel):
    """Representation of an evpn fabric."""

    spines: list[Switch]
    lifs: list[Switch]
    site: str


class Metamodel(BaseModel):
    """Define metamodel main class that store all config."""

    default: Default
    fabrics: list[Fabric]

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
