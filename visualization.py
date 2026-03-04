import matplotlib.pyplot as plt

def plot_cross_section(Nodes, Elements, cross_section):
    """
    Plot the cross-section in original and transformed coordinate systems.
    
    Args:
        Nodes: List of Node objects
        Elements: List of Element objects
        cross_section: CrossSection object with calculated properties
    """
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # ===== ORIGINAL COORDINATE SYSTEM PLOT =====
    # Plot elements (lines connecting nodes)
    for elem in Elements:
        y_coords = [elem.start_node.y1, elem.end_node.y1]
        z_coords = [elem.start_node.z1, elem.end_node.z1]
        ax1.plot(z_coords, y_coords, 'b-', linewidth=2, label='Element' if elem == Elements[0] else '')

    # Plot nodes (points)
    node_y = [node.y1 for node in Nodes]
    node_z = [node.z1 for node in Nodes]
    ax1.scatter(node_z, node_y, color='red', s=100, zorder=5, label='Nodes')

    # Add node labels
    for node in Nodes:
        ax1.text(node.z1 + 0.5, node.y1, f'N{node.id}', ha='left', va='center', fontsize=7)

    # Plot center of gravity
    ax1.scatter([cross_section.Z1s], [cross_section.Y1s], color='green', s=200, marker='x', linewidth=3, label='Center of Gravity (COG)')

    # Labels and formatting for original
    ax1.set_xlabel('Z (initial arbitrary) Coordinate (mm) - Positive towards Left', fontsize=12)
    ax1.set_ylabel('Y (initial arbitrary) Coordinate (mm) - Positive Downward', fontsize=12)
    ax1.set_title('Original Coordinate System', fontsize=14, fontweight='bold')

    # Add MOI information as text box
    moi_text = f'MOI along Y axis (I_y): {cross_section.I_y:.2f}\nMOI along Z axis (I_z): {cross_section.I_z:.2f}\nα: {cross_section.alpha:.2f}°'
    ax1.text(0.02, 0.98, moi_text, transform=ax1.transAxes, fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=11)
    ax1.set_aspect('equal', adjustable='box')
    ax1.invert_xaxis()  # Z positive towards left
    ax1.invert_yaxis()  # Y positive downward

    # ===== TRANSFORMED COORDINATE SYSTEM PLOT =====
    # Calculate transformed coordinates for all nodes
    transformed_y = [cross_section.y(node.y1, node.z1) for node in Nodes]
    transformed_z = [cross_section.z(node.y1, node.z1) for node in Nodes]

    # Plot transformed elements (lines connecting nodes)
    for elem in Elements:
        y_start = cross_section.y(elem.start_node.y1, elem.start_node.z1)
        z_start = cross_section.z(elem.start_node.y1, elem.start_node.z1)
        y_end = cross_section.y(elem.end_node.y1, elem.end_node.z1)
        z_end = cross_section.z(elem.end_node.y1, elem.end_node.z1)
        ax2.plot([z_start, z_end], [y_start, y_end], 'b-', linewidth=2, label='Element' if elem == Elements[0] else '')

    # Plot transformed nodes (points)
    ax2.scatter(transformed_z, transformed_y, color='red', s=100, zorder=5, label='Nodes')

    # Add node labels for transformed
    for i, node in enumerate(Nodes):
        ax2.text(transformed_z[i] + 0.5, transformed_y[i], f'N{node.id}', ha='left', va='center', fontsize=7)

    # Plot center of gravity at origin (ideally 0,0 )
    ax2.scatter([0], [0], color='green', s=200, marker='x', linewidth=3, label='COG (Origin)')

    # Labels and formatting for transformed
    ax2.set_xlabel('z (rotated) Coordinate (mm)', fontsize=12)
    ax2.set_ylabel('y (rotated) Coordinate (mm)', fontsize=12)
    ax2.set_title('COG-Centered Coordinate System (Rotated)', fontsize=14, fontweight='bold')

    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=11)
    ax2.set_aspect('equal', adjustable='box')
    ax2.axhline(y=0, color='k', linewidth=0.5)
    ax2.axvline(x=0, color='k', linewidth=0.5)
    ax2.invert_xaxis()  # z positive towards left
    ax2.invert_yaxis()  # y positive downward

    plt.tight_layout()
    plt.show()
