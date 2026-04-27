import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv

def plot_cross_section(Nodes, Elements, cross_section):
    # Setup PyVista Plotter with 3 subplots
    # 0: Original Coordinates, 1: Transformed Coordinates, 2: Extruded 3D Beam
    plotter = pv.Plotter(shape=(1, 3), window_size=[1800, 600])

    def to_pv(y, z, x=0):
        # To map standard engineering 2D views (Y left, Z down) to PyVista
        # PV_X = -y (positive y moves left)
        # PV_Y = -z (positive z moves down)
        return [-y, -z, x]

    # ===== VIEW 1: ORIGINAL SYSTEM =====
    plotter.subplot(0, 0)
    plotter.add_text('Original Coordinate System\n(Y positive left, Z positive down)', font_size=10, position='upper_edge')
    
    # Elements
    for elem in Elements:
        p1 = to_pv(elem.start_node.y1, elem.start_node.z1)
        p2 = to_pv(elem.end_node.y1, elem.end_node.z1)
        line = pv.Line(p1, p2)
        plotter.add_mesh(line, color='blue', line_width=5)
        
    # Nodes
    pts = np.array([to_pv(node.y1, node.z1) for node in Nodes])
    cloud = pv.PolyData(pts)
    plotter.add_mesh(cloud, color='red', point_size=15, render_points_as_spheres=True)
    
    # Node Labels
    labels = [f"N{node.id}" for node in Nodes]
    plotter.add_point_labels(cloud, labels, point_size=18, font_size=14, text_color='black', shape_color='white', shape_opacity=0.7, always_visible=True)

    # COG
    cog_pt = to_pv(cross_section.Y1s, cross_section.Z1s)
    cog_cloud = pv.PolyData(np.array([cog_pt]))
    plotter.add_mesh(cog_cloud, color='green', point_size=20, render_points_as_spheres=True)
    plotter.add_point_labels(cog_cloud, ['COG'], point_size=20, font_size=14, text_color='green', always_visible=True)

    # Info Text
    moi_text = f'MOI Y (I_y): {cross_section.I_y:.2f}\nMOI Z (I_z): {cross_section.I_z:.2f}\nAlpha: {cross_section.alpha:.2f} deg'
    plotter.add_text(moi_text, font_size=10, position='lower_left')
    
    plotter.view_xy()
    plotter.enable_parallel_projection()
    
    # ===== VIEW 2: TRANSFORMED SYSTEM =====
    plotter.subplot(0, 1)
    plotter.add_text('Transformed (Rotated) System', font_size=10, position='upper_edge')
    
    for elem in Elements:
        y1_trans = cross_section.y(elem.start_node.y1, elem.start_node.z1)
        z1_trans = cross_section.z(elem.start_node.y1, elem.start_node.z1)
        y2_trans = cross_section.y(elem.end_node.y1, elem.end_node.z1)
        z2_trans = cross_section.z(elem.end_node.y1, elem.end_node.z1)
        
        p1 = to_pv(y1_trans, z1_trans)
        p2 = to_pv(y2_trans, z2_trans)
        line = pv.Line(p1, p2)
        plotter.add_mesh(line, color='blue', line_width=5)
        
    pts_trans = []
    for node in Nodes:
        yt = cross_section.y(node.y1, node.z1)
        zt = cross_section.z(node.y1, node.z1)
        pts_trans.append(to_pv(yt, zt))
    cloud_trans = pv.PolyData(np.array(pts_trans))
    plotter.add_mesh(cloud_trans, color='red', point_size=15, render_points_as_spheres=True)
    plotter.add_point_labels(cloud_trans, labels, point_size=18, font_size=14, text_color='black', shape_color='white', shape_opacity=0.7, always_visible=True)

    cog_trans_cloud = pv.PolyData(np.array([to_pv(0, 0)]))
    plotter.add_mesh(cog_trans_cloud, color='green', point_size=20, render_points_as_spheres=True)
    plotter.add_point_labels(cog_trans_cloud, ['COG (0,0)'], point_size=20, font_size=14, text_color='green', always_visible=True)
    
    plotter.view_xy()
    plotter.enable_parallel_projection()
    
    # ===== VIEW 3: EXTRUDED 3D BEAM =====
    plotter.subplot(0, 2)
    plotter.add_text('3D Extruded Beam\n(Extruded 100cm along Z axis)', font_size=10, position='upper_edge')
    
    extrusion_length = 100.0 # cm
    
    points_3d = []
    lines_3d = []
    pt_idx = 0
    
    for elem in Elements:
        y1_trans = cross_section.y(elem.start_node.y1, elem.start_node.z1)
        z1_trans = cross_section.z(elem.start_node.y1, elem.start_node.z1)
        y2_trans = cross_section.y(elem.end_node.y1, elem.end_node.z1)
        z2_trans = cross_section.z(elem.end_node.y1, elem.end_node.z1)
        
        points_3d.append(to_pv(y1_trans, z1_trans, 0))
        points_3d.append(to_pv(y2_trans, z2_trans, 0))
        
        lines_3d.append(2)
        lines_3d.append(pt_idx)
        lines_3d.append(pt_idx + 1)
        pt_idx += 2
        
    profile = pv.PolyData(np.array(points_3d), lines=np.array(lines_3d))
    beam_surface = profile.extrude((0, 0, extrusion_length))
    
    plotter.add_mesh(beam_surface, color='steelblue', opacity=0.9, show_edges=True)
    plotter.add_axes()
    plotter.view_isometric()

    plotter.show()
    
