"""Tests for per-plate thickness, torsion, closed sections, derived values and stresses."""

import math

import pytest

import cross_sections
from model import CrossSection

T = 0.5  # wall thickness used for the uniform sections [cm]

ALL_SECTIONS = sorted(cross_sections.cross_sections)
OPEN_SECTIONS = [n for n in ALL_SECTIONS if n not in ("Box", "Two-Cell-Box", "Box-Girder")]


def box(width, height, thickness=T):
    coords = [(width / 2, 0), (-width / 2, 0), (-width / 2, height), (width / 2, height)]
    return CrossSection.from_geometry(coords, [(1, 2), (2, 3), (3, 4), (4, 1)], thickness)


# --- thickness per plate ------------------------------------------------------

def test_thickness_per_plate():
    cs = cross_sections.build("I-Section", [1.0, 1.0, 0.5, 1.0, 1.0])
    assert [e.thickness for e in cs.elements] == [1.0, 1.0, 0.5, 1.0, 1.0]
    assert cs.total_area == pytest.approx(4 * 5 * 1.0 + 10 * 0.5)
    assert cs.I_y == pytest.approx(0.5 * 10**3 / 12 + 2 * 10 * 1.0 * 5**2)


def test_wrong_number_of_thicknesses_is_rejected():
    with pytest.raises(ValueError):
        cross_sections.build("I-Section", [1.0, 0.5])


def test_ipe_200_is_close_to_the_catalogue():
    """Centerline model without fillets, so a few percent below the tables."""
    cs = cross_sections.build("IPE-200")
    assert cs.total_area == pytest.approx(28.5, rel=0.05)
    assert cs.I_y == pytest.approx(1943, rel=0.05)
    assert cs.I_z == pytest.approx(142, rel=0.05)
    assert cs.I_omega == pytest.approx(12990, rel=0.02)


# --- derived values -------------------------------------------------------------

def test_section_moduli_and_radii_of_i_section():
    cs = cross_sections.build("I-Section", T)   # b = 10, h = 10
    assert cs.W_y == pytest.approx(cs.I_y / 5)
    assert cs.W_z == pytest.approx(cs.I_z / 5)
    assert cs.i_y == pytest.approx(math.sqrt(cs.I_y / cs.total_area))
    assert cs.W_pl_y == pytest.approx(10 * T * 10 + T * 10**2 / 4)   # b*t*h + t*h^2/4
    assert cs.W_pl_z == pytest.approx(2 * T * 10**2 / 4)             # two flanges


def test_plastic_modulus_is_never_below_the_elastic_one():
    for name in ALL_SECTIONS:
        cs = cross_sections.build(name, T)
        assert cs.W_pl_y >= cs.W_y * (1 - 1e-9)
        assert cs.W_pl_z >= cs.W_z * (1 - 1e-9)


# --- torsion constant -----------------------------------------------------------

@pytest.mark.parametrize("name", OPEN_SECTIONS)
def test_torsion_constant_of_open_sections(name):
    cs = cross_sections.build(name, T)
    assert cs.n_cells == 0
    assert cs.I_T == pytest.approx(sum(e.length for e in cs.elements) * T**3 / 3)


def test_torsion_constant_of_a_box_follows_bredt():
    cs = box(10, 20)
    bredt = 4 * (10 * 20) ** 2 / (60 / T)
    assert cs.n_cells == 1
    assert cs.I_T == pytest.approx(bredt + 60 * T**3 / 3)


def test_symmetric_two_cell_box_twists_like_its_outer_box():
    """By symmetry the middle web carries no torsion shear flow."""
    cs = cross_sections.build("Two-Cell-Box", T)
    outer = 4 * (20 * 10) ** 2 / (60 / T)
    walls = sum(e.length for e in cs.elements) * T**3 / 3
    assert cs.n_cells == 2
    assert cs.I_T == pytest.approx(outer + walls)


# --- shear centre and warping -----------------------------------------------------

def test_doubly_symmetric_sections_have_the_shear_centre_at_the_centroid():
    for name in ("I-Section", "Cruciform", "Box", "Two-Cell-Box", "Z-Section"):
        cs = cross_sections.build(name, T)
        y_m, z_m = cs.shear_centre
        assert y_m == pytest.approx(0.0, abs=1e-9)
        assert z_m == pytest.approx(0.0, abs=1e-9)


def test_channel_shear_centre_lies_behind_the_web():
    cs = cross_sections.build("Channel", T)     # b = 5, h = 10, web at y1 = 0
    e = 3 * 5**2 / (6 * 5 + 10)                 # 3 b^2 / (6 b + h)
    y1_m, z1_m = cs.shear_centre_1
    assert y1_m == pytest.approx(-e)
    assert z1_m == pytest.approx(5.0)


@pytest.mark.parametrize("name", ["Angle", "Equal-Angle", "T-Section", "Cruciform"])
def test_plates_meeting_in_one_point_do_not_warp(name):
    """The shear centre is the meeting point and the warping constant is zero."""
    cs = cross_sections.build(name, T)
    meeting = {"Angle": (0, 0), "Equal-Angle": (0, 0), "T-Section": (0, 0), "Cruciform": (0, 0)}[name]
    y1_m, z1_m = cs.shear_centre_1
    assert (y1_m, z1_m) == pytest.approx(meeting, abs=1e-9)
    assert cs.I_omega == pytest.approx(0.0, abs=1e-9)


def test_warping_constants_match_the_closed_form_values():
    b, h = 5, 10
    i_section = cross_sections.build("I-Section", T)
    assert i_section.I_omega == pytest.approx(i_section.I_z * 10**2 / 4)

    channel = cross_sections.build("Channel", T)
    assert channel.I_omega == pytest.approx(T * b**3 * h**2 / 12 * (3 * b + 2 * h) / (6 * b + h))

    z_section = cross_sections.build("Z-Section", T)
    assert z_section.I_omega == pytest.approx(T * b**3 * h**2 / 12 * (b + 2 * h) / (2 * b + h))


def test_square_box_does_not_warp_but_a_rectangular_one_does():
    assert box(10, 10).I_omega == pytest.approx(0.0, abs=1e-9)
    assert box(10, 20).I_omega > 1.0


@pytest.mark.parametrize("name", ALL_SECTIONS)
def test_warping_ordinate_is_normalised(name):
    """omega must be orthogonal to 1, y and z."""
    cs = cross_sections.build(name, T)
    omega = cs.warping_ordinates()
    area = y_moment = z_moment = 0.0
    for e in cs.elements:
        a, b = e.start_node, e.end_node
        wa, wb = omega[a.id], omega[b.id]
        ya, za = cs.y(a.y1, a.z1), cs.z(a.y1, a.z1)
        yb, zb = cs.y(b.y1, b.z1), cs.z(b.y1, b.z1)
        area += e.area * (wa + wb) / 2
        y_moment += e.area / 6 * (2 * ya * wa + 2 * yb * wb + ya * wb + yb * wa)
        z_moment += e.area / 6 * (2 * za * wa + 2 * zb * wb + za * wb + zb * wa)
    scale = cs.total_area * 100
    assert area == pytest.approx(0.0, abs=1e-9 * scale)
    assert y_moment == pytest.approx(0.0, abs=1e-8 * scale)
    assert z_moment == pytest.approx(0.0, abs=1e-8 * scale)


# --- static moments in closed sections ----------------------------------------------

def test_box_static_moment():
    cs = box(10, 20)
    profiles = cs.compute_static_moments(n_pts=101)
    # Half the flange plus half the web above the y axis: b/2*t*h/2 + t*(h/2)^2/2
    assert max(abs(v) for p in profiles.values() for v in p["Sy"]) == pytest.approx(5 * T * 10 + T * 10**2 / 2)
    # Zero on the axis of symmetry, i.e. in the middle of the flanges (elements 1 and 3)
    for element_id in (1, 3):
        assert profiles[element_id]["Sy"][50] == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("name", ["Box", "Two-Cell-Box", "Box-Girder"])
def test_closed_section_shear_flow_causes_no_twist(name):
    """integral(S / t ds) around a closed loop of plates must vanish."""
    cs = cross_sections.build(name, T)
    profiles = cs.compute_static_moments(n_pts=201)
    # (element id, node the loop enters the plate at)
    loop = {
        "Box": [(1, 1), (2, 2), (3, 3), (4, 4)],
        "Two-Cell-Box": [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)],
        "Box-Girder": [(2, 2), (4, 3), (5, 5), (6, 6)],
    }[name]
    elements = {e.element_id: e for e in cs.elements}

    for key in ("Sy", "Sz"):
        total = 0.0
        for element_id, entry_node in loop:
            e, p = elements[element_id], profiles[element_id]
            values = p[key]
            step = e.length / (len(values) - 1)
            integral = sum((values[i] + values[i + 1]) / 2 for i in range(len(values) - 1)) * step
            # The values are a flow in the plotted direction; flip plates walked against it.
            sign = 1.0 if p["start_node"] == entry_node else -1.0
            total += sign * integral / e.thickness
        peak = max(abs(v) for p in profiles.values() for v in p[key]) or 1.0
        assert total == pytest.approx(0.0, abs=1e-3 * peak * 60 / T)


# --- stresses -------------------------------------------------------------------------

def test_bending_and_axial_stress_of_i_section():
    cs = cross_sections.build("I-Section", T)
    stresses = cs.compute_stresses(N=30.0, My=100.0)
    sigma = [v for p in stresses.values() for v in p["sigma"]]
    axial = 30.0 / cs.total_area
    bending = 100.0 * 5 / cs.I_y
    assert max(sigma) == pytest.approx(axial + bending)
    assert min(sigma) == pytest.approx(axial - bending)


def test_bending_about_the_weak_axis():
    cs = cross_sections.build("I-Section", T)
    stresses = cs.compute_stresses(Mz=50.0)
    sigma = [v for p in stresses.values() for v in p["sigma"]]
    assert max(sigma) == pytest.approx(50.0 * 5 / cs.I_z)
    assert min(sigma) == pytest.approx(-50.0 * 5 / cs.I_z)


def test_shear_stress_in_the_web_of_an_i_section():
    cs = cross_sections.build("I-Section", T)
    web = cs.compute_stresses(Vz=10.0, n_pts=51)[3]
    s_max = 10 * T * 5 + T * 5**2 / 2
    assert max(abs(v) for v in web["tau"]) == pytest.approx(10.0 * s_max / (cs.I_y * T))


@pytest.mark.parametrize("name", ALL_SECTIONS)
def test_shear_stresses_add_up_to_the_shear_force(name):
    """Integrating tau over the area must return V_y and V_z."""
    cs = cross_sections.build(name, T)
    v_y, v_z = 7.0, 11.0
    stresses = cs.compute_stresses(Vy=v_y, Vz=v_z, n_pts=201)
    sum_y = sum_z = 0.0
    for e in cs.elements:
        p = stresses[e.element_id]
        tau = p["tau"]
        step = e.length / (len(tau) - 1)
        force = sum((tau[i] + tau[i + 1]) / 2 for i in range(len(tau) - 1)) * step * e.thickness
        ys, zs = cs.y(*p["pv_start"]), cs.z(*p["pv_start"])
        ye, ze = cs.y(*p["pv_end"]), cs.z(*p["pv_end"])
        sum_y += force * (ye - ys) / e.length
        sum_z += force * (ze - zs) / e.length
    assert sum_y == pytest.approx(v_y, rel=1e-3)
    assert sum_z == pytest.approx(v_z, rel=1e-3)


def test_torsion_of_a_box_follows_bredt():
    cs = box(10, 20)
    stresses = cs.compute_stresses(Mx=100.0)
    closed_share = (cs.I_T - 60 * T**3 / 3) / cs.I_T
    for p in stresses.values():
        assert abs(p["tau"][0]) == pytest.approx(100.0 / (2 * 200 * T) * closed_share)


def test_torsion_of_an_open_section_gives_surface_shear_stress():
    cs = cross_sections.build("Channel", T)
    stresses = cs.compute_stresses(Mx=5.0)
    for p in stresses.values():
        assert p["tau_t"] == pytest.approx(5.0 * T / cs.I_T)
        assert max(abs(v) for v in p["tau"]) == pytest.approx(0.0, abs=1e-12)
        assert p["von_mises"][0] == pytest.approx(math.sqrt(3) * p["tau_t"])


def test_disconnected_section_is_rejected():
    cs = CrossSection.from_geometry([(0, 0), (5, 0), (0, 5), (5, 5)], [(1, 2), (3, 4)], T)
    with pytest.raises(ValueError):
        cs.compute_static_moments()
