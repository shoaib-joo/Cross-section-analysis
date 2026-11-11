"""PyVista plots for thin-walled cross-sections.

All three plot functions accept two optional keyword arguments:

    screenshot: path of a PNG file to save when the window is shown
    off_screen: render without opening a window (useful with ``screenshot``)

Plot convention: y is positive to the left and z is positive downwards.
"""

import math

import numpy as np
import pyvista as pv

# ---------------------------------------------------------------------------
# Look and feel
# ---------------------------------------------------------------------------

BG_BOTTOM = "#0b0f19"
BG_TOP = "#1c2740"
TEXT = "#e6edf7"
MUTED = "#7f8ba3"
STEEL = "#9fb4cc"
NODE = "#ffb454"
COG = "#5eead4"
SHEAR_CENTRE = "#c4b5fd"
AXIS_Y = "#ff6b8b"
AXIS_Z = "#59c2ff"
PANEL = "#111827"
DIVERGING_CMAP = "coolwarm"
SEQUENTIAL_CMAP = "plasma"


def _to_pv(y, z, x=0.0):
    """Engineering (y left, z down, x along the beam) -> PyVista coordinates."""
    return np.array([-y, -z, x], dtype=float)


def _new_plotter(shape, window_size, off_screen):
    plotter = pv.Plotter(shape=shape, window_size=window_size, off_screen=off_screen,
                         border_color=MUTED)
    try:
        plotter.enable_anti_aliasing("msaa")   # "ssaa" blanks all but one subplot
    except Exception:
        pass   # not supported by every graphics driver
    return plotter


def _begin_view(plotter, row, col, title, subtitle=None):
    plotter.subplot(row, col)
    plotter.set_background(BG_BOTTOM, top=BG_TOP, all_renderers=False)
    plotter.add_text(title, font_size=13, color=TEXT, position="upper_left")
    if subtitle:
        plotter.add_text(subtitle, font_size=8, color=MUTED, position=(12, plotter.window_size[1] - 62))


def _end_view_2d(plotter, zoom=0.85, shift_up=0.0):
    """Look straight at the section. ``shift_up`` moves the drawing up by that
    fraction of the view height, to leave room for text below it."""
    plotter.view_xy()
    plotter.enable_parallel_projection()
    plotter.camera.zoom(zoom)
    if shift_up:
        camera = plotter.camera
        offset = shift_up * 2 * camera.parallel_scale
        x, y, z = camera.position
        fx, fy, fz = camera.focal_point
        camera.position = (x, y - offset, z)
        camera.focal_point = (fx, fy - offset, fz)


def _show(plotter, screenshot):
    if screenshot:
        plotter.show(screenshot=str(screenshot))
    else:
        plotter.show()


def _labels(plotter, points, texts, color=TEXT, boxed=True, font_size=13):
    if not len(points):
        return
    plotter.add_point_labels(
        np.array(points, dtype=float), list(texts),
        font_size=font_size, text_color=color, bold=boxed,
        shape="rounded_rect" if boxed else None,
        shape_color=PANEL, shape_opacity=0.75, margin=4,
        show_points=False, always_visible=True,
    )


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _principal(cross_section, node):
    return cross_section.y(node.y1, node.z1), cross_section.z(node.y1, node.z1)


def _size(points):
    """Largest extent of a list of PyVista points."""
    pts = np.array(points, dtype=float)
    return float(max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]), 1e-9))


def _draw_plates(plotter, segments, color=STEEL, line_width=7):
    for p1, p2 in segments:
        plotter.add_mesh(pv.Line(p1, p2), color=color, line_width=line_width,
                         render_lines_as_tubes=True, lighting=False)


def _draw_nodes(plotter, points, labels, size):
    cloud = pv.PolyData(np.array(points, dtype=float))
    plotter.add_mesh(cloud, color=NODE, point_size=14, render_points_as_spheres=True, lighting=False)
    offset = np.array([0.03 * size, 0.03 * size, 0.0])
    _labels(plotter, [p + offset for p in points], labels, color=NODE, font_size=11)


def _draw_cog(plotter, point, label="COG"):
    plotter.add_mesh(pv.PolyData(np.array([point], dtype=float)), color=COG, point_size=18,
                     render_points_as_spheres=True, lighting=False)
    _labels(plotter, [point], [f"  {label}"], color=COG, boxed=False, font_size=12)


def _draw_centres(plotter, cog, shear_centre, size):
    """Mark the centre of gravity and the shear centre M."""
    cog = np.array(cog, dtype=float)
    shear_centre = np.array(shear_centre, dtype=float)
    if np.linalg.norm(shear_centre - cog) < 0.01 * size:
        _draw_cog(plotter, cog, "COG = M")
        return
    _draw_cog(plotter, cog)
    plotter.add_mesh(pv.PolyData(np.array([shear_centre])), color=SHEAR_CENTRE, point_size=18,
                     render_points_as_spheres=True, lighting=False)
    _labels(plotter, [shear_centre], ["  M"], color=SHEAR_CENTRE, boxed=False, font_size=12)


def _draw_axes(plotter, origin, dir_y, dir_z, length, names, colors=(AXIS_Y, AXIS_Z)):
    """Two arrows from ``origin``. Directions are given in PyVista coordinates."""
    origin = np.array(origin, dtype=float)
    for direction, name, color in zip((dir_y, dir_z), names, colors):
        direction = np.array(direction, dtype=float)
        start = origin - 0.25 * length * direction
        arrow = pv.Arrow(start=start, direction=direction, scale=1.25 * length,
                         shaft_radius=0.006, tip_radius=0.022, tip_length=0.07)
        plotter.add_mesh(arrow, color=color, lighting=False)
        _labels(plotter, [origin + 1.08 * length * direction], [name], color=color, boxed=False, font_size=14)


def _info_panel(plotter, cross_section):
    text = (
        f"A     = {cross_section.total_area:10.3f} cm^2\n"
        f"y1,s  = {cross_section.Y1s:10.3f} cm\n"
        f"z1,s  = {cross_section.Z1s:10.3f} cm\n"
        f"alpha = {cross_section.alpha:10.3f} deg\n"
        f"I_y   = {cross_section.I_y:10.3f} cm^4\n"
        f"I_z   = {cross_section.I_z:10.3f} cm^4\n"
        f"I_T   = {cross_section.I_T:10.3f} cm^4\n"
        f"I_w   = {cross_section.I_omega:10.3f} cm^6\n"
        f"y_M   = {cross_section.shear_centre[0] + 0.0:10.3f} cm\n"
        f"z_M   = {cross_section.shear_centre[1] + 0.0:10.3f} cm"
    )
    plotter.add_text(text, font_size=10, color=TEXT, position=(14, 14), font="courier")


# ---------------------------------------------------------------------------
# 1) Section in input and principal systems + extruded beam
# ---------------------------------------------------------------------------

