"""Tests for the cross-section model, checked against hand calculations."""

import math

import pytest

import cross_sections
from model import CrossSection

T = 0.5  # wall thickness used throughout [cm]


def principal_values(cs):
    """Principal second moments from Mohr's circle (independent of alpha)."""
    mean = (cs.Ayy_2 + cs.Azz_2) / 2
    radius = math.hypot((cs.Ayy_2 - cs.Azz_2) / 2, cs.Ayz_2)
    return mean - radius, mean + radius


# --- doubly / singly symmetric sections: closed-form values -----------------

def test_i_section():
    cs = cross_sections.build("I-Section", T)   # b = 10, h = 10
    assert cs.total_area == pytest.approx(30 * T)
    assert cs.Y1s == pytest.approx(0.0)
    assert cs.Z1s == pytest.approx(5.0)
    assert cs.alpha == pytest.approx(0.0)
    assert cs.I_y == pytest.approx(T * 10**3 / 12 + 2 * 10 * T * 5**2)   # web + flanges
    assert cs.I_z == pytest.approx(2 * T * 10**3 / 12)                   # two flanges


def test_channel():
    cs = cross_sections.build("Channel", T)     # b = 5, h = 10
    assert cs.total_area == pytest.approx(20 * T)
    assert cs.Y1s == pytest.approx(1.25)
    assert cs.Z1s == pytest.approx(5.0)
    assert cs.alpha == pytest.approx(0.0)
    assert cs.I_y == pytest.approx(T * 10**3 / 12 + 2 * 5 * T * 5**2)
    assert cs.I_z == pytest.approx(2 * T * 5**3 / 3 - 20 * T * 1.25**2)


def test_aligned_section_is_not_rotated_when_strong_axis_is_y():
    """A_zz > A_yy with A_yz = 0 must give alpha = 0, not 90 degrees."""
    cs = cross_sections.build("I-Section", T)
    assert cs.Azz_2 > cs.Ayy_2
    assert cs.alpha == 0.0


# --- unsymmetric section: hand calculation ----------------------------------

def test_unequal_angle():
    cs = cross_sections.build("Angle", 1.0)     # legs 10 (along y) and 5 (along z)
    assert cs.total_area == pytest.approx(15.0)
    assert cs.Y1s == pytest.approx(10 / 3)
    assert cs.Z1s == pytest.approx(5 / 6)
    assert cs.Ayy_2 == pytest.approx(166.6667, abs=1e-4)
    assert cs.Azz_2 == pytest.approx(31.25)
    assert cs.Ayz_2 == pytest.approx(-41.6667, abs=1e-4)
    assert cs.alpha == pytest.approx(-15.8037, abs=1e-4)
    assert cs.I_y == pytest.approx(19.4566, abs=1e-4)
    assert cs.I_z == pytest.approx(178.4601, abs=1e-4)


def test_equal_angle_rotates_45_degrees():
    cs = CrossSection.from_geometry([(10, 0), (0, 0), (0, 10)], [(1, 2), (2, 3)], T)
    assert abs(cs.alpha) == pytest.approx(45.0)


# --- properties that must hold for every section ----------------------------

@pytest.mark.parametrize("name", sorted(cross_sections.cross_sections))
def test_principal_moments_match_mohrs_circle(name):
    cs = cross_sections.build(name, T)
    i_min, i_max = principal_values(cs)
    assert sorted([cs.I_y, cs.I_z]) == pytest.approx([i_min, i_max])
    assert cs.I_y + cs.I_z == pytest.approx(cs.Ayy_2 + cs.Azz_2)
    assert -45.0 <= cs.alpha <= 45.0


@pytest.mark.parametrize("name", sorted(cross_sections.cross_sections))
def test_transformed_section_is_principal(name):
    """Rebuild the section from its transformed coordinates: the product
    moment must vanish and the second moments must equal I_y and I_z."""
    cs = cross_sections.build(name, T)
    coords = [(cs.y(n.y1, n.z1), cs.z(n.y1, n.z1)) for n in cs.nodes.values()]
    rotated = CrossSection.from_geometry(coords, cross_sections.element_connections[name], T)

    scale = cs.Ayy_2 + cs.Azz_2
    assert rotated.Y1s == pytest.approx(0.0, abs=1e-9)
    assert rotated.Z1s == pytest.approx(0.0, abs=1e-9)
    assert rotated.A_yz_1 == pytest.approx(0.0, abs=1e-9 * scale)
    assert rotated.A_zz_1 == pytest.approx(cs.I_y)
    assert rotated.A_yy_1 == pytest.approx(cs.I_z)


# --- static moments ----------------------------------------------------------

def test_static_moment_starts_at_zero_on_free_ends():
    cs = cross_sections.build("Channel", T)
    profiles = cs.compute_static_moments(cs.elements)
    # Elements 1 and 3 are the flanges, each starting at a free end.
    for element_id in (1, 3):
        assert profiles[element_id]["Sy"][0] == pytest.approx(0.0)
        assert profiles[element_id]["Sz"][0] == pytest.approx(0.0)


def test_i_section_web_collects_both_flange_halves():
    cs = cross_sections.build("I-Section", T)
    web = cs.compute_static_moments(cs.elements, n_pts=51)[3]["Sy"]
    # Whole flange (b*t) at lever arm h/2 enters the web ...
    assert abs(web[0]) == pytest.approx(10 * T * 5)
    # ... and the maximum sits at mid-height.
    assert max(abs(v) for v in web) == pytest.approx(10 * T * 5 + T * 5**2 / 2)
    assert abs(web[25]) == pytest.approx(10 * T * 5 + T * 5**2 / 2)


@pytest.mark.parametrize("name", sorted(cross_sections.cross_sections))
def test_static_moment_increments_sum_to_zero(name):
    """The first moment of the whole section about its centroid is zero, so
    the increments picked up along all elements must cancel."""
    cs = cross_sections.build(name, T)
    profiles = cs.compute_static_moments(cs.elements)
    scale = cs.total_area * 10
    for key in ("Sy", "Sz"):
        total = sum(p[key][-1] - p[key][0] for p in profiles.values())
        assert total == pytest.approx(0.0, abs=1e-9 * scale)


def test_static_moment_branches_meet_with_opposite_values():
    """Angle: the two legs are traversed from their free ends and meet at the
    corner, where their static moments must cancel."""
    cs = cross_sections.build("Angle", T)
    profiles = cs.compute_static_moments(cs.elements)
    for key in ("Sy", "Sz"):
        assert profiles[1][key][-1] + profiles[2][key][-1] == pytest.approx(0.0, abs=1e-9)
