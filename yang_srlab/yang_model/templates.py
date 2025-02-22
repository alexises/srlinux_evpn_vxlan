"""Define decorator for templates."""

import importlib
import pkgutil
from collections.abc import Callable
from typing import Generic, Self, TypeVar

from yang_srlab.yang_model.interface import YangInterafece

T = TypeVar("T", bound=YangInterafece)


class TemplateGroup(Generic[T]):
    """Define template group."""

    def __init__(self: Self) -> None:
        """Init.

        Args:
            self (Self): self.
        """
        self.functions: list[Callable[[T], None]] = []

    def register(self: Self, func: Callable[[T], None]) -> Callable[[T], None]:
        """Register callback.

        Args:
            func (Callable[[T], None]): function.

        Returns:
            Callable[[T], None]: callback
        """
        self.functions.append(func)
        return func

    def run(self: Self, instance: T) -> None:
        """Run functions.

        Args:
            instance (T): _description_
        """
        for func in self.functions:
            func(instance)

    def scan(self: Self, package_name: str) -> None:
        """Scan module for decorator.

        Args:
            self (Self): self
            package_name (str): package to scan
        """
        package = importlib.import_module(package_name)
        for _loader, module_name, _is_pkg in pkgutil.walk_packages(
            package.__path__,
            package.__name__ + ".",
        ):
            importlib.import_module(module_name)
