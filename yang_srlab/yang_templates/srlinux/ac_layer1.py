"""Define layer 1 operations."""

from typing import cast

import pydantic_srlinux.models.system as sys

from yang_srlab.yang_model.srlinux import SRLinuxYang, srlinux_template


@srlinux_template
def evpn_type_1(model: SRLinuxYang) -> None:
    """Define type 1 evpn routes.

    Args:
        model (SRLinuxYang): model.
    """
    nsys = cast(sys.SystemContainer, model.system.system)
    nsys.network_instance = sys.NetworkInstanceContainer2()
    ne = nsys.network_instance
    ne.protocols = sys.ProtocolsContainer2()
    ne.protocols.evpn = sys.EvpnContainer3()
    ne.protocols.evpn.ethernet_segments = sys.EthernetSegmentsContainer()
    ne.protocols.evpn.ethernet_segments.bgp_instance = [sys.BgpInstanceListEntry2(id=1)]
    ne.protocols.evpn.ethernet_segments.bgp_instance[0].ethernet_segment = []
    segments = ne.protocols.evpn.ethernet_segments.bgp_instance[0].ethernet_segment
    for lag_id in model.sw.interfaces.lags:
        segment = sys.EthernetSegmentListEntry(
            name=f"lag{lag_id}",
            admin_state=sys.EnumerationEnum2.enable,
            interface_association=sys.Layer2InterfaceCase(
                interface=[sys.InterfaceListEntry2(ethernet_interface=f"lag{lag_id}")],
            ),
            multi_homing_mode=sys.EnumerationEnum33.all_active,
            esi=f"{model.sw.system_id}:42:42:{lag_id // 255:02x}:{lag_id % 255:02x}",
        )
        segments.append(segment)


@srlinux_template
def bgp_vpn(model: SRLinuxYang) -> None:
    """Define bgp vpn.

    Args:
        model (SRLinuxYang): model.
    """
    nsys = cast(sys.SystemContainer, model.system.system)
    nei = cast(sys.NetworkInstanceContainer2, nsys.network_instance)
    protos = cast(sys.ProtocolsContainer2, nei.protocols)
    protos.bgp_vpn = sys.BgpVpnContainer()
    protos.bgp_vpn.bgp_instance = [sys.BgpInstanceListEntry3(id=1)]
