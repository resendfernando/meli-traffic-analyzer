import argparse

from app.database import PacketDatabase


def print_report(database_path: str) -> None:
    with PacketDatabase(database_path) as database:
        total = database.count_packets()
        protocols = database.count_by_protocol()
        top_sources = database.top_source_ips()
        top_destinations = database.top_destination_ips()

    print("\n=== Traffic Analysis Report ===\n")

    print(f"Total packets: {total}")

    print("\nPackets by protocol:")
    if protocols:
        for row in protocols:
            print(
                f"  {row['protocol']:<10} "
                f"{row['packet_count']:>8}"
            )
    else:
        print("  No packets found.")

    print("\nTop 5 source IPs:")
    if top_sources:
        for position, row in enumerate(top_sources, start=1):
            print(
                f"  {position}. "
                f"{row['source_ip']:<40} "
                f"{row['packet_count']:>8}"
            )
    else:
        print("  No packets found.")

    print("\nTop 5 destination IPs:")
    if top_destinations:
        for position, row in enumerate(
            top_destinations,
            start=1,
        ):
            print(
                f"  {position}. "
                f"{row['destination_ip']:<40} "
                f"{row['packet_count']:>8}"
            )
    else:
        print("  No packets found.")

    print()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate traffic statistics from the packet database."
    )

    parser.add_argument(
        "--database",
        default="data/traffic.db",
        help="SQLite database path (default: data/traffic.db).",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    print_report(args.database)


if __name__ == "__main__":
    main()
