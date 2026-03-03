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
├── model.py       # Core classes: Node, Element, CrossSection
├── main.py        # Example script with visualization
└── README.md      # Project documentation
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

## Usage

### Basic Usage

```python
from model import Node, Element, CrossSection

# Create nodes defining the cross-section outline
node1 = Node(y1=0, z1=9.5, node_id=1)
node2 = Node(y1=0, z1=5, node_id=2)
# ... add more nodes

# Create cross-section with uniform thickness
thickness = 0.124  # in cm
cross_section = CrossSection(thickness)

# Add nodes
for node in nodes_list:
    cross_section.add_node(node.id, node.y1, node.z1)

# Create elements connecting nodes
element = Element(element_id=1, start_node=node1, end_node=node2, thickness=thickness)
cross_section.elements.append(element)

# Access geometric properties
print(f"Total Area: {cross_section.total_area}")
print(f"COG: ({cross_section.Y1s}, {cross_section.Z1s})")
print(f"MOI Y: {cross_section.I_y}, MOI Z: {cross_section.I_z}")
print(f"Principal Axis Angle: {cross_section.alpha}°")

# Transform coordinates to COG-centered system
y_transformed = cross_section.y(y_arbitrary, z_arbitrary)
z_transformed = cross_section.z(y_arbitrary, z_arbitrary)

```

### Example: H-Shaped Beam

See [main.py](main.py) for a complete working example that analyzes an H-shaped cross-section:
1. Defines 6 nodes at the corners of an H-shaped profile
2. Creates elements connecting the nodes
3. Calculates all geometric properties
4. Displays the original and transformed coordinate systems

## Running the Example

```bash
python main.py
```

This generates a figure with two side-by-side plots:
1. **Left plot**: Original arbitrary coordinate system with COG marked
2. **Right plot**: COG-centered coordinate system aligned with principal axes

The plots display:
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
