"""Analyse a predefined cross-section and show the results.

Examples:
    python main.py                       choose a section from a menu
    python main.py --list                show the available sections
    python main.py --section Angle       pick a section by name
    python main.py --section 3           ... or by its number in the list
    python main.py --section Hat --thickness 0.5 --no-plot
"""

import argparse
import sys

import cross_sections

DEFAULT_SECTION = "Channel"


def print_section_list() -> None:
    print("Available cross-sections:\n")
    for number, name in enumerate(cross_sections.names(), start=1):
        print(f"  {number:2d}  {name:<16}{cross_sections.descriptions.get(name, '')}")


def find_section(choice: str) -> str:
    """Turn a name or a list number into a library name. Raises KeyError."""
    choice = choice.strip()
    if choice.isdigit():
        available = cross_sections.names()
        if 1 <= int(choice) <= len(available):
            return available[int(choice) - 1]
        raise KeyError(f"There is no section number {choice}. Choose 1 to {len(available)}.")
    return cross_sections.resolve(choice)


def section_argument(choice: str) -> str:
    try:
        return find_section(choice)
    except KeyError as error:
        raise argparse.ArgumentTypeError(f"{error.args[0]} Run with --list to see them.")


def ask_for_section() -> str:
    """Show the menu and keep asking until a valid section is chosen."""
    print_section_list()
    while True:
        try:
            choice = input(f"\nSection number or name [{DEFAULT_SECTION}]: ").strip()
        except EOFError:
            return DEFAULT_SECTION
        if not choice:
            return DEFAULT_SECTION
        try:
            return find_section(choice)
        except KeyError as error:
            print(error.args[0])


def print_report(name: str, cross_section) -> None:
    print(f"\nCross-section: {name}  (t = {cross_section.thickness} cm)")
    print(f"  {cross_sections.descriptions.get(name, '')}")

    print("\nNodes:")
    for node in cross_section.nodes.values():
        print(f"  {node}")

    print("\nElements:")
    for elem in cross_section.elements:
        print(f"  Element {elem.element_id}: Node {elem.start_node.id} -> Node {elem.end_node.id}, "
              f"length {elem.length:.2f} cm, area {elem.area:.3f} cm^2")

    print(f"\nTotal area A              : {cross_section.total_area:.3f} cm^2")
    print(f"Centre of gravity (y1, z1): ({cross_section.Y1s:.3f}, {cross_section.Z1s:.3f}) cm")
    print(f"Principal axis angle alpha: {cross_section.alpha:.3f} deg")
    print(f"Moment of inertia I_y     : {cross_section.I_y:.3f} cm^4")
    print(f"Moment of inertia I_z     : {cross_section.I_z:.3f} cm^4")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Thin-walled cross-section analysis",
        epilog="Run without --section to choose from a menu.",
    )
    parser.add_argument("-s", "--section", type=section_argument, metavar="NAME",
                        help="section to analyse: a name or a number from --list")
    parser.add_argument("-l", "--list", action="store_true",
                        help="show the available sections and exit")
    parser.add_argument("-t", "--thickness", type=float, default=0.124,
                        help="uniform wall thickness in cm (default: 0.124)")
    parser.add_argument("--no-plot", action="store_true",
                        help="print the results only, without opening the 3D windows")
    args = parser.parse_args()

    if args.list:
        print_section_list()
        return

    name = args.section
    if name is None:
        # Only show the menu when someone is there to answer it.
        name = ask_for_section() if sys.stdin.isatty() else DEFAULT_SECTION

    cross_section = cross_sections.build(name, args.thickness)
    print_report(name, cross_section)

    if not args.no_plot:
        # Imported here so the numbers are available without PyVista installed.
        from visualization import (plot_cross_section, plot_element_distributions,
                                   plot_static_moment_distributions)

        nodes = list(cross_section.nodes.values())
        elements = cross_section.elements
        plot_cross_section(nodes, elements, cross_section)
        plot_element_distributions(elements, cross_section)
        plot_static_moment_distributions(elements, cross_section)


if __name__ == "__main__":
    main()
