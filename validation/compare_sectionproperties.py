"""Compare this tool with the finite element package ``sectionproperties``.

    pip install sectionproperties
    python validation/compare_sectionproperties.py

This tool uses a centerline model: every plate is a line with a thickness.
sectionproperties meshes the real, solid outline. Each case below therefore
builds the solid shape whose wall centerlines are the library section, with
sharp corners and no fillets.

The script prints a Markdown table (the one shown in the README).
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sectionproperties.analysis import Section
from sectionproperties.pre.library import (angle_section, channel_section, i_section,
                                           rectangular_hollow_section)

import cross_sections

T = 0.5   # wall thickness of the uniform sections [cm]


def cases():
    """(label, library name, thickness, solid geometry)."""
    yield ("IPE 200 (no fillets)", "IPE-200", None,
           i_section(d=19.15 + 0.85, b=10.0, t_f=0.85, t_w=0.56, r=0.0, n_r=1))
    yield (f"Channel 5 x 10, t = {T}", "Channel", T,
           channel_section(d=10.0 + T, b=5.0 + T / 2, t_f=T, t_w=T, r=0.0, n_r=1))
    yield (f"Angle 10 x 5, t = {T}", "Angle", T,
           angle_section(d=5.0 + T / 2, b=10.0 + T / 2, t=T, r_r=0.0, r_t=0.0, n_r=1))
    yield (f"Box 10 x 20, t = {T}", "Box", T,
           rectangular_hollow_section(d=20.0 + T, b=10.0 + T, t=T, r_out=0.0, n_r=1))


def finite_element_values(geometry, thickness):
    geometry.create_mesh(mesh_sizes=[thickness**2 / 8])
    section = Section(geometry=geometry)
    section.calculate_geometric_properties()
    section.calculate_warping_properties()
    i_11, i_22 = section.get_ip()
    cx, cy = section.get_c()
    sx, sy = section.get_sc()
    return {
        "A": section.get_area(),
        "I_max": max(i_11, i_22),
        "I_min": min(i_11, i_22),
        "I_T": section.get_j(),
        "I_w": section.get_gamma(),
        "e_M": math.hypot(sx - cx, sy - cy),
    }


def centerline_values(name, thickness):
    section = cross_sections.build(name, thickness)
    return {
        "A": section.total_area,
        "I_max": max(section.I_y, section.I_z),
        "I_min": min(section.I_y, section.I_z),
        "I_T": section.I_T,
        "I_w": section.I_omega,
        "e_M": math.hypot(*section.shear_centre),
    }


ROWS = [("A", "A [cm²]"), ("I_max", "I_max [cm⁴]"), ("I_min", "I_min [cm⁴]"),
        ("I_T", "I_T [cm⁴]"), ("I_w", "I_ω [cm⁶]"), ("e_M", "COG to M [cm]")]


def main():
    print("| Section | Property | This tool | sectionproperties | Difference |")
    print("|---|---|---:|---:|---:|")
    for label, name, thickness, geometry in cases():
        thinnest = thickness if thickness is not None else min(cross_sections.thicknesses[name])
        ours = centerline_values(name, thickness)
        theirs = finite_element_values(geometry, thinnest)
        for key, text in ROWS:
            a, b = ours[key], theirs[key]
            if abs(b) < 1e-6 * max(theirs["I_max"], 1.0) and abs(a) < 1e-6 * max(theirs["I_max"], 1.0):
                difference = "–"
            elif key == "I_w" and abs(a) < 1e-9 * abs(b):
                difference = "see note"
            elif key == "e_M":
                difference = f"{a - b:+.3f} cm"
            else:
                difference = f"{(a - b) / b * 100:+.1f} %"
            print(f"| {label} | {text} | {a:.3f} | {b:.3f} | {difference} |")
            label = ""


if __name__ == "__main__":
    main()
