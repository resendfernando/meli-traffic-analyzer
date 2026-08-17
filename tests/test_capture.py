from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import ARP
from scapy.packet import Raw

from app.capture import normalize_packet


def test_normalize_ipv4_tcp_packet():
    packet = (
        IP(src="10.0.0.10", dst="10.0.0.20")
        / TCP(sport=12345, dport=443)
        / Raw(b"test")
    )

    result = normalize_packet(packet)

    assert result is not None
    assert result.source_ip == "10.0.0.10"
    assert result.destination_ip == "10.0.0.20"
    assert result.protocol == "TCP"
    assert result.packet_size == len(packet)


def test_normalize_ipv4_udp_packet():
    packet = IP(src="192.168.1.10", dst="8.8.8.8") / UDP(dport=53)

    result = normalize_packet(packet)

    assert result is not None
    assert result.protocol == "UDP"


def test_normalize_icmp_packet():
    packet = IP(src="192.168.1.10", dst="8.8.8.8") / ICMP()

    result = normalize_packet(packet)

    assert result is not None
    assert result.protocol == "ICMP"


def test_normalize_ipv6_packet():
    packet = IPv6(src="2001:db8::1", dst="2001:db8::2") / TCP(dport=443)

    result = normalize_packet(packet)

    assert result is not None
    assert result.source_ip == "2001:db8::1"
    assert result.destination_ip == "2001:db8::2"
    assert result.protocol == "TCP"


def test_ignore_non_ip_packet():
    packet = ARP(psrc="192.168.1.10", pdst="192.168.1.1")

    assert normalize_packet(packet) is None