def plot_cross_section(Nodes, Elements, cross_section, screenshot=None, off_screen=False):
    """Show the section in the input system, in the principal system and as a 3D beam."""
    plotter = _new_plotter((1, 3), [1800, 700], off_screen)
    labels = [f"N{node.id}" for node in Nodes]
    alpha = math.radians(cross_section.alpha)

    # ----- input system -----
    _begin_view(plotter, 0, 0, "Input system", "y1 positive left, z1 positive down")
    pts = [_to_pv(n.y1, n.z1) for n in Nodes]
    segments = [(_to_pv(e.start_node.y1, e.start_node.z1), _to_pv(e.end_node.y1, e.end_node.z1))
                for e in Elements]
    size = _size(pts)
    cog = _to_pv(cross_section.Y1s, cross_section.Z1s)

    _draw_axes(plotter, _to_pv(0, 0), (-1, 0, 0), (0, -1, 0), 0.30 * size, ("y1", "z1"), (MUTED, MUTED))
    _draw_plates(plotter, segments)
    # Principal axes through the COG, rotated by alpha
    _draw_axes(plotter, cog,
               (-math.cos(alpha), -math.sin(alpha), 0),
               (math.sin(alpha), -math.cos(alpha), 0),
               0.45 * size, ("y", "z"))
    _draw_nodes(plotter, pts, labels, size)
    _draw_centres(plotter, cog, _to_pv(*cross_section.shear_centre_1), size)
    _info_panel(plotter, cross_section)
    _end_view_2d(plotter, zoom=0.62, shift_up=0.16)

    # ----- principal system -----
    _begin_view(plotter, 0, 1, "Principal system", f"rotated by alpha = {cross_section.alpha:.2f} deg about the COG")
    pts_t = [_to_pv(*_principal(cross_section, n)) for n in Nodes]
    segments_t = [(_to_pv(*_principal(cross_section, e.start_node)), _to_pv(*_principal(cross_section, e.end_node)))
                  for e in Elements]
    _draw_plates(plotter, segments_t)
    _draw_axes(plotter, _to_pv(0, 0), (-1, 0, 0), (0, -1, 0), 0.45 * size, ("y", "z"))
    _draw_nodes(plotter, pts_t, labels, size)
    _draw_centres(plotter, _to_pv(0, 0), _to_pv(*cross_section.shear_centre), size)
    _end_view_2d(plotter)

    # ----- extruded beam -----
    beam_length = 4.0 * size
    _begin_view(plotter, 0, 2, "3D beam", f"wall thickness to scale, length {beam_length:.0f} cm")
    for elem, (p1, p2) in zip(Elements, segments_t):
        t_vis = max(elem.thickness, 0.01 * size)   # keep very thin walls visible
        vec = p2 - p1
        length = np.linalg.norm(vec)
        if length < 1e-12:
            continue
        d = vec / length
        n = np.array([-d[1], d[0], 0.0]) * t_vis / 2
        a, b = p1 - d * t_vis / 2, p2 + d * t_vis / 2      # overlap at the corners
        outline = pv.PolyData(np.array([a - n, b - n, b + n, a + n]), faces=[4, 0, 1, 2, 3])
        plate = outline.extrude((0, 0, -beam_length), capping=True)
        plotter.add_mesh(plate, color=STEEL, smooth_shading=False,
                         ambient=0.25, diffuse=0.75, specular=0.6, specular_power=25)
    # Centerline on the front face
    _draw_plates(plotter, [(p1 + (0, 0, 0.002 * size), p2 + (0, 0, 0.002 * size)) for p1, p2 in segments_t],
                 color=NODE, line_width=2)
    _draw_axes(plotter, _to_pv(0, 0, 0.004 * size), (-1, 0, 0), (0, -1, 0), 0.45 * size, ("y", "z"))

    centre = np.array([0.0, 0.0, -beam_length / 2])
    plotter.camera_position = [tuple(centre + np.array([1.0, 0.55, 1.25]) * beam_length), tuple(centre), (0, 1, 0)]
    plotter.reset_camera()
    plotter.camera.zoom(1.05)

    _show(plotter, screenshot)


# ---------------------------------------------------------------------------
# Distribution diagrams drawn on the plates
# ---------------------------------------------------------------------------

def _outward_normal(p1, p2):
    """In-plane unit normal of the plate p1-p2, pointing away from the COG (origin).

    Using the same side for every plate keeps positive values outside and
    negative values inside, whatever direction the plate was defined in.
    """
    d = (p2 - p1) / np.linalg.norm(p2 - p1)
    normal = np.array([-d[1], d[0], 0.0])
    side = float(np.dot(normal, (p1 + p2) / 2))
    eps = 1e-9 * max(np.linalg.norm(p1), np.linalg.norm(p2), 1.0)
    if side < -eps:
        normal = -normal
    elif abs(side) <= eps and (normal[0] < -1e-12 or (abs(normal[0]) <= 1e-12 and normal[1] < 0)):
        normal = -normal   # plate passes through the COG: pick a fixed side
    return normal


def _draw_diagram(plotter, p1, p2, values, scale, clim, scalar_bar_title=None, cmap=DIVERGING_CMAP):
    """Draw ``values`` (sampled evenly from p1 to p2) as a filled diagram on a plate.

    Returns the sample positions on the diagram edge and their values.
    """
    p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
    if np.linalg.norm(p2 - p1) < 1e-12 or len(values) < 2:
        return np.empty((0, 3)), np.empty(0)

    # Insert the exact zero crossings so the fill never folds over itself.
    t = list(np.linspace(0.0, 1.0, len(values)))
    v = [float(x) for x in values]
    ts, vs = [t[0]], [v[0]]
    for i in range(1, len(v)):
        if vs[-1] * v[i] < 0:
            tc = ts[-1] + (t[i] - ts[-1]) * vs[-1] / (vs[-1] - v[i])
            ts.append(tc)
            vs.append(0.0)
        ts.append(t[i])
        vs.append(v[i])
    ts, vs = np.array(ts), np.array(vs)

    normal = _outward_normal(p1, p2)
    base = p1 + np.outer(ts, p2 - p1)
    tip = base + np.outer(vs * scale, normal)

    n = len(ts)
    faces = np.array([[4, i, i + 1, n + i + 1, n + i] for i in range(n - 1)]).ravel()
    mesh = pv.PolyData(np.vstack((base, tip)), faces=faces)
    mesh["value"] = np.concatenate((vs, vs))

    bar = None
    if scalar_bar_title:
        bar = dict(title=scalar_bar_title, color=TEXT, vertical=True, position_x=0.86, position_y=0.25,
                   height=0.5, width=0.045, title_font_size=13, label_font_size=12, fmt="%.2f")
    plotter.add_mesh(mesh, scalars="value", cmap=cmap, clim=clim, opacity=0.9, lighting=False,
                     show_scalar_bar=bar is not None, scalar_bar_args=bar)

    plotter.add_mesh(pv.lines_from_points(tip), color=TEXT, line_width=2)
    for i in (0, -1):
        if abs(vs[i]) > 0:
            plotter.add_mesh(pv.Line(base[i], tip[i]), color=TEXT, line_width=1)
    return tip + 0.0, vs


