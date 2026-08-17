from app.capture import PacketRecord
from app.database import PacketDatabase


def test_database_initialization():
    database = PacketDatabase(":memory:")

    assert database.count_packets() == 0

    database.close()


def test_insert_packet():
    database = PacketDatabase(":memory:")

    packet = PacketRecord(
        source_ip="192.168.1.10",
        destination_ip="8.8.8.8",
        protocol="UDP",
        packet_size=128,
    )

    packet_id = database.insert_packet(packet)

    assert packet_id == 1
    assert database.count_packets() == 1

    database.close()


def test_persist_packet_fields():
    database = PacketDatabase(":memory:")

    packet = PacketRecord(
        source_ip="10.0.0.10",
        destination_ip="10.0.0.20",
        protocol="TCP",
        packet_size=512,
    )

    database.insert_packet(packet)

    rows = database.fetch_all_packets()

    assert len(rows) == 1

    stored_packet = rows[0]

    assert stored_packet["source_ip"] == "10.0.0.10"
    assert stored_packet["destination_ip"] == "10.0.0.20"
    assert stored_packet["protocol"] == "TCP"
    assert stored_packet["packet_size"] == 512
    assert stored_packet["captured_at"] is not None

    database.close()


def test_multiple_packets_are_persisted():
    database = PacketDatabase(":memory:")

    packets = [
        PacketRecord(
            source_ip="10.0.0.1",
            destination_ip="10.0.0.2",
            protocol="TCP",
            packet_size=100,
        ),
        PacketRecord(
            source_ip="10.0.0.3",
            destination_ip="10.0.0.4",
            protocol="UDP",
            packet_size=200,
        ),
        PacketRecord(
            source_ip="10.0.0.5",
            destination_ip="8.8.8.8",
            protocol="ICMP",
            packet_size=98,
        ),
    ]

    for packet in packets:
        database.insert_packet(packet)

    assert database.count_packets() == 3

    database.close()


def test_count_by_protocol():
    database = PacketDatabase(":memory:")

    packets = [
        PacketRecord("10.0.0.1", "10.0.0.2", "TCP", 100),
        PacketRecord("10.0.0.1", "10.0.0.3", "TCP", 200),
        PacketRecord("10.0.0.2", "10.0.0.3", "UDP", 300),
        PacketRecord("10.0.0.3", "10.0.0.1", "ICMP", 80),
    ]

    for packet in packets:
        database.insert_packet(packet)

    results = database.count_by_protocol()

    assert [
        (row["protocol"], row["packet_count"])
        for row in results
    ] == [
        ("TCP", 2),
        ("ICMP", 1),
        ("UDP", 1),
    ]

    database.close()


def test_top_source_ips():
    database = PacketDatabase(":memory:")

    packets = [
        PacketRecord("10.0.0.1", "8.8.8.8", "TCP", 100),
        PacketRecord("10.0.0.1", "8.8.8.8", "TCP", 100),
        PacketRecord("10.0.0.1", "1.1.1.1", "UDP", 100),
        PacketRecord("10.0.0.2", "8.8.8.8", "TCP", 100),
        PacketRecord("10.0.0.2", "1.1.1.1", "UDP", 100),
        PacketRecord("10.0.0.3", "8.8.8.8", "TCP", 100),
    ]

    for packet in packets:
        database.insert_packet(packet)

    results = database.top_source_ips(limit=2)

    assert len(results) == 2

    assert results[0]["source_ip"] == "10.0.0.1"
    assert results[0]["packet_count"] == 3

    assert results[1]["source_ip"] == "10.0.0.2"
    assert results[1]["packet_count"] == 2

    database.close()


def test_top_destination_ips():
    database = PacketDatabase(":memory:")

    packets = [
        PacketRecord("10.0.0.1", "8.8.8.8", "TCP", 100),
        PacketRecord("10.0.0.2", "8.8.8.8", "TCP", 100),
        PacketRecord("10.0.0.3", "8.8.8.8", "UDP", 100),
        PacketRecord("10.0.0.1", "1.1.1.1", "UDP", 100),
        PacketRecord("10.0.0.2", "1.1.1.1", "UDP", 100),
        PacketRecord("10.0.0.3", "9.9.9.9", "ICMP", 100),
    ]

    for packet in packets:
        database.insert_packet(packet)

    results = database.top_destination_ips(limit=2)

    assert len(results) == 2

    assert results[0]["destination_ip"] == "8.8.8.8"
    assert results[0]["packet_count"] == 3

    assert results[1]["destination_ip"] == "1.1.1.1"
    assert results[1]["packet_count"] == 2

    database.close()
