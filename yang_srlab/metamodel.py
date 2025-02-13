"""Define metamodel class used as source of preprocessing."""

from ipaddress import IPv4Address
from pathlib import Path

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_raw_as


class Switch(BaseModel):
    """Representation of switch config."""

    name: str
    address: IPv4Address


class Fabric(BaseModel):
    """Representation of an evpn fabric."""

    spines: list[Switch]
    lifs: list[Switch]
    site: str


class Metamodel(BaseModel):
    """Define metamodel main class that store all config."""

    fabrics: list[Fabric]


def get_model(filename: str) -> Metamodel:
    """Parse model from filename.

    Args:
        filename (str): filmename to parse

    Returns:
        Metamodel: parsed metamodel
    """
    path = Path(filename)
    with path.open() as f:
        return parse_yaml_raw_as(Metamodel, f)