def _diagram_view(plotter, cross_section, Elements, title, subtitle, unit_label, plate_values, fmt,
                  sequential=False):
    """One viewport with a diagram on every plate.

    ``plate_values`` is a list of (p_start, p_end, values) in PyVista coordinates.
    ``sequential`` is for values that are never negative (one-sided colour scale).
    """
    all_pts = [p for p1, p2, _ in plate_values for p in (p1, p2)]
    size = _size(all_pts)
    peak = max((abs(float(x)) for _, _, vals in plate_values for x in vals), default=0.0) or 1.0
    scale = 0.22 * size / peak
    clim = [0.0, peak] if sequential else [-peak, peak]
    cmap = SEQUENTIAL_CMAP if sequential else DIVERGING_CMAP

    _draw_axes(plotter, _to_pv(0, 0), (-1, 0, 0), (0, -1, 0), 0.30 * size, ("y", "z"), (MUTED, MUTED))

    label_pts, label_txt, seen = [], [], set()

    def add_label(point, value):
        key = (round(point[0] / size, 2), round(point[1] / size, 2), fmt.format(value))
        if key not in seen:
            seen.add(key)
            label_pts.append(point)
            label_txt.append(fmt.format(value))

    first = True
    for p1, p2, vals in plate_values:
        tip, vs = _draw_diagram(plotter, p1, p2, vals, scale, clim, unit_label if first else None, cmap)
        first = False
        if not len(vs):
            continue
        i_max = int(np.argmax(np.abs(vs)))
        for i in {0, len(vs) - 1, i_max}:
            if abs(vs[i]) > 1e-9 * peak:
                add_label(tip[i], vs[i])

    _draw_plates(plotter, [(p1, p2) for p1, p2, _ in plate_values], line_width=5)

    nodes = {}
    for elem in Elements:
        for node in (elem.start_node, elem.end_node):
            nodes[node.id] = _to_pv(*_principal(cross_section, node))
    cloud = pv.PolyData(np.array(list(nodes.values())))
    plotter.add_mesh(cloud, color=NODE, point_size=10, render_points_as_spheres=True, lighting=False)
    _draw_centres(plotter, _to_pv(0, 0), _to_pv(*cross_section.shear_centre), size)
    _labels(plotter, label_pts, label_txt, font_size=11)
    _end_view_2d(plotter)


# ---------------------------------------------------------------------------
# 2) Ordinates y and z
# ---------------------------------------------------------------------------

def plot_element_distributions(Elements, cross_section, screenshot=None, off_screen=False):
    """Plot the principal ordinates y and z along every plate."""
    plotter = _new_plotter((1, 2), [1600, 800], off_screen)

    views = [("Ordinate y", "distance from the z axis", "y [cm]", 0),
             ("Ordinate z", "distance from the y axis", "z [cm]", 1)]
    for col, (title, subtitle, unit, component) in enumerate(views):
        _begin_view(plotter, 0, col, title, subtitle + " - positive values are drawn away from the COG")
        plate_values = []
        for elem in Elements:
            start = _principal(cross_section, elem.start_node)
            end = _principal(cross_section, elem.end_node)
            values = np.linspace(start[component], end[component], 21)
            plate_values.append((_to_pv(*start), _to_pv(*end), values))
        _diagram_view(plotter, cross_section, Elements, title, subtitle, unit, plate_values, "{:.2f}")

    _show(plotter, screenshot)


# ---------------------------------------------------------------------------
# 3) Static moments
# ---------------------------------------------------------------------------

def plot_static_moment_distributions(Elements, cross_section, screenshot=None, off_screen=False):
    """Plot the static moments S_y(s) and S_z(s), starting from zero at the free ends."""
    profiles = cross_section.compute_static_moments(Elements)
    plotter = _new_plotter((1, 2), [1600, 800], off_screen)

    views = [("Static moment S_y", "S_y [cm^3]", "Sy"),
             ("Static moment S_z", "S_z [cm^3]", "Sz")]
    for col, (title, unit, key) in enumerate(views):
        _begin_view(plotter, 0, col, title, "zero at free ends - positive values are drawn away from the COG")
        plate_values = []
        for elem in Elements:
            prof = profiles[elem.element_id]
            start = _to_pv(cross_section.y(*prof["pv_start"]), cross_section.z(*prof["pv_start"]))
            end = _to_pv(cross_section.y(*prof["pv_end"]), cross_section.z(*prof["pv_end"]))
            plate_values.append((start, end, prof[key]))
        _diagram_view(plotter, cross_section, Elements, title, "", unit, plate_values, "{:.2f}")

    _show(plotter, screenshot)


# ---------------------------------------------------------------------------
# 4) Warping ordinate
# ---------------------------------------------------------------------------

def _plate_ends(cross_section, profile):
    """PyVista start and end point of a plate in its plotted direction."""
    start = _to_pv(cross_section.y(*profile["pv_start"]), cross_section.z(*profile["pv_start"]))
    end = _to_pv(cross_section.y(*profile["pv_end"]), cross_section.z(*profile["pv_end"]))
    return start, end


def plot_warping(Elements, cross_section, screenshot=None, off_screen=False):
    """Plot the normalised warping ordinate omega about the shear centre M."""
    omega = cross_section.warping_ordinates()
    plotter = _new_plotter((1, 1), [900, 800], off_screen)
    _begin_view(plotter, 0, 0, "Warping ordinate",
                f"about the shear centre M - I_T = {cross_section.I_T:.3f} cm^4, "
                f"I_w = {cross_section.I_omega:.3f} cm^6")
    plate_values = []
    for elem in Elements:
        start = _to_pv(*_principal(cross_section, elem.start_node))
        end = _to_pv(*_principal(cross_section, elem.end_node))
        values = np.linspace(omega[elem.start_node.id], omega[elem.end_node.id], 21)
        plate_values.append((start, end, values))
    _diagram_view(plotter, cross_section, Elements, "", "", "omega [cm^2]", plate_values, "{:.2f}")
    _show(plotter, screenshot)


# ---------------------------------------------------------------------------
# 5) Stresses
# ---------------------------------------------------------------------------

def plot_stresses(Elements, cross_section, N=0.0, My=0.0, Mz=0.0, Vy=0.0, Vz=0.0, Mx=0.0, Mw=0.0,
                  screenshot=None, off_screen=False):
    """Plot normal stress, shear stress and von Mises stress for a set of internal forces.

    Units follow the input: with cm, kN and kNcm the stresses are in kN/cm^2.
    See ``CrossSection.compute_stresses`` for the meaning of the loads.
    """
    loads = dict(N=N, My=My, Mz=Mz, Vy=Vy, Vz=Vz, Mx=Mx, Mw=Mw)
    stresses = cross_section.compute_stresses(**loads)
    applied = ", ".join(f"{key} = {value:g}" for key, value in loads.items() if value) or "no loads"

    plotter = _new_plotter((1, 3), [1800, 700], off_screen)
    views = [("Normal stress", applied, "sigma_x [kN/cm^2]", "sigma", False),
             ("Shear stress", "sign: direction of the shear flow along the plate", "tau [kN/cm^2]", "tau", False),
             ("Von Mises stress", "includes the torsion shear stress at the plate surfaces",
              "sigma_v [kN/cm^2]", "von_mises", True)]
    for col, (title, subtitle, unit, key, sequential) in enumerate(views):
        _begin_view(plotter, 0, col, title, subtitle)
        plate_values = []
        for elem in Elements:
            profile = stresses[elem.element_id]
            start, end = _plate_ends(cross_section, profile)
            plate_values.append((start, end, profile[key]))
        _diagram_view(plotter, cross_section, Elements, title, subtitle, unit, plate_values, "{:.2f}",
                      sequential=sequential)

    _show(plotter, screenshot)
