from dataclasses import dataclass
from typing import Optional

from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.inet6 import IPv6, ICMPv6EchoRequest, ICMPv6EchoReply
from scapy.packet import Packet


@dataclass(frozen=True)
class PacketRecord:
    source_ip: str
    destination_ip: str
    protocol: str
    packet_size: int


def _get_protocol_name(packet: Packet) -> str:
    if TCP in packet:
        return "TCP"

    if UDP in packet:
        return "UDP"

    if ICMP in packet:
        return "ICMP"

    if ICMPv6EchoRequest in packet or ICMPv6EchoReply in packet:
        return "ICMPv6"

    if IP in packet:
        return f"IP-{packet[IP].proto}"

    if IPv6 in packet:
        return f"IPv6-{packet[IPv6].nh}"

    return "UNKNOWN"


def normalize_packet(packet: Packet) -> Optional[PacketRecord]:
    if IP in packet:
        source_ip = packet[IP].src
        destination_ip = packet[IP].dst

    elif IPv6 in packet:
        source_ip = packet[IPv6].src
        destination_ip = packet[IPv6].dst

    else:
        return None

    return PacketRecord(
        source_ip=source_ip,
        destination_ip=destination_ip,
        protocol=_get_protocol_name(packet),
        packet_size=len(packet),
    )
