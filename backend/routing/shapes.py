"""
shapes.py — loads GTFS shapes.txt and slices the real track geometry
between two stop coordinates, so the frontend can draw the metro line
as it actually curves rather than a straight line between stations.

Usage:
    shapes = load_shapes(data_dir)
    segment = get_shape_segment(shapes, "shp_1_2", 28.61, 77.02, 28.64, 77.05)
    # segment is a list of (lat, lon) tuples along the real track
"""

import os
import pandas as pd
from haversine import haversine, Unit


def load_shapes(data_dir: str) -> dict:
    """
    Load shapes.txt and group points by shape_id, sorted by sequence.

    Returns:
        { shape_id: [(lat, lon), (lat, lon), ...] }
    """
    path = os.path.join(data_dir, "dmrc", "shapes.txt")
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    df = df.sort_values(["shape_id", "shape_pt_sequence"])

    shapes = {}
    for shape_id, group in df.groupby("shape_id"):
        points = list(zip(group["shape_pt_lat"].astype(float),
                          group["shape_pt_lon"].astype(float)))
        shapes[shape_id] = points

    print(f"[shapes] Loaded {len(shapes)} shapes "
          f"({len(df):,} total points)")
    return shapes


def closest_point_index(points: list, lat: float, lon: float) -> int:
    """
    Find the index of the point in `points` closest to (lat, lon).

    Same pattern as nearest_stop() in geocode.py — loop through every
    candidate, track the minimum haversine distance seen so far.
    """
    min_dist = float("inf")
    closest_idx = 0

    for i, (p_lat, p_lon) in enumerate(points):
        dist = haversine((lat, lon), (p_lat, p_lon), unit=Unit.METERS)
        if dist < min_dist:
            min_dist = dist
            closest_idx = i

    return closest_idx


def get_shape_segment(shapes: dict, shape_id: str,
                      from_lat: float, from_lon: float,
                      to_lat: float, to_lon: float) -> list:
    """
    Returns the slice of real track points between two stop coordinates.

    Falls back to a straight 2-point line if the shape_id is missing —
    this keeps bus legs (which have no shape data) working correctly,
    since they'll just draw a straight line as before.

    Returns:
        list of (lat, lon) tuples tracing the real curve
    """
    if not shape_id or shape_id == "None" or shape_id not in shapes:
        return [(from_lat, from_lon), (to_lat, to_lon)]

    points = shapes[shape_id]

    start_idx = closest_point_index(points, from_lat, from_lon)
    end_idx   = closest_point_index(points, to_lat, to_lon)

    if start_idx == end_idx:
        # degenerate case - same point, just return the two endpoints
        return [(from_lat, from_lon), (to_lat, to_lon)]

    if start_idx < end_idx:
        segment = points[start_idx:end_idx + 1]
    else:
        # shape direction is reversed relative to travel direction
        segment = points[end_idx:start_idx + 1][::-1]

    return segment


if __name__ == "__main__":
    # quick manual test
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    shapes = load_shapes(data_dir)

    # grab any shape_id to sanity check
    sample_id = list(shapes.keys())[0]
    sample_points = shapes[sample_id]
    print(f"\nSample shape: {sample_id}")
    print(f"Total points: {len(sample_points)}")
    print(f"First point: {sample_points[0]}")
    print(f"Last point:  {sample_points[-1]}")

    seg = get_shape_segment(
        shapes, sample_id,
        sample_points[0][0], sample_points[0][1],
        sample_points[-1][0], sample_points[-1][1]
    )
    print(f"\nSliced segment length: {len(seg)} points "
          f"(should be close to {len(sample_points)})")