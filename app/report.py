import argparse

from app.database import PacketDatabase


def format_bytes(total_bytes: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]

    value = float(total_bytes)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"

            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{total_bytes} B"


def print_report(
    database: PacketDatabase,
    after_id: int = 0,
    title: str = "Traffic Analysis Report",
) -> None:
    total = database.count_packets(after_id=after_id)

    protocols = database.count_by_protocol(
        after_id=after_id
    )

    top_sources = database.top_source_ips(
        limit=5,
        after_id=after_id,
    )

    top_destinations = database.top_destination_ips(
        limit=5,
        after_id=after_id,
    )

    print(f"\n=== {title} ===\n")

    print(f"Total packets: {total}")

    print("\nPackets by protocol:")

    if protocols:
        for row in protocols:
            print(
                f"  {row['protocol']:<10} "
                f"{row['packet_count']:>8} packets "
                f"({format_bytes(row['total_bytes'])})"
            )
    else:
        print("  No packets found.")

    print("\nTop 5 source IPs by traffic volume:")

    if top_sources:
        for position, row in enumerate(
            top_sources,
            start=1,
        ):
            print(
                f"  {position}. "
                f"{row['source_ip']:<40} "
                f"{format_bytes(row['total_bytes']):>12} "
                f"({row['packet_count']} packets)"
            )
    else:
        print("  No packets found.")

    print("\nTop 5 destination IPs by traffic volume:")

    if top_destinations:
        for position, row in enumerate(
            top_destinations,
            start=1,
        ):
            print(
                f"  {position}. "
                f"{row['destination_ip']:<40} "
                f"{format_bytes(row['total_bytes']):>12} "
                f"({row['packet_count']} packets)"
            )
    else:
        print("  No packets found.")

    print()


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generate traffic statistics from "
            "the packet database."
        )
    )

    parser.add_argument(
        "--database",
        default="data/traffic.db",
        help=(
            "SQLite database path "
            "(default: data/traffic.db)."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    with PacketDatabase(args.database) as database:
        print_report(database)


if __name__ == "__main__":
    main()
