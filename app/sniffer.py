import argparse
import sys

from scapy.all import conf, get_if_list, sniff

from app.capture import normalize_packet
from app.database import PacketDatabase
from app.report import print_report


def positive_int(value: str) -> int:
    """
    Parse a command-line argument that must be a positive integer.
    """
    try:
        parsed_value = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "value must be a positive integer"
        ) from exc

    if parsed_value <= 0:
        raise argparse.ArgumentTypeError(
            "value must be greater than zero"
        )

    return parsed_value


def get_available_interfaces() -> list[str]:
    return get_if_list()


def detect_interface() -> str:
    """
    Automatically select a network interface.

    The preferred strategy is to use the interface associated with the
    default IPv4 route. If that is not available, fall back to the first
    non-loopback interface that does not look like a common container or
    virtual bridge interface.
    """

    available_interfaces = get_available_interfaces()

    try:
        route_interface = conf.route.route("8.8.8.8")[0]

        if (
            route_interface
            and route_interface in available_interfaces
            and route_interface != "lo"
        ):
            return route_interface

    except Exception:
        pass

    ignored_prefixes = (
        "lo",
        "docker",
        "br-",
        "veth",
    )

    candidates = [
        interface
        for interface in available_interfaces
        if not interface.startswith(ignored_prefixes)
    ]

    if candidates:
        return candidates[0]

    print(
        "\nERROR: No suitable network interface "
        "could be detected automatically.\n",
        file=sys.stderr,
    )

    print(
        "Available interfaces:",
        file=sys.stderr,
    )

    for interface in available_interfaces:
        print(
            f"  - {interface}",
            file=sys.stderr,
        )

    print(
        "\nSpecify an interface explicitly using "
        "--interface.",
        file=sys.stderr,
    )

    raise SystemExit(2)


def validate_interface(interface: str) -> None:
    available_interfaces = get_available_interfaces()

    if interface not in available_interfaces:
        print(
            f"\nERROR: Interface '{interface}' "
            "was not found.\n",
            file=sys.stderr,
        )

        print(
            "Available interfaces:",
            file=sys.stderr,
        )

        for available_interface in available_interfaces:
            print(
                f"  - {available_interface}",
                file=sys.stderr,
            )

        print(
            "\nUse --help for usage information.",
            file=sys.stderr,
        )

        raise SystemExit(2)


def capture(
    interface: str,
    database_path: str,
    count: int | None = None,
    duration: int | None = None,
    verbose: bool = False,
) -> None:
    validate_interface(interface)

    database = PacketDatabase(database_path)

    start_id = database.get_last_packet_id()
    captured_packets = 0

    def handle_packet(packet):
        nonlocal captured_packets

        record = normalize_packet(packet)

        if record is None:
            return

        database.insert_packet(record)
        captured_packets += 1

        if verbose:
            print(record)

    try:
        if duration is not None:
            print(
                f"Capturing IP traffic on "
                f"'{interface}' for {duration} seconds..."
            )
        else:
            print(
                f"Capturing {count} IP packets "
                f"on interface '{interface}'..."
            )

        print(f"Database: {database_path}")

        if verbose:
            print("Verbose packet output: enabled")

        print()

        sniff(
            iface=interface,
            prn=handle_packet,
            store=False,
            count=count or 0,
            timeout=duration,
            filter="ip or ip6",
        )

    finally:
        stored_this_run = database.count_packets(
            after_id=start_id
        )

        print("\nCapture finished.")
        print(
            "Packets captured this run: "
            f"{captured_packets}"
        )
        print(
            "Packets stored this run: "
            f"{stored_this_run}"
        )

        print_report(
            database=database,
            after_id=start_id,
            title="Current Capture Summary",
        )

        database.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Capture, persist and analyze "
            "IP network traffic."
        )
    )

    parser.add_argument(
        "--interface",
        required=False,
        help=(
            "Network interface used for packet capture. "
            "If omitted, the application attempts to "
            "detect the interface automatically."
        ),
    )

    parser.add_argument(
        "--database",
        default="data/traffic.db",
        help=(
            "SQLite database path "
            "(default: data/traffic.db)."
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "Display each normalized packet "
            "during capture."
        ),
    )

    capture_mode = (
        parser.add_mutually_exclusive_group()
    )

    capture_mode.add_argument(
        "--count",
        type=positive_int,
        help=(
            "Stop after capturing this "
            "number of packets."
        ),
    )

    capture_mode.add_argument(
        "--duration",
        type=positive_int,
        help=(
            "Capture traffic for this "
            "number of seconds."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    count = args.count
    duration = args.duration

    if count is None and duration is None:
        duration = 30

    try:
        if args.interface:
            interface = args.interface

            print(
                f"Using requested interface: "
                f"{interface}"
            )
        else:
            interface = detect_interface()

            print(
                f"Auto-detected interface: "
                f"{interface}"
            )

        capture(
            interface=interface,
            database_path=args.database,
            count=count,
            duration=duration,
            verbose=args.verbose,
        )

    except PermissionError:
        print(
            "\nERROR: Packet capture requires "
            "elevated privileges.\n"
            "Run the application with sudo or grant "
            "the appropriate network capabilities.",
            file=sys.stderr,
        )

        raise SystemExit(1)

    except KeyboardInterrupt:
        print("\nCapture stopped by user.")


if __name__ == "__main__":
    main()