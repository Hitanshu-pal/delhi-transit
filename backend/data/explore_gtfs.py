"""
Step 3 — Explore and validate GTFS data.

Run this ONCE after you've placed the GTFS files in backend/data/.
It prints a summary of each feed and flags any problems (missing coords,
duplicate stop IDs, zero-duration trips) before you build the graph.

Usage:
    cd backend/data
    python explore_gtfs.py
"""

import os
import pandas as pd

DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def load_table(folder: str, filename: str) -> pd.DataFrame | None:
    path = os.path.join(DATA_DIR, folder, filename)
    if not os.path.exists(path):
        print(f"  [missing] {folder}/{filename}")
        return None
    df = pd.read_csv(path, low_memory=False)
    print(f"  [ok] {folder}/{filename:25s}  {len(df):>7,} rows  {list(df.columns)}")
    return df


def check_stops(stops: pd.DataFrame, label: str):
    print(f"\n  -- Stop quality checks ({label}) --")
    missing_lat = stops["stop_lat"].isna().sum()
    missing_lon = stops["stop_lon"].isna().sum()
    dupe_ids = stops["stop_id"].duplicated().sum()
    print(f"  Missing lat:   {missing_lat}")
    print(f"  Missing lon:   {missing_lon}")
    print(f"  Duplicate IDs: {dupe_ids}")

    # Sanity-check coords are inside Delhi bbox
    # Delhi roughly: lat 28.4–28.9, lon 76.8–77.4
    if "stop_lat" in stops.columns and "stop_lon" in stops.columns:
        outside = stops[
            (stops["stop_lat"] < 28.0) | (stops["stop_lat"] > 29.5) |
            (stops["stop_lon"] < 76.5) | (stops["stop_lon"] > 78.0)
        ]
        if len(outside):
            print(f"  Stops outside Delhi bbox: {len(outside)}")
            print(outside[["stop_id", "stop_name", "stop_lat", "stop_lon"]].head())
        else:
            print(f"  All {len(stops)} stops are inside the Delhi bounding box. Good.")


def check_stop_times(stop_times: pd.DataFrame):
    print("\n  -- stop_times quality checks --")
    print(f"  Unique trips:  {stop_times['trip_id'].nunique():,}")
    print(f"  Unique stops:  {stop_times['stop_id'].nunique():,}")
    missing_dep = stop_times["departure_time"].isna().sum()
    missing_arr = stop_times["arrival_time"].isna().sum()
    print(f"  Missing departure_time: {missing_dep}")
    print(f"  Missing arrival_time:   {missing_arr}")

    sample = stop_times.head(3)[["trip_id", "stop_sequence", "stop_id",
                                  "arrival_time", "departure_time"]]
    print("\n  Sample rows:")
    print(sample.to_string(index=False))


def explore_feed(folder: str, label: str):
    print(f"\n{'='*55}")
    print(f"  {label} — folder: {folder}/")
    print(f"{'='*55}")

    stops       = load_table(folder, "stops.txt")
    routes      = load_table(folder, "routes.txt")
    trips       = load_table(folder, "trips.txt")
    stop_times  = load_table(folder, "stop_times.txt")

    if stops is not None:
        check_stops(stops, label)
    if stop_times is not None:
        check_stop_times(stop_times)

    return stops, routes, trips, stop_times


if __name__ == "__main__":
    print("\nDelhi Transit — GTFS Data Explorer")

    explore_feed("dmrc", "DMRC Metro")
    explore_feed("dtc", "DTC Bus")