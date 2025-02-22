"""Define decorator for templates."""

import importlib
import pkgutil
from collections.abc import Callable

from yang_srlab.yang_model.interface import YangInterafece

# Use the concrete type instead of a generic type variable.
_yang_template_functions: dict[str, list[Callable[[YangInterafece], None]]] = {}


def template_group(
    group: str,
) -> Callable[[Callable[[YangInterafece], None]], Callable[[YangInterafece], None]]:
    """Store a template into a template group stack.

    Args:
        group (str): group associated with this template.
    """

    def _decorator(func: Callable[[YangInterafece], None]) -> Callable[[YangInterafece], None]:
        if group not in _yang_template_functions:
            _yang_template_functions[group] = []
        _yang_template_functions[group].append(func)
        return func

    return _decorator


def get_yang_func_from_group(group: str) -> list[Callable[[YangInterafece], None]]:
    """Get list of templating function from groups.

    Args:
        group (str): group to check.

    Returns:
        list[Callable[[YangInterafece], None]]: list of functions.
    """
    return _yang_template_functions.get(group, [])


def scan_yang(package_name: str) -> None:
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