def plot_element_distributions(Elements, cross_section):
    """
    For each element, plot y and z distance from COG directly on the cross-section elements.
    """
    plotter = pv.Plotter(shape=(1, 2), window_size=[1600, 800])
    
    def to_pv(y, z, x=0):
        # Map our Y to PV_X = -y (positive left) and Z to PV_Y = -z (positive down)
        return [-y, -z, x]

    # Find the bounding box width to scale the diagrams
    max_val = 0.0
    min_y = float('inf')
    max_y = float('-inf')
    min_z = float('inf')
    max_z = float('-inf')
    
    for elem in Elements:
        y_start = cross_section.y(elem.start_node.y1, elem.start_node.z1)
        z_start = cross_section.z(elem.start_node.y1, elem.start_node.z1)
        y_end = cross_section.y(elem.end_node.y1, elem.end_node.z1)
        z_end = cross_section.z(elem.end_node.y1, elem.end_node.z1)
        
        max_val = max(max_val, abs(y_start), abs(y_end), abs(z_start), abs(z_end))
        min_y = min(min_y, y_start, y_end)
        max_y = max(max_y, y_start, y_end)
        min_z = min(min_z, z_start, z_end)
        max_z = max(max_z, z_start, z_end)
        
    cross_section_width = max(max_y - min_y, max_z - min_z)
    
    # Auto-scale: max diagram height = 20% of cross-section width
    target_height = 0.20 * cross_section_width if cross_section_width > 0 else 5.0
    scale = target_height / max_val if max_val > 0 else 1.0

    titles = ['Y Distance from COG Distribution', 'Z Distance from COG Distribution']
    colors = ['blue', 'red']
    
    for vp_idx in [0, 1]:
        plotter.subplot(0, vp_idx)
        plotter.add_text(titles[vp_idx], font_size=12, position='upper_edge')
        
        # Plot COG
        cog_pt = to_pv(0, 0)
        cog_cloud = pv.PolyData(np.array([cog_pt], dtype=float))
        plotter.add_mesh(cog_cloud, color='green', point_size=20, render_points_as_spheres=True)
        plotter.add_point_labels(cog_cloud, ['COG (0,0)'], point_size=20, font_size=14, text_color='green', always_visible=True)

        for elem in Elements:
            y1_trans = cross_section.y(elem.start_node.y1, elem.start_node.z1)
            z1_trans = cross_section.z(elem.start_node.y1, elem.start_node.z1)
            y2_trans = cross_section.y(elem.end_node.y1, elem.end_node.z1)
            z2_trans = cross_section.z(elem.end_node.y1, elem.end_node.z1)
            
            p1 = to_pv(y1_trans, z1_trans)
            p2 = to_pv(y2_trans, z2_trans)
            line = pv.Line(p1, p2)
            plotter.add_mesh(line, color='black', line_width=4)
            
            # Nodes labels
            plotter.add_point_labels(pv.PolyData(np.array([p1], dtype=float)), [f"N{elem.start_node.id}"], font_size=12, text_color='black', shape_opacity=0, always_visible=True)
            plotter.add_point_labels(pv.PolyData(np.array([p2], dtype=float)), [f"N{elem.end_node.id}"], font_size=12, text_color='black', shape_opacity=0, always_visible=True)
            
            # Determine values based on viewport
            if vp_idx == 0:
                val_A = y1_trans
                val_B = y2_trans
            else:
                val_A = z1_trans
                val_B = z2_trans
                
            # Direction vector
            vec = np.array(p2) - np.array(p1)
            length = np.linalg.norm(vec)
            if length == 0: continue
            
            dir_vec = vec / length
            
            # Perpendicular vector in PV plane (-dy, dx, 0)
            perp = np.array([-dir_vec[1], dir_vec[0], 0])
            
            # Diagram points
            p3 = np.array(p2) + scale * val_B * perp
            p4 = np.array(p1) + scale * val_A * perp
            
            # Handle zero-crossing (bowtie polygon) to prevent rendering artifacts
            if val_A * val_B < -1e-8:
                t = val_A / (val_A - val_B)
                p_z = np.array(p1) + t * vec
                points = np.vstack((p1, p2, p3, p4, p_z)).astype(float)
                # Split into two triangles with consistent winding: [p1, p4, p_z] and [p_z, p2, p3]
                faces = np.hstack(([3, 0, 3, 4], [3, 4, 1, 2]))
            else:
                points = np.vstack((p1, p2, p3, p4)).astype(float)
                faces = np.array([4, 0, 1, 2, 3])
            
            diagram_surface = pv.PolyData(points, faces)
            
            # lighting=False is critical to prevent dark spots from 2D surface normals
            plotter.add_mesh(diagram_surface, color=colors[vp_idx], opacity=0.4, show_edges=True, lighting=False)
            
            # Annotate values
            plotter.add_point_labels(pv.PolyData(np.array([p3], dtype=float)), [f"{val_B:.2f}"], font_size=14, text_color=colors[vp_idx], shape_opacity=0, always_visible=True)
            plotter.add_point_labels(pv.PolyData(np.array([p4], dtype=float)), [f"{val_A:.2f}"], font_size=14, text_color=colors[vp_idx], shape_opacity=0, always_visible=True)
            
        plotter.view_xy()
        plotter.enable_parallel_projection()
        
    plotter.show()