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


def _cleanup_candidate_config(diff: str) -> str:
    return (
        diff.replace("srl_nokia-interfaces-ip-dhcp:", "")
        .replace("srl_nokia-interfaces:", "")
        .replace("srl_nokia-network-instance:", "")
        .replace("srl_nokia-linux:", "")
        .replace("srl_nokia-ospf:", "")
        .replace("srl_nokia-bgp:", "")
        .replace("srl_nokia-tunnel-interfaces:", "")
        .replace("srl_nokia-interfaces-vlans:", "")
        .replace("srl_nokia-bgp-evpn:", "")
        .replace("srl_nokia-routing-policy:", "")
        .replace("srl_nokia-system-network-instance:", "")
        .replace("srl_nokia-aaa:", "")
        .replace("srl_nokia-ssh:", "")
        .replace("srl_nokia-snmp:", "")
        .replace("srl_nokia-logging:", "")
        .replace("srl_nokia-tls:", "")
        .replace("srl_nokia-system-banner:", "")
        .replace("srl_nokia-json-rpc:", "")
        .replace("srl_nokia-netconf-server:", "")
        .replace("srl_nokia-system-network-instance-bgp-evpn-ethernet-segments:", "")
        .replace("srl_nokia-dns:", "")
        .replace("srl_nokia-grpc:", "")
        .replace("srl_nokia-system:", "")
        .replace("srl_nokia-acl:", "")
        .replace("srl_nokia-openconfig:", "")
        .replace("srl_nokia-system-network-instance-bgp-vpn:", "")
    )


def _build_srclient(switch: Switch) -> SRClient:
    return SRClient(str(switch.address), switch.username, switch.password)


class SwitchStorage:
    """Store switch configuration and perform transformation on candidate configuration."""

    def __init__(self: Self, switch: Switch, config: dict) -> None:
        """Constructor.

        Args:
            self (Self): self
            switch (Switch): switch object
            config (dict): target config
        """
        self._switch = switch
        self._base_config = config
        self._config: dict = {}

    def add_base_config(self: Self, base_config: dict) -> None:
        """Add base config of the switch.

        Args:
            self (Self): self
            base_config (dict): base config collected from the switch.
        """
        self._config = base_config

    @property
    def base_config(self: Self) -> str:
        """Get base configuration suitable for config printing.

        Args:
            self (Self): self

        Returns:
            dict: base config
        """
        return _cleanup_candidate_config(dumps(self._base_config, indent=2))

    @property
    def switch(self: Self) -> Switch:
        """Get switch associated with storage.

        Args:
            self (Self): self

        Returns:
            Switch: switch associated with storage
        """
        return self._switch

    @property
    def merged_config(self: Self) -> dict:
        """Get merged config.

        Args:
            self (Self): _description_

        Returns:
            dict: _description_
        """
        return {**self._config, **self._base_config}


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
        self._switchs: list[SwitchStorage] = []
        self._with_diff = with_diff
        self._with_config_print = with_config_print
        self._with_commit = with_commit
        self._console = console

        for switch, config in switchs:
            self._switchs.append(SwitchStorage(switch, config))

    def collect_running_config(self: Self) -> None:
        """Collect and inject running config into switch storage.

        Args:
            self (Self): self
        """
        self._console.log("Collect running config", style="bold yellow")
        for sw_sto in self._switchs:
            client = _build_srclient(sw_sto.switch)
            sw_sto.add_base_config(client.get_running_config("/"))

    def print_config(self: Self) -> None:
        """Print configuration that will be pushed.

        Args:
            self (Self): self.
        """
        self._console.log("Print configuration", style="bold yellow")
        for sw_sto in self._switchs:
            syntax = Syntax(
                sw_sto.base_config,
                "json",
                theme="monokai",
                line_numbers=True,
            )
            panel = Panel(syntax, title=f"Switch : {sw_sto.switch.name}", title_align="center")
            self._console.print(panel)

    def generate_diff(self: Self) -> None:
        """Print diff from running config.

        Args:
            self (Self): self
        """
        self._console.log("Print diff ", style="bold yellow")
        for sw_sto in self._switchs:
            client = _build_srclient(sw_sto.switch)
            diff_data = client.diff("/", sw_sto.merged_config)
            if "result" not in diff_data:
                self._console.print(diff_data)
            elif len(diff_data["result"]) > 0:
                syntax = Syntax(diff_data["result"][0], "diff", theme="monokai", line_numbers=True)
                panel = Panel(syntax, title=f"Switch : {sw_sto.switch.name}", title_align="center")
                self._console.print(panel)
            else:
                self._console.log(f"no diff for {sw_sto.switch.name}", style="green")

    def valitate_config(self: Self) -> bool:
        """Validate configuration before commiting it.

        Args:
            self (Self): self
        Return:
            bool: true if all config are validated successfully. false otherwise.
        """
        self._console.log("validate ", style="bold yellow")
        for sw_sto in self._switchs:
            client = _build_srclient(sw_sto.switch)
            validate_info = client.validate("/", sw_sto.merged_config)
            if "error" in validate_info:
                self._console.log(
                    f"Switch {sw_sto.switch.name} failed : {validate_info["error"]["message"]}",
                    style="red",
                )
                return False
            self._console.log(
                f"Switch {sw_sto.switch.name} successfully validated",
                style="green",
            )
        return True

    def commit_config(self: Self) -> None:
        """Commit configuration the switch.

        Args:
            self (Self): self
        """
        self._console.log("commit ", style="bold yellow")
        for sw_sto in self._switchs:
            client = _build_srclient(sw_sto.switch)
            validate_info = client.commit("/", sw_sto.merged_config)
            if "result" not in validate_info:
                self._console.log(validate_info, style="red")
                continue
            result = validate_info["result"][0]
            if result == {}:
                self._console.log(
                    f"Switch {sw_sto.switch.name} successfully commited",
                    style="green",
                )
            else:
                self._console.log(f"Switch {sw_sto.switch.name} failed : {result}")

    def run(self: Self) -> None:
        """Run configuration.

        Args:
            self (Self): self.
        """
        if self._with_diff:
            self.collect_running_config()
        if self._with_config_print:
            self.print_config()
        if self._with_diff:
            self.generate_diff()
        validation_status = self.valitate_config()
        if not validation_status:
            self._console.log("Exit due to validation error", style="red")
            return
        if self._with_commit:
            self.commit_config()
