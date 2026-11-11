"""Analyse a predefined cross-section and show the results.

Examples:
    python main.py                       choose a section from a menu
    python main.py --list                show the available sections
    python main.py --section Angle       pick a section by name
    python main.py --section 3           ... or by its number in the list
    python main.py -s Hat -t 0.5 --no-plot
    python main.py -s I-Section -t 0.8 0.8 0.5 0.8 0.8      one thickness per plate
    python main.py -s IPE-200 --Vz 50 --My 2000             stresses for a load case

Units: lengths in cm, forces in kN, moments in kNcm, stresses in kN/cm^2.
"""

import argparse
import sys

import cross_sections

DEFAULT_SECTION = "Channel"
LOADS = [
    ("N", "axial force N [kN], tension positive"),
    ("My", "bending moment M_y [kNcm]"),
    ("Mz", "bending moment M_z [kNcm]"),
    ("Vy", "shear force V_y [kN]"),
    ("Vz", "shear force V_z [kN]"),
    ("Mx", "St. Venant torsion moment M_x [kNcm]"),
    ("Mw", "warping bimoment M_w [kNcm^2]"),
]


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
    print(f"\nCross-section: {name}")
    print(f"  {cross_sections.descriptions.get(name, '')}")

    print("\nNodes:")
    for node in cross_section.nodes.values():
        print(f"  {node}")

    print("\nElements:")
    for elem in cross_section.elements:
        print(f"  Element {elem.element_id}: Node {elem.start_node.id} -> Node {elem.end_node.id}, "
              f"length {elem.length:.2f} cm, t {elem.thickness:.3f} cm, area {elem.area:.3f} cm^2")

    cells = cross_section.n_cells
    kind = "open" if cells == 0 else f"closed, {cells} cell{'s' if cells > 1 else ''}"
    y_m, z_m = cross_section.shear_centre
    y1_m, z1_m = cross_section.shear_centre_1

    rows = [
        ("Type", kind, ""),
        ("Area A", cross_section.total_area, "cm^2"),
        ("Centre of gravity y1,s", cross_section.Y1s, "cm"),
        ("Centre of gravity z1,s", cross_section.Z1s, "cm"),
        ("Principal axis angle alpha", cross_section.alpha, "deg"),
        None,
        ("Moment of inertia I_y", cross_section.I_y, "cm^4"),
        ("Moment of inertia I_z", cross_section.I_z, "cm^4"),
        ("Radius of gyration i_y", cross_section.i_y, "cm"),
        ("Radius of gyration i_z", cross_section.i_z, "cm"),
        ("Elastic modulus W_y", cross_section.W_y, "cm^3"),
        ("Elastic modulus W_z", cross_section.W_z, "cm^3"),
        ("Plastic modulus W_pl,y", cross_section.W_pl_y, "cm^3"),
        ("Plastic modulus W_pl,z", cross_section.W_pl_z, "cm^3"),
        None,
        ("Shear centre y_M (principal)", y_m, "cm"),
        ("Shear centre z_M (principal)", z_m, "cm"),
        ("Shear centre y1,M (input)", y1_m, "cm"),
        ("Shear centre z1,M (input)", z1_m, "cm"),
        ("Torsion constant I_T", cross_section.I_T, "cm^4"),
        ("Warping constant I_omega", cross_section.I_omega, "cm^6"),
    ]
    print()
    for row in rows:
        if row is None:
            print()
            continue
        label, value, unit = row
        text = value if isinstance(value, str) else f"{value + 0.0:12.3f}"
        print(f"{label:<30}: {text} {unit}")


def print_stress_report(cross_section, loads: dict) -> None:
    stresses = cross_section.compute_stresses(**loads)
    applied = ", ".join(f"{key} = {value:g}" for key, value in loads.items() if value)
    print(f"\nStresses for {applied}  [kN, cm]")
    print(f"\n  {'Element':<9}{'sigma min':>11}{'sigma max':>11}{'|tau| max':>11}{'tau_t':>9}{'von Mises':>11}")
    for elem in cross_section.elements:
        result = stresses[elem.element_id]
        print(f"  {elem.element_id:<9}{min(result['sigma']):>11.3f}{max(result['sigma']):>11.3f}"
              f"{max(abs(v) for v in result['tau']):>11.3f}{result['tau_t']:>9.3f}"
              f"{max(result['von_mises']):>11.3f}")
    peak = max(v for result in stresses.values() for v in result["von_mises"])
    print(f"\n  Largest von Mises stress: {peak:.3f} kN/cm^2")
    print("  tau_t is the extra torsion shear stress at the plate surfaces.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Thin-walled cross-section analysis",
        epilog="Run without --section to choose from a menu. "
               "Units: cm, kN, kNcm. Loads refer to the principal axes.",
    )
    parser.add_argument("-s", "--section", type=section_argument, metavar="NAME",
                        help="section to analyse: a name or a number from --list")
    parser.add_argument("-l", "--list", action="store_true",
                        help="show the available sections and exit")
    parser.add_argument("-t", "--thickness", type=float, nargs="+", metavar="T",
                        help="wall thickness in cm: one value for all plates, or one value "
                             f"per plate (default: {cross_sections.DEFAULT_THICKNESS}, or the "
                             "section's own thicknesses)")
    parser.add_argument("--no-plot", action="store_true",
                        help="print the results only, without opening the 3D windows")
    load_group = parser.add_argument_group("loads (give at least one to get stresses)")
    for key, text in LOADS:
        load_group.add_argument(f"--{key}", type=float, default=0.0, metavar="X", help=text)
    args = parser.parse_args()

    if args.list:
        print_section_list()
        return

    name = args.section
    if name is None:
        # Only show the menu when someone is there to answer it.
        name = ask_for_section() if sys.stdin.isatty() else DEFAULT_SECTION

    thickness = args.thickness
    if thickness is not None and len(thickness) == 1:
        thickness = thickness[0]
    try:
        cross_section = cross_sections.build(name, thickness)
    except ValueError as error:
        parser.error(f"{error} Give one thickness, or one per plate of '{name}'.")

    print_report(name, cross_section)

    loads = {key: getattr(args, key) for key, _ in LOADS}
    has_loads = any(loads.values())
    if has_loads:
        print_stress_report(cross_section, loads)

    if not args.no_plot:
        # Imported here so the numbers are available without PyVista installed.
        from visualization import (plot_cross_section, plot_element_distributions,
                                   plot_static_moment_distributions, plot_stresses, plot_warping)

        nodes = list(cross_section.nodes.values())
        elements = cross_section.elements
        plot_cross_section(nodes, elements, cross_section)
        plot_element_distributions(elements, cross_section)
        plot_static_moment_distributions(elements, cross_section)
        plot_warping(elements, cross_section)
        if has_loads:
            plot_stresses(elements, cross_section, **loads)


if __name__ == "__main__":
    main()
