import matplotlib.pyplot as plt
import numpy as np

def plot_cross_section(Nodes, Elements, cross_section):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # ===== ORIGINAL COORDINATE SYSTEM PLOT =====
    for elem in Elements:
        y_coords = [elem.start_node.y1, elem.end_node.y1]
        z_coords = [elem.start_node.z1, elem.end_node.z1]
        ax1.plot(y_coords, z_coords, 'b-', linewidth=2, label='Element' if elem == Elements[0] else '')

    node_y = [node.y1 for node in Nodes]
    node_z = [node.z1 for node in Nodes]
    ax1.scatter(node_y, node_z, color='red', s=100, zorder=5, label='Nodes')

    for node in Nodes:
        ax1.text(node.y1, node.z1 + 0.5, f'N{node.id}', ha='center', va='bottom', fontsize=7)

    ax1.scatter([cross_section.Y1s], [cross_section.Z1s], color='green', s=200, marker='x', linewidth=3, label='Center of Gravity (COG)')

    ax1.set_xlabel('Y (initial arbitrary) Coordinate (mm) - Positive towards Left', fontsize=12)
    ax1.set_ylabel('Z (initial arbitrary) Coordinate (mm) - Positive Downward', fontsize=12)
    ax1.set_title('Original Coordinate System', fontsize=14, fontweight='bold')

    moi_text = f'MOI along Y axis (I_y): {cross_section.I_y:.2f}\nMOI along Z axis (I_z): {cross_section.I_z:.2f}\nα: {cross_section.alpha:.2f}°'
    ax1.text(0.02, 0.98, moi_text, transform=ax1.transAxes, fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=11)
    ax1.set_aspect('equal', adjustable='box')
    ax1.invert_xaxis()  # Y positive towards left
    ax1.invert_yaxis()  # Z positive downward

    # ===== TRANSFORMED COORDINATE SYSTEM PLOT =====
    transformed_y = [cross_section.y(node.y1, node.z1) for node in Nodes]
    transformed_z = [cross_section.z(node.y1, node.z1) for node in Nodes]

    for elem in Elements:
        y_start = cross_section.y(elem.start_node.y1, elem.start_node.z1)
        z_start = cross_section.z(elem.start_node.y1, elem.start_node.z1)
        y_end = cross_section.y(elem.end_node.y1, elem.end_node.z1)
        z_end = cross_section.z(elem.end_node.y1, elem.end_node.z1)
        ax2.plot([y_start, y_end], [z_start, z_end], 'b-', linewidth=2, label='Element' if elem == Elements[0] else '')

    ax2.scatter(transformed_y, transformed_z, color='red', s=100, zorder=5, label='Nodes')

    for i, node in enumerate(Nodes):
        ax2.text(transformed_y[i], transformed_z[i] + 0.5, f'N{node.id}', ha='center', va='bottom', fontsize=7)

    ax2.scatter([0], [0], color='green', s=200, marker='x', linewidth=3, label='COG (Origin)')

    ax2.set_xlabel('y (rotated) Coordinate (mm) - Positive towards Left', fontsize=12)
    ax2.set_ylabel('z (rotated) Coordinate (mm) - Positive Downward', fontsize=12)
    ax2.set_title('COG-Centered Coordinate System (Rotated)', fontsize=14, fontweight='bold')

    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=11)
    ax2.set_aspect('equal', adjustable='box')
    ax2.axhline(y=0, color='k', linewidth=0.5)
    ax2.axvline(x=0, color='k', linewidth=0.5)
    ax2.invert_xaxis()  # y positive towards left
    ax2.invert_yaxis()  # z positive downward

    plt.tight_layout()
    plt.show()
    
def plot_element_distributions(Elements, cross_section):
    """
    For each element, plot y and z distance from COG vs distance along element.
    """
    n_elements = len(Elements)
    fig, axes = plt.subplots(n_elements, 1, figsize=(10, 4 * n_elements))

    # handle case of single element
    if n_elements == 1:
        axes = [axes]

    for i, elem in enumerate(Elements):
        ax = axes[i]

        # transformed coordinates of start and end
        y_start = cross_section.y(elem.start_node.y1, elem.start_node.z1)
        z_start = cross_section.z(elem.start_node.y1, elem.start_node.z1)
        y_end = cross_section.y(elem.end_node.y1, elem.end_node.z1)
        z_end = cross_section.z(elem.end_node.y1, elem.end_node.z1)

        # sample points along element
        t_values = np.linspace(0, 1, 50)
        length = elem.length

        distances = []   # x-axis: distance along element
        y_vals = []      # y distance from COG
        z_vals = []      # z distance from COG

        for t in t_values:
            py = y_start + t * (y_end - y_start)
            pz = z_start + t * (z_end - z_start)
            distances.append(t * length)
            y_vals.append(py)
            z_vals.append(pz)

        # plot both on same axes
        ax.plot(distances, y_vals, 'b-', linewidth=2, label='y distance from COG')
        ax.plot(distances, z_vals, 'r-', linewidth=2, label='z distance from COG')

        # zero line
        ax.axhline(y=0, color='k', linewidth=0.8, linestyle='--')

        # fill between zero and values
        ax.fill_between(distances, y_vals, 0, alpha=0.2, color='blue')
        ax.fill_between(distances, z_vals, 0, alpha=0.2, color='red')

        # mark start and end values
        ax.annotate(f'{y_vals[0]:.2f}', (distances[0], y_vals[0]), textcoords="offset points", xytext=(5,5), color='blue', fontsize=8)
        ax.annotate(f'{y_vals[-1]:.2f}', (distances[-1], y_vals[-1]), textcoords="offset points", xytext=(5,5), color='blue', fontsize=8)
        ax.annotate(f'{z_vals[0]:.2f}', (distances[0], z_vals[0]), textcoords="offset points", xytext=(5,-12), color='red', fontsize=8)
        ax.annotate(f'{z_vals[-1]:.2f}', (distances[-1], z_vals[-1]), textcoords="offset points", xytext=(5,-12), color='red', fontsize=8)

        ax.set_title(f'Element {elem.element_id}: Node {elem.start_node.id} → Node {elem.end_node.id} (Length: {length:.2f} cm)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Distance along element (cm)', fontsize=10)
        ax.set_ylabel('Distance from COG (cm)', fontsize=10)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

    plt.suptitle('Y and Z Distances from COG per Element', fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.show()