import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.capture import PacketRecord


SCHEMA = """
CREATE TABLE IF NOT EXISTS packets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    source_ip TEXT NOT NULL,
    destination_ip TEXT NOT NULL,
    protocol TEXT NOT NULL,
    packet_size INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_packets_protocol
ON packets(protocol);

CREATE INDEX IF NOT EXISTS idx_packets_source_ip
ON packets(source_ip);

CREATE INDEX IF NOT EXISTS idx_packets_destination_ip
ON packets(destination_ip);
"""


class PacketDatabase:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._ensure_parent_directory()

        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row

        self.initialize_schema()

    def _ensure_parent_directory(self) -> None:
        if self.database_path == ":memory:":
            return

        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)

    def initialize_schema(self) -> None:
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def insert_packet(self, packet: PacketRecord) -> int:
        captured_at = datetime.now(timezone.utc).isoformat()

        cursor = self.connection.execute(
            """
            INSERT INTO packets (
                captured_at,
                source_ip,
                destination_ip,
                protocol,
                packet_size
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                captured_at,
                packet.source_ip,
                packet.destination_ip,
                packet.protocol,
                packet.packet_size,
            ),
        )

        self.connection.commit()

        return cursor.lastrowid

    def count_packets(self) -> int:
        cursor = self.connection.execute(
            "SELECT COUNT(*) AS total FROM packets"
        )

        row = cursor.fetchone()

        return row["total"]

    def count_by_protocol(self) -> list[sqlite3.Row]:
        cursor = self.connection.execute(
            """
            SELECT
                protocol,
                COUNT(*) AS packet_count
            FROM packets
            GROUP BY protocol
            ORDER BY packet_count DESC, protocol ASC
            """
        )

        return cursor.fetchall()

    def top_source_ips(self, limit: int = 5) -> list[sqlite3.Row]:
        cursor = self.connection.execute(
            """
            SELECT
                source_ip,
                COUNT(*) AS packet_count
            FROM packets
            GROUP BY source_ip
            ORDER BY packet_count DESC, source_ip ASC
            LIMIT ?
            """,
            (limit,),
        )

        return cursor.fetchall()

    def top_destination_ips(self, limit: int = 5) -> list[sqlite3.Row]:
        cursor = self.connection.execute(
            """
            SELECT
                destination_ip,
                COUNT(*) AS packet_count
            FROM packets
            GROUP BY destination_ip
            ORDER BY packet_count DESC, destination_ip ASC
            LIMIT ?
            """,
            (limit,),
        )

        return cursor.fetchall()

    def fetch_all_packets(self) -> list[sqlite3.Row]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                captured_at,
                source_ip,
                destination_ip,
                protocol,
                packet_size
            FROM packets
            ORDER BY id
            """
        )

        return cursor.fetchall()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
