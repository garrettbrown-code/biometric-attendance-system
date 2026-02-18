from __future__ import annotations

import math

from app.services.geo_service import distance_feet, is_within_distance


def test_distance_zero_for_same_point() -> None:
    point = (33.214, -97.133)
    assert distance_feet(point, point) == 0.0


def test_distance_positive_for_different_points() -> None:
    a = (33.214, -97.133)
    b = (33.215, -97.133)
    d = distance_feet(a, b)
    assert d > 0
    assert isinstance(d, float)


def test_within_distance_true_when_inside_threshold() -> None:
    class_loc = (33.214, -97.133)
    student_loc = (33.21401, -97.13301)

    assert is_within_distance(
        student_loc,
        class_loc,
        max_distance_feet=100,
    ) is True


def test_within_distance_false_when_outside_threshold() -> None:
    class_loc = (33.214, -97.133)
    student_loc = (34.214, -97.133)  # ~69 miles away

    assert is_within_distance(
        student_loc,
        class_loc,
        max_distance_feet=100,
    ) is False


def test_boundary_condition_is_inclusive() -> None:
    """
    If distance == threshold exactly, it should still pass.
    """
    class_loc = (33.214, -97.133)

    # Move a tiny bit north
    student_loc = (33.2141, -97.133)

    distance = distance_feet(class_loc, student_loc)

    # Use computed distance as threshold
    assert math.isclose(distance, distance_feet(class_loc, student_loc))

    assert is_within_distance(
        student_loc,
        class_loc,
        max_distance_feet=distance,
    ) is True
