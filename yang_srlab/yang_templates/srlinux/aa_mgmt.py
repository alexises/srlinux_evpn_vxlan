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
                password="$y$j9T$f/fNdwO8wCAHXmDGetrrE/$drOi8I6XEm316yo4l6tdGCdhotA8Brw2M6.98OV8mC1",  # noqa: S106
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
            port=830,
            disable_shell=True,
        ),
    ]


@srlinux_template
def lldp_config(node: SRLinuxYang) -> None:
    """Define lldp config."""
    nsys = cast(sys.SystemContainer, node.system.system)
    nsys.lldp = sys.LldpContainer(admin_state=sys.EnumerationEnum2.enable)


@srlinux_template
def grpc(node: SRLinuxYang) -> None:
    """Define grpc server.

    Args:
        node (SRLinuxYang): grpc
    """
    nsys = cast(sys.SystemContainer, node.system.system)
    nsys.grpc_server = [
        sys.GrpcServerListEntry(
            name="eda-discovery",
            admin_state=sys.EnumerationEnum2.enable,
            rate_limit=65535,
            session_limit=1024,
            metadata_authentication=True,
            default_tls_profile=True,
            port=50052,
            services=["gnmi", "gnsi"],
        ),
        sys.GrpcServerListEntry(
            name="eda-insecure-mgmt",
            admin_state=sys.EnumerationEnum2.enable,
            rate_limit=65535,
            session_limit=1024,
            metadata_authentication=True,
            port=57411,
            services=["gnmi", "gnoi", "gnsi"],
        ),
        sys.GrpcServerListEntry(
            name="eda-mgmt",
            admin_state=sys.EnumerationEnum2.enable,
            rate_limit=65535,
            session_limit=1024,
            metadata_authentication=True,
            port=57410,
            tls_profile="EDA",
            services=["gnmi", "gnoi", "gnsi"],
        ),
        sys.GrpcServerListEntry(
            name="insecure-mgmt",
            admin_state=sys.EnumerationEnum2.enable,
            rate_limit=65000,
            port=57401,
            trace_options=[
                sys.EnumerationEnum14.request,
                sys.EnumerationEnum14.response,
                sys.EnumerationEnum14.common,
            ],
            services=["gnmi", "gnoi", "gnsi", "gribi", "p4rt"],
            unix_socket=sys.UnixSocketContainer(admin_state=sys.EnumerationEnum2.enable),
        ),
        sys.GrpcServerListEntry(
            name="mgmt",
            admin_state=sys.EnumerationEnum2.enable,
            rate_limit=65000,
            tls_profile="clab-profile",
            trace_options=[
                sys.EnumerationEnum14.request,
                sys.EnumerationEnum14.response,
                sys.EnumerationEnum14.common,
            ],
            services=["gnmi", "gnoi", "gnsi", "gribi", "p4rt"],
            unix_socket=sys.UnixSocketContainer(admin_state=sys.EnumerationEnum2.enable),
        ),
    ]


@srlinux_template
def json_rpc(node: SRLinuxYang) -> None:
    """Configure json_rpc api.

    Args:
        node (SRLinuxYang): node
    """
    nsys = cast(sys.SystemContainer, node.system.system)
    nsys.json_rpc_server = sys.JsonRpcServerContainer(
        admin_state=sys.EnumerationEnum2.enable,
        network_instance=[
            sys.NetworkInstanceListEntry3(
                name="mgmt",
                http=sys.HttpContainer(admin_state=sys.EnumerationEnum2.enable),
                https=sys.HttpsContainer(
                    admin_state=sys.EnumerationEnum2.enable,
                    tls_profile="clab-profile",
                ),
            ),
        ],
    )


@srlinux_template
def dns(node: SRLinuxYang) -> None:
    """Define dns config.

    Args:
        node (SRLinuxYang): self
    """
    nsys = cast(sys.SystemContainer, node.system.system)
    nsys.dns = sys.DnsContainer(server_list=[sys.Ipv4AddressType("192.168.1.254")])


@srlinux_template
def banner(node: SRLinuxYang) -> None:
    """Define banner."""
    nsys = cast(sys.SystemContainer, node.system.system)
    login_banner = """................................................................
:                  Welcome to Nokia SR Linux!                  :
:              Open Network OS for the NetOps era.             :
:                                                              :
:    This is a freely distributed official container image.    :
:                      Use it - Share it                       :
:                                                              :
: Get started: https://learn.srlinux.dev                       :
: Container:   https://go.srlinux.dev/container-image          :
: Docs:        https://doc.srlinux.dev/24-10                   :
: Rel. notes:  https://doc.srlinux.dev/rn24-10-2               :
: YANG:        https://yang.srlinux.dev/v24.10.2               :
: Discord:     https://go.srlinux.dev/discord                  :
: Contact:     https://go.srlinux.dev/contact-sales            :
................................................................
"""
    nsys.banner = sys.BannerContainer(login_banner=login_banner)


@srlinux_template
def netconf_server(node: SRLinuxYang) -> None:
    """Define netconf server."""
    nsys = cast(sys.SystemContainer, node.system.system)
    nsys.netconf_server = [
        sys.NetconfServerListEntry(
            name="mgmt",
            admin_state=sys.EnumerationEnum2.enable,
        ),
    ]
