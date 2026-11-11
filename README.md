# Cross-Section Analysis Tool

[![Tests](https://github.com/shoaib-joo/Cross-section-analysis/actions/workflows/tests.yml/badge.svg)](https://github.com/shoaib-joo/Cross-section-analysis/actions/workflows/tests.yml)

A Python tool for analysing thin-walled structural cross-sections with a centerline model. It computes the section properties (area, centre of gravity, principal axes, moments of inertia, static moments) and shows them in interactive 3D views.

The notation and sign conventions follow Kindmann & Kraus, *Steel Structures: Design using FEM*.

![Unequal angle in the input and principal coordinate systems, and extruded as a beam](docs/images/cross_section.png)

## Features

- **Flexible geometry** – describe any open thin-walled section with nodes and connecting plates of uniform thickness
- **Section properties**
  - Total area and centre of gravity (COG)
  - Second moments of area about the input axes and about the COG
  - Principal axis angle α
  - Principal moments of inertia I_y and I_z
  - Static moment distributions S_y(s) and S_z(s) along every plate
- **Coordinate transformation** from the arbitrary input system to the principal axes through the COG
- **Visualisation** with PyVista: input and principal systems, an extruded 3D beam, ordinate diagrams and static moment diagrams
- **Section library** – 12 ready-made sections: I, mono-symmetric I, T, channel, lipped channel, hat, cruciform, equal and unequal angle, Z, lipped Z and a slit box

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/shoaib-joo/Cross-section-analysis.git
cd Cross-section-analysis
pip install -r requirements.txt
```

The calculations in `model.py` use only the Python standard library. NumPy and PyVista are needed for the plots.

## Quick start

```bash
python main.py              # choose a section from a menu
python main.py --list       # show the available sections
```

```
Available cross-sections:

   1  I-Section       I-beam, flanges 10 cm, height 10 cm
   2  Cruciform       Cross of two 10 cm plates
   3  Channel         U-profile, flanges 5 cm, web 10 cm
   4  Lipped-Channel  C-profile with 1.5 cm lips
   5  T-Section       T-profile, flange 10 cm, web 10 cm
   6  Mono-I          I-beam with unequal flanges (10 cm and 6 cm)
   7  Hat             Top-hat profile with 3 cm brims
   8  Equal-Angle     L-profile, legs 10 x 10 cm (principal axes at 45 deg)
   9  Custom          Box 19 x 18.65 cm with a slit in one flange
  10  Angle           L-profile, legs 10 x 5 cm (rotated principal axes)
  11  Z-Section       Z-profile, flanges 5 cm, web 10 cm (rotated principal axes)
  12  Lipped-Z        Z-profile with 1.5 cm lips (rotated principal axes)
```

Pick a section by name or by its number. Names ignore case, spaces and hyphens.

```bash
python main.py --section Angle                    # by name
python main.py --section 7                        # by number (Hat)
python main.py -s "lipped z" -t 0.5               # short options, custom thickness in cm
python main.py --section I-Section --no-plot      # numbers only, no plot windows
```

| Option | Meaning |
|---|---|
| `-s`, `--section NAME` | Section to analyse: a name or a number from `--list`. Without it, a menu is shown. |
| `-l`, `--list` | Show the available sections and exit |
| `-t`, `--thickness T` | Uniform wall thickness in cm (default 0.124) |
| `--no-plot` | Print the results without opening the plot windows |

Example output:

```
Cross-section: Angle  (t = 1.0 cm)

Total area A              : 15.000 cm^2
Centre of gravity (y1, z1): (3.333, 0.833) cm
Principal axis angle alpha: -15.804 deg
Moment of inertia I_y     : 19.457 cm^4
Moment of inertia I_z     : 178.460 cm^4
```

## Using it in your own code

```python
from model import CrossSection

# Node coordinates as (y1, z1) pairs in cm, numbered from 1 in the order given
coordinates = [(10, 0), (0, 0), (0, 5)]
# Plates as (start_node, end_node) pairs
connections = [(1, 2), (2, 3)]

section = CrossSection.from_geometry(coordinates, connections, thickness=1.0)

print(section.total_area)            # 15.0
print(section.Y1s, section.Z1s)      # centre of gravity
print(section.alpha)                 # principal axis angle in degrees
print(section.I_y, section.I_z)      # principal moments of inertia
```

To use a section from the library and plot it:

```python
import cross_sections
from visualization import plot_cross_section, plot_static_moment_distributions

section = cross_sections.build("I-Section", thickness=0.5)
nodes = list(section.nodes.values())

plot_cross_section(nodes, section.elements, section)
plot_static_moment_distributions(section.elements, section)
```

Add your own section by adding an entry with the same name to the three dictionaries in [cross_sections.py](cross_sections.py) (coordinates, connections and description). It then appears in `--list` and the menu automatically.

## Plots

Distances of each plate from the principal axes:

![y and z ordinates drawn on an I-section](docs/images/distances.png)

Static moments, starting from zero at the free ends:

![Static moment diagrams of an I-section](docs/images/static_moments.png)

## Project structure

```
├── model.py             # Node, Element, CrossSection: all calculations
├── cross_sections.py    # Library of predefined sections
├── visualization.py     # PyVista plots
├── main.py              # Command-line example
├── tests/               # pytest suite checked against hand calculations
└── docs/images/         # Screenshots used in this README
```

## Mathematical background

Coordinates: `y1`, `z1` are the arbitrary input axes. `y`, `z` are the principal axes through the centre of gravity. In the plots y points left and z points down.

Each plate between nodes *a* and *b* with area $A = t \cdot l$ contributes

$$A_{yy} = \tfrac{A}{3}\,(y_a^2 + y_a y_b + y_b^2) \qquad A_{zz} = \tfrac{A}{3}\,(z_a^2 + z_a z_b + z_b^2)$$

$$A_{yz} = \tfrac{A}{6}\,\big(2 y_a z_a + 2 y_b z_b + y_a z_b + y_b z_a\big)$$

After shifting to the centre of gravity $(Y_{1s}, Z_{1s})$ with the parallel axis theorem, the principal axis angle is

$$\tan 2\alpha = \frac{2A_{yz}}{A_{yy} - A_{zz}}, \qquad -45^\circ \le \alpha \le 45^\circ$$

and the principal moments of inertia are

$$I_y = A_{zz}\cos^2\alpha + A_{yy}\sin^2\alpha - 2A_{yz}\sin\alpha\cos\alpha$$

$$I_z = A_{yy}\cos^2\alpha + A_{zz}\sin^2\alpha + 2A_{yz}\sin\alpha\cos\alpha$$

Coordinates are transformed with

$$y = (y_1 - Y_{1s})\cos\alpha + (z_1 - Z_{1s})\sin\alpha$$

$$z = (z_1 - Z_{1s})\cos\alpha - (y_1 - Y_{1s})\sin\alpha$$

The static moment along a plate, measured from its start at arc length $s = 0$, is

$$S_y(s) = S_{y,0} + t\left(z_a s + \frac{z_b - z_a}{2l}s^2\right)$$

and likewise for $S_z$ with y in place of z. $S_0$ is zero at a free end. Where plates meet, the next plate starts with the sum of everything arriving at the node.

## Limitations

- All plates share one thickness.
- Static moments are computed for open sections only. Plates that are part of a closed cell are not handled.
- Torsion properties (shear centre, warping ordinate, I_T, I_ω) are not implemented yet.

## Tests

```bash
pip install pytest
pytest
```

The tests compare the results with closed-form values for the I-section and channel, with a hand calculation for the unequal angle, and with Mohr's circle for every library section.

## Credits

The coordinate system and procedure follow

> Rolf Kindmann, Matthias Kraus: *Steel Structures: Design using FEM*. Ernst & Sohn. https://onlinelibrary.wiley.com/doi/book/10.1002/9783433600771

## Author

[shoaib-joo](https://github.com/shoaib-joo). Created during WiSe 2026 at Bauhaus Universitaet.
