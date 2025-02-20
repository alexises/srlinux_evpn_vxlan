"""Define decorator for templates."""

import importlib
import pkgutil
from collections.abc import Callable

from .container import ComputeContainer

_template_functions: dict[str, list[Callable[[ComputeContainer], None]]] = {}


def template_group(
    group: str,
) -> Callable[[Callable[[ComputeContainer], None]], Callable[[ComputeContainer], None]]:
    """Store a template into a template group stack.

    Args:
        group (str): group associated with this template.
    """

    def _decorator(func: Callable[[ComputeContainer], None]) -> Callable[[ComputeContainer], None]:
        if group not in _template_functions:
            _template_functions[group] = []
        _template_functions[group].append(func)
        return func

    return _decorator


def get_func_from_group(group: str) -> list[Callable[[ComputeContainer], None]]:
    """Get list of templating function from groups.

    Args:
        group (str): group to check.

    Returns:
        list[Callable[[ComputeContainer], None]]: list of groups.
    """
    return _template_functions.get(group, [])


def scan(package_name: str) -> None:
    """Scan modules for decorator.

    Args:
        package_name (str): package to scan
    """
    package = importlib.import_module(package_name)
    for _loader, module_name, _is_pkg in pkgutil.walk_packages(
        package.__path__,
        package.__name__ + ".",
    ):
        importlib.import_module(module_name)
