"""Library of predefined centerline cross-sections.

``cross_sections`` maps a section name to its node coordinates as
(y1, z1) pairs in cm. Nodes are numbered from 1 in the order listed.
In the plots y is positive to the left and z is positive downwards.

``element_connections`` maps the same name to the (start_node, end_node)
pairs that make up the plates of the section.

``descriptions`` holds a one-line description of each section.

To add a section, add an entry with the same name to all three dictionaries.
"""

from model import CrossSection

cross_sections = {
    # --- doubly symmetric ---
    "I-Section": [(5, 0), (0, 0), (-5, 0), (-5, 10), (0, 10), (5, 10)],
    "Cruciform": [(5, 0), (-5, 0), (0, -5), (0, 5), (0, 0)],
    # --- singly symmetric ---
    "Channel": [(0, 0), (5, 0), (5, 10), (0, 10)],
    "Lipped-Channel": [(5, 1.5), (5, 0), (0, 0), (0, 10), (5, 10), (5, 8.5)],
    "T-Section": [(5, 0), (0, 0), (-5, 0), (0, 10)],
    "Mono-I": [(5, 0), (0, 0), (-5, 0), (3, 10), (0, 10), (-3, 10)],
    "Hat": [(7, 10), (4, 10), (4, 0), (-4, 0), (-4, 10), (-7, 10)],
    "Equal-Angle": [(10, 0), (0, 0), (0, 10)],
    "Custom": [(9.5, 0), (5, 0), (-5, 0), (-9.5, 0), (-9.5, 18.65), (9.5, 18.65)],
    # --- no symmetry axis: the principal axes are rotated ---
    "Angle": [(10, 0), (0, 0), (0, 5)],
    "Z-Section": [(5, 0), (0, 0), (0, 10), (-5, 10)],
    "Lipped-Z": [(5, 1.5), (5, 0), (0, 0), (0, 10), (-5, 10), (-5, 8.5)],
}

element_connections = {
    "I-Section": [(1, 2), (2, 3), (2, 5), (4, 5), (5, 6)],
    "Cruciform": [(1, 5), (5, 2), (3, 5), (5, 4)],
    "Channel": [(1, 2), (1, 4), (4, 3)],
    "Lipped-Channel": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)],
    "T-Section": [(1, 2), (2, 3), (2, 4)],
    "Mono-I": [(1, 2), (2, 3), (2, 5), (4, 5), (5, 6)],
    "Hat": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)],
    "Equal-Angle": [(1, 2), (2, 3)],
    "Custom": [(1, 2), (3, 4), (4, 5), (5, 6), (6, 1)],
    "Angle": [(1, 2), (2, 3)],
    "Z-Section": [(1, 2), (2, 3), (3, 4)],
    "Lipped-Z": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)],
}

descriptions = {
    "I-Section": "I-beam, flanges 10 cm, height 10 cm",
    "Cruciform": "Cross of two 10 cm plates",
    "Channel": "U-profile, flanges 5 cm, web 10 cm",
    "Lipped-Channel": "C-profile with 1.5 cm lips",
    "T-Section": "T-profile, flange 10 cm, web 10 cm",
    "Mono-I": "I-beam with unequal flanges (10 cm and 6 cm)",
    "Hat": "Top-hat profile with 3 cm brims",
    "Equal-Angle": "L-profile, legs 10 x 10 cm (principal axes at 45 deg)",
    "Custom": "Box 19 x 18.65 cm with a slit in one flange",
    "Angle": "L-profile, legs 10 x 5 cm (rotated principal axes)",
    "Z-Section": "Z-profile, flanges 5 cm, web 10 cm (rotated principal axes)",
    "Lipped-Z": "Z-profile with 1.5 cm lips (rotated principal axes)",
}


def names() -> list[str]:
    """Names of all library sections, in library order."""
    return list(cross_sections)


def resolve(name: str) -> str:
    """Return the library name matching ``name``.

    Matching ignores case, spaces, hyphens and underscores, so "i section",
    "I_Section" and "isection" all find "I-Section".
    """
    def key(text: str) -> str:
        return "".join(ch for ch in text.lower() if ch.isalnum())

    wanted = key(name)
    for candidate in cross_sections:
        if key(candidate) == wanted:
            return candidate
    raise KeyError(f"Unknown cross-section '{name}'. Available: {', '.join(names())}.")


def build(name: str, thickness: float) -> CrossSection:
    """Create a CrossSection from the library.

    Args:
        name: Name of the section, e.g. "I-Section" (see ``resolve``).
        thickness: Uniform wall thickness in cm.
    """
    name = resolve(name)
    return CrossSection.from_geometry(cross_sections[name], element_connections[name], thickness)
