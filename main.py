from model import * 
import cross_sections
from visualization import plot_cross_section,plot_element_distributions


Nodes_coordinates = cross_sections.cross_sections["Channel"]  #in cm

Nodes = []

#create node objects
for i in range(len(Nodes_coordinates)):
    node = Node(Nodes_coordinates[i][1], Nodes_coordinates[i][0], i+1)
    Nodes.append(node)

print("List of Nodes:")
for node in Nodes:
    print(node)

# Create a cross-section and add nodes and elements
thickness = 0.124  #in cm  #constant thickness
cross_section = CrossSection(thickness)

# Add all nodes to the cross-section
for node in Nodes:
    cross_section.add_node(node.id, node.y1, node.z1)

# Create elements connecting the nodes
# Elements: horizontal connections and vertical connections
element_connections = cross_sections.element_connections["Channel"]

element_id = 1
Elements = []
for start_id, end_id in element_connections:
    element = Element(element_id, cross_section.nodes[start_id], cross_section.nodes[end_id], thickness)
    Elements.append(element)
    cross_section.elements.append(element)
    element_id += 1

print("\nList of Elements:")
for elem in Elements:
    print(f"Element {elem.element_id}: Node {elem.start_node.id} -> Node {elem.end_node.id}, Length: {elem.length:.2f} cm, Area: {elem.area:.2f} cm2")

print(f"\nTotal Cross-Section Area: {cross_section.total_area:.2f} cm^4")

print(f"\nCOG y1 coordinate: {cross_section.Y1s} cm")
print(f"\nCOG z1 coordinate: {cross_section.Z1s} cm")

print(f"\nMOI along y axis Azz: {cross_section.I_y:.2f} cm4")
print(f"\nMOI along z axis Ayy: {cross_section.I_z:.2f} cm4")

# Plot the cross-section

plot_cross_section(Nodes, Elements, cross_section)
plot_element_distributions(Elements, cross_section)