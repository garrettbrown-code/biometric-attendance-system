from __future__ import annotations

from haversine import Unit, haversine


def distance_feet(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
) -> float:
    """
    Returns the distance in feet between two (lat, lon) points.
    """
    return float(haversine(point_a, point_b, unit=Unit.FEET))


def is_within_distance(
    student_location: tuple[float, float],
    class_location: tuple[float, float],
    *,
    max_distance_feet: float,
) -> bool:
    """
    Returns True if student_location is within max_distance_feet of class_location.
    Boundary is inclusive.
    """
    distance = distance_feet(student_location, class_location)
    return distance <= max_distance_feet
