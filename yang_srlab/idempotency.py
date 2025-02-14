"""This module will manage idempotency on netflow config propagation.

This module provides :
* autotoritative config management print
* validation of target configuration
* diff of target configuration, and print into user readable format
* push configuration
"""

from json import dumps
from typing import Self

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .metamodel import Switch
from .yang import SRClient


def _cleanup_diff(diff: str) -> str:
    return diff.replace("srl_nokia-interfaces-ip-dhcp:", "").replace("srl_nokia-interfaces:", "")


class IdempotencyManager:
    """Manage idempotency flow of checking and commiting configuration on the switch."""

    def __init__(
        self: Self,
        switchs: list[tuple[Switch, dict]],
        console: Console,
        *,
        with_config_print: bool = False,
        with_diff: bool = True,
        with_commit: bool = False,
    ) -> None:
        """Constructor.

        Args:
            self (Self): Self
            switchs (dict[Switch, dict]): switch to process with their model
            console (Console): rich console object used for printing
            with_config_print (bool, optional): print config Defaults to False.
            with_diff (bool, optional): generate diff Defaults to True.
            with_commit (bool, optional): commit configuration. Defaults to False.
        """
        self._switchs = switchs
        self._with_diff = with_diff
        self._with_config_print = with_config_print
        self._with_commit = with_commit
        self._console = console

    def print_config(self: Self) -> None:
        """Print configuration that will be pushed.

        Args:
            self (Self): self.
        """
        self._console.log("Print configuration", style="bold yellow")
        for switch, data in self._switchs:
            syntax = Syntax(
                _cleanup_diff(dumps(data, indent=2)),
                "json",
                theme="monokai",
                line_numbers=True,
            )
            panel = Panel(syntax, title=f"Switch : {switch.name}", title_align="center")
            self._console.print(panel)

    def generate_diff(self: Self) -> None:
        """Print diff from running config.

        Args:
            self (Self): self
        """
        self._console.log("Print diff ", style="bold yellow")
        for switch, data in self._switchs:
            client = SRClient(str(switch.address), switch.username, switch.password)
            diff_data = client.diff("/interface[name=*]", data["srl_nokia-interfaces:interface"])
            if "result" in diff_data:
                syntax = Syntax(diff_data["result"][0], "diff", theme="monokai", line_numbers=True)
                panel = Panel(syntax, title=f"Switch : {switch.name}", title_align="center")
                self._console.print(panel)
            else:
                self._console.print(diff_data)

    def run(self: Self) -> None:
        """Run configuration.

        Args:
            self (Self): self.
        """
        if self._with_config_print:
            self.print_config()
        if self._with_diff:
            self.generate_diff()
