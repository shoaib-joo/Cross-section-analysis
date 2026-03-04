# Cross-Section Analysis Tool

A Python-based tool for analyzing structural cross-sections using centerline models. This tool calculates geometric properties (area, moments of inertia, center of gravity) and transforms coordinates between arbitrary and principal axes.

## Features

- **Flexible Cross-Section Definition**: Define custom cross-sections using nodes and connecting elements
- **Centerline Model**: Based on middle-line structural analysis approach with uniform element thickness
- **Geometric Properties Calculation**:
  - Total cross-sectional area
  - Center of gravity (COG)
  - First moments of area
  - Moments of inertia (Ayy, Azz)
  - Principal axes orientation (α)
  
- **Coordinate Transformation**: Convert between arbitrary and COG-centered principal-axis-aligned coordinate systems
- **Visualization**: Dual-plot display showing original and COG-centered transformed geometries

## File Structure

```
├── model.py           # Core classes: Node, Element, CrossSection
├── cross_sections.py  # Predefined cross-section templates and element connections
├── visualization.py   # Plotting functions for cross-section visualization
├── main.py            # Example script (I-Section analysis with visualization)
└── README.md          # Project documentation
```

## Classes

### model.py

- **Node**: Represents a point in 2D space with y and z coordinates
  - Attributes: `id`, `y1`, `z1`
  
- **Element**: Represents a structural element (line segment) connecting two nodes with uniform thickness
  - Properties: `length`, `area`, `first_moment_y1i`, `first_moment_z1i`, `Ayy_1i`, `Azz_1i`, `Ayz_1i`
  
- **CrossSection**: Aggregates nodes and elements, calculates all geometric properties
  - Properties: `total_area`, `Y1s` (COG y-coordinate), `Z1s` (COG z-coordinate), `I_y`, `I_z`, `alpha` (principal axis angle)
  - Methods: `add_node()`, `add_elements()`, `y()` (coordinate transformation), `z()` (coordinate transformation)

### cross_sections.py

- **cross_sections**: Dictionary of predefined cross-section coordinates
  - Available sections: `"Custom"`, `"I-Section"`
  
- **element_connections**: Dictionary mapping section names to their element connection patterns

### visualization.py

- **plot_cross_section()**: Function to visualize cross-sections
  - Parameters: `Nodes` (list of Node objects), `Elements` (list of Element objects), `cross_section` (CrossSection object)
  - Displays two side-by-side plots: original and transformed coordinate systems

## Usage

### Basic Usage

```python
from model import Node, Element, CrossSection
from visualization import plot_cross_section
import cross_sections

# Load predefined cross-section or define your own
coordinates = cross_sections.cross_sections["I-Section"]
element_connections = cross_sections.element_connections["I-Section"]

# Create nodes
thickness = 0.124  # in cm
cross_section = CrossSection(thickness)
Nodes = []

for i, coord in enumerate(coordinates):
    node = Node(coord[1], coord[0], i+1)
    Nodes.append(node)
    cross_section.add_node(node.id, node.y1, node.z1)

# Create elements
Elements = []
for elem_id, (start_id, end_id) in enumerate(element_connections, 1):
    element = Element(elem_id, cross_section.nodes[start_id], cross_section.nodes[end_id], thickness)
    Elements.append(element)
    cross_section.elements.append(element)

# Access geometric properties
print(f"Total Area: {cross_section.total_area}")
print(f"COG: ({cross_section.Y1s}, {cross_section.Z1s})")
print(f"MOI Y: {cross_section.I_y}, MOI Z: {cross_section.I_z}")
print(f"Principal Axis Angle: {cross_section.alpha}°")

# Visualize the cross-section
plot_cross_section(Nodes, Elements, cross_section)
```

### Example: I-Section Analysis

See [main.py](main.py) for a complete working example that analyzes an I-Section:
1. Loads predefined I-Section nodes and element connections from [cross_sections.py](cross_sections.py)
2. Creates Node and Element objects
3. Calculates all geometric properties
4. Calls [visualization.py](visualization.py) to display the original and transformed coordinate systems

## Running the Example

```bash
python main.py
```

This script:
1. Loads the I-Section configuration from `cross_sections.py`
2. Creates Node and Element objects with specified thickness
3. Calculates cross-sectional properties (area, COG, moments of inertia)
4. Prints the results to the console
5. Calls `plot_cross_section()` from `visualization.py` to generate a figure with two side-by-side plots:
   - **Left plot**: Original arbitrary coordinate system with COG marked
   - **Right plot**: COG-centered coordinate system aligned with principal axes

The visualization displays:
- Structural elements (blue lines)
- Node positions (red dots with labels)
- Center of gravity location
- Moments of inertia and principal axis angle

## Requirements

- Python 3.7+
- matplotlib
- numpy

## Mathematical Background

### Coordinate Transformation

The transformation from arbitrary (y₁, z₁) to principal (y, z) coordinates:

$$y = (y_1 - Y_{1s})\cos(\alpha) + (z_1 - Z_{1s})\sin(\alpha)$$

$$z = (z_1 - Z_{1s})\cos(\alpha) - (y_1 - Y_{1s})\sin(\alpha)$$

Where:
- $(Y_{1s}, Z_{1s})$ = Center of gravity coordinates
- $\alpha$ = Principal axes angle

## Author

Created during WiSe 2026 - ModSteel Project

## License

MIT License - Feel free to use and modify
