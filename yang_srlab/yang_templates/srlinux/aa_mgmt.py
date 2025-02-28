"""Define system operations."""

from typing import cast

import pydantic_srlinux.models.system as sys

from yang_srlab.yang_model.srlinux import SRLinuxYang, srlinux_template


@srlinux_template
def openconfig(node: SRLinuxYang) -> None:
    """Define openconfig node."""
    node.system.system = sys.SystemContainer()
    nsys = node.system.system
    nsys.management = sys.ManagementContainer()
    nsys.management.openconfig = sys.OpenconfigContainer(admin_state=sys.EnumerationEnum2.enable)


@srlinux_template
def controle_plane_traffic(node: SRLinuxYang) -> None:
    """Define controle plane traffic."""
    nsys = cast(sys.SystemContainer, node.system.system)
    nsys.control_plane_traffic = sys.ControlPlaneTrafficContainer(
        input=sys.InputContainer(
            acl=sys.AclContainer(
                acl_filter=[
                    sys.AclFilterListEntry(name="cpm", type=sys.EnumerationEnum5.ipv4),
                    sys.AclFilterListEntry(name="cpm", type=sys.EnumerationEnum5.ipv6),
                ],
            ),
        ),
    )


@srlinux_template
def aaa(node: SRLinuxYang) -> None:
    """Define AAA config.

    Args:
        node (SRLinuxYang): node
    """
    nsys = cast(sys.SystemContainer, node.system.system)
    nsys.aaa = sys.AaaContainer(
        authentication=sys.AuthenticationContainer(
            idle_timeout=24 * 60 * 60,
            authentication_method=[sys.AuthenticationMethodLeafList("local")],
            admin_user=sys.AdminUserContainer(ssh_key=node.sw.ssh_keys),
            linuxadmin_user=sys.LinuxadminUserContainer(
                password="$y$j9T$f/fNdwO8wCAHXmDGetrrE/$drOi8I6XEm316yo4l6tdGCdhotA8Brw2M6.98OV8mC1",
                ssh_key=node.sw.ssh_keys,
            ),
        ),
        server_group=[sys.ServerGroupListEntry(name="local", type="local")],
    )


@srlinux_template
def ssh_server(node: SRLinuxYang) -> None:
    """Define ssh server conf."""
    nsys = cast(sys.SystemContainer, node.system.system)
    nsys.ssh_server = [
        sys.SshServerListEntry(
            name="mgmt",
            admin_state=sys.EnumerationEnum2.enable,
            use_credentialz=True,
        ),
        sys.SshServerListEntry(
            name="mgmt-netconf",
            admin_state=sys.EnumerationEnum2.enable,
            use_credentialz=True,
            port=830,
            disable_shell=True,
        ),
    ]
