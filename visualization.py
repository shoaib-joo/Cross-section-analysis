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


def _draw_distribution_diagram(plotter, p_start, p_end, values, color, cross_section):
    """
    Helper: draw a smooth parabolic distribution diagram orthogonal to the element.
    p_start, p_end: PyVista [x,y,z] endpoint arrays.
    values: list of scalar values sampled at equal arc-length steps between p_start and p_end.
    The diagram is built from a strip of quads (one per interval).
    """
    n = len(values)
    if n < 2:
        return

    p1 = np.array(p_start, dtype=float)
    p2 = np.array(p_end,   dtype=float)
    vec = p2 - p1
    length = np.linalg.norm(vec)
    if length < 1e-12:
        return

    dir_vec = vec / length
    perp = np.array([-dir_vec[1], dir_vec[0], 0.0])

    # Sample points on the element axis
    t_vals = np.linspace(0.0, 1.0, n)
    base_pts = np.array([p1 + t * vec for t in t_vals])   # points on element
    tip_pts  = np.array([base_pts[i] + float(values[i]) * perp for i in range(n)])

    # Build quad strip: each segment becomes one quad
    all_pts = []
    faces   = []
    pt_idx  = 0
    for i in range(n - 1):
        b0, b1 = base_pts[i], base_pts[i + 1]
        t0, t1 = tip_pts[i],  tip_pts[i + 1]

        # Check for sign change -> split at zero crossing
        v0, v1 = float(values[i]), float(values[i + 1])
        if v0 * v1 < -1e-12:
            tc = v0 / (v0 - v1)
            bm = b0 + tc * (b1 - b0)   # zero crossing on base
            # Triangle A: b0, t0, bm
            pts_a = np.vstack((b0, t0, bm)).astype(float)
            plotter.add_mesh(pv.PolyData(pts_a, np.array([3, 0, 1, 2])),
                             color=color, opacity=0.45, lighting=False, show_edges=False)
            # Triangle B: bm, t1, b1
            pts_b = np.vstack((bm, t1, b1)).astype(float)
            plotter.add_mesh(pv.PolyData(pts_b, np.array([3, 0, 1, 2])),
                             color=color, opacity=0.45, lighting=False, show_edges=False)
        else:
            pts = np.vstack((b0, b1, t1, t0)).astype(float)
            plotter.add_mesh(pv.PolyData(pts, np.array([4, 0, 1, 2, 3])),
                             color=color, opacity=0.45, lighting=False, show_edges=False)

    # Outline: base line (element) and tip curve
    for i in range(n - 1):
        plotter.add_mesh(pv.Line(base_pts[i], base_pts[i + 1]), color='black', line_width=3)
        plotter.add_mesh(pv.Line(tip_pts[i],  tip_pts[i + 1]),  color=color,   line_width=2)
    # Closing verticals at start and end
    plotter.add_mesh(pv.Line(base_pts[0],  tip_pts[0]),  color=color, line_width=1)
    plotter.add_mesh(pv.Line(base_pts[-1], tip_pts[-1]), color=color, line_width=1)


def plot_static_moment_distributions(Elements, cross_section):
    """
    Plot Sy and Sz static moment diagrams drawn orthogonally on the cross-section elements.
    The diagrams are parabolic because S(s) is quadratic along a linear element.
    """
    # Compute profiles via BFS traversal from free ends
    profiles = cross_section.compute_static_moments(Elements)

    # Auto-scale: find max absolute value across all profiles
    max_Sy = max(abs(v) for p in profiles.values() for v in p['Sy']) or 1.0
    max_Sz = max(abs(v) for p in profiles.values() for v in p['Sz']) or 1.0

    # Bounding box of transformed coordinates for scale target
    all_y = [cross_section.y(n.y1, n.z1) for elem in Elements
             for n in (elem.start_node, elem.end_node)]
    all_z = [cross_section.z(n.y1, n.z1) for elem in Elements
             for n in (elem.start_node, elem.end_node)]
    cs_width = max(max(all_y) - min(all_y), max(all_z) - min(all_z))
    target_h = 0.20 * cs_width if cs_width > 0 else 5.0

    scale_Sy = target_h / max_Sy
    scale_Sz = target_h / max_Sz

    plotter = pv.Plotter(shape=(1, 2), window_size=[1600, 800])
    titles = ['Static Moment Sy Distribution', 'Static Moment Sz Distribution']
    colors = ['royalblue', 'firebrick']

    def to_pv(y, z, x=0.0):
        return np.array([-y, -z, x], dtype=float)

    for vp_idx in range(2):
        plotter.subplot(0, vp_idx)
        plotter.add_text(titles[vp_idx], font_size=12, position='upper_edge')

        # COG marker
        cog_cloud = pv.PolyData(np.array([to_pv(0, 0)]))
        plotter.add_mesh(cog_cloud, color='green', point_size=20, render_points_as_spheres=True)
        plotter.add_point_labels(cog_cloud, ['COG'], font_size=14, text_color='green', always_visible=True)

        for elem in Elements:
            prof = profiles[elem.element_id]
            y_s, z_s = prof['pv_start']
            y_e, z_e = prof['pv_end']

            # Transformed coordinates of the traversal direction
            y1_t = cross_section.y(y_s, z_s)
            z1_t = cross_section.z(y_s, z_s)
            y2_t = cross_section.y(y_e, z_e)
            z2_t = cross_section.z(y_e, z_e)

            p_start = to_pv(y1_t, z1_t)
            p_end   = to_pv(y2_t, z2_t)

            raw_vals = prof['Sy'] if vp_idx == 0 else prof['Sz']
            scale    = scale_Sy  if vp_idx == 0 else scale_Sz
            scaled   = [v * scale for v in raw_vals]

            _draw_distribution_diagram(plotter, p_start, p_end, scaled,
                                       colors[vp_idx], cross_section)

            # Node labels at both ends
            plotter.add_point_labels(pv.PolyData(np.array([p_start])),
                                     [f"N{elem.start_node.id if not prof['pv_start'] == (elem.end_node.y1, elem.end_node.z1) else elem.end_node.id}"],
                                     font_size=12, text_color='black', shape_opacity=0, always_visible=True)

            # Annotate max value on diagram
            vals = raw_vals
            max_i = int(np.argmax(np.abs(vals)))
            tip_t = np.linspace(0, 1, len(vals))[max_i]
            p_tip = p_start + tip_t * (p_end - p_start) + scaled[max_i] * np.array(
                [-(p_end - p_start)[1], (p_end - p_start)[0], 0.0]) / max(np.linalg.norm(p_end - p_start), 1e-9)
            plotter.add_point_labels(pv.PolyData(np.array([p_tip], dtype=float)),
                                     [f"  {vals[max_i]:.3f}"],
                                     font_size=13, text_color=colors[vp_idx], shape_opacity=0, always_visible=True)

        plotter.view_xy()
        plotter.enable_parallel_projection()

    plotter.show()