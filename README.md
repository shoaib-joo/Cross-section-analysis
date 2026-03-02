# Cross-Section Analysis Tool

A Python-based tool for analyzing structural cross-sections using centerline models. This tool calculates geometric properties (area, moments of inertia, center of gravity) and transforms coordinates between arbitrary and principal axes.

## Features

- **Multiple Cross-Section Templates**: Pre-defined I-section, rectangular, T-section, L-section, and custom shapes
- **Centerline Model**: Based on middle-line structural analysis approach
- **Geometric Properties Calculation**:
  - Total cross-sectional area
  - Center of gravity (COG)
  - First moments of area
  - Moments of inertia
  - Principal axes orientation (α)
  
- **Coordinate Transformation**: Convert between arbitrary and COG-centered rotated coordinate systems
- **Visualization**: Dual-plot display showing original and transformed geometries

## File Structure

```
├── model.py              # Core classes: Node, Element, CrossSection
├── cross_sections.py     # Cross-section library and factory
├── main.py              # Main script with visualization
└── .gitignore           # Git ignore rules
```

## Classes

### model.py
- **Node**: Represents a point in 2D space with y and z coordinates
- **Element**: Represents a structural element connecting two nodes
- **CrossSection**: Aggregates nodes and elements, calculates geometric properties

### cross_sections.py
- **CROSS_SECTIONS**: Dictionary of predefined section templates
- **CrossSectionFactory**: Factory class to instantiate sections from templates

## Usage

### Basic Usage

```python
from model import CrossSection
from cross_sections import CrossSectionFactory, CROSS_SECTIONS

# Create a cross-section
thickness = 2.15  # in mm
section_name = 'I_section'  # or 'rectangular_section', 'T_section', etc.

cross_section, nodes, elements = CrossSectionFactory.create_section(
    section_name, thickness, CrossSection
)

# Access properties
print(f"Area: {cross_section.total_area}")
print(f"COG Y: {cross_section.Y1s}, COG Z: {cross_section.Z1s}")
print(f"I_y: {cross_section.I_y}, I_z: {cross_section.I_z}")
print(f"Principal angle α: {cross_section.alpha}°")

# Transform coordinates to principal axes
y_transformed = cross_section.y(y_coord, z_coord)
z_transformed = cross_section.z(y_coord, z_coord)
```

### Available Cross-Sections

- `'custom_section'`: Custom 6-node section
- `'I_section'`: I-shaped beam section
- `'rectangular_section'`: Simple rectangular section
- `'T_section'`: T-shaped section
- `'L_section'`: L-shaped section

## Running the Visualization

```bash
python main.py
```

This generates a side-by-side comparison:
1. **Left plot**: Original arbitrary coordinate system
2. **Right plot**: COG-centered rotated coordinate system

## Requirements

- Python 3.7+
- matplotlib
- numpy (if needed)

## Installation

```bash
git clone <repository-url>
cd Standardiyation\ 1
python main.py
```

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
