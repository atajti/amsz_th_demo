"""
Merge/deduplicate Google Timeline location points.

Clusters points that are close in space AND close in time into a single
representative "visit" point (centroid + time range), collapsing noisy
GPS clusters into one location.

Requires: pandas, numpy, scikit-learn
    pip install pandas numpy scikit-learn --break-system-packages

Usage:
    python merge_timeline_points.py input.json output.csv
"""

import json
import sys
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

EARTH_RADIUS_M = 6371000


def load_points(data):
    """
    Loads points from a Google Timeline export.
    Handles both the old 'Location History' format (list of dicts with
    latitudeE7/longitudeE7/timestamp) and the newer semanticSegments format.
    Adjust the parsing below to match your actual export structure.
    """
    # with open(path, "r", encoding="utf-8") as f:
    #     data = json.load(f)

    records = []

    # --- Old format: {"locations": [{"latitudeE7":..., "longitudeE7":..., "timestamp":...}]}
    if isinstance(data, dict) and "locations" in data:
        for loc in data["locations"]:
            lat = loc.get("latitudeE7")
            lon = loc.get("longitudeE7")
            ts = loc.get("timestamp")
            if lat is None or lon is None:
                continue
            records.append({
                "lat": lat / 1e7,
                "lon": lon / 1e7,
                "timestamp": pd.to_datetime(ts),
            })

    # --- Newer format: {"semanticSegments": [...]} with rawSignal points
    elif isinstance(data, dict) and "semanticSegments" in data:
        for seg in data["semanticSegments"]:
            for point in seg.get("timelinePath", []):
                latlon = point.get("point", "")
                if "," not in latlon:
                    continue
                lat_str, lon_str = latlon.replace("°", "").split(",")
                records.append({
                    "lat": float(lat_str),
                    "lon": float(lon_str),
                    "timestamp": pd.to_datetime(point.get("time")),
                })

    else:
        raise ValueError(
            "Unrecognized Timeline export format. "
            "Inspect the JSON top-level keys and adjust load_points()."
        )

    df = pd.DataFrame(records).dropna(subset=["lat", "lon", "timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def cluster_points(df, distance_m=50, min_samples=1, time_gap_minutes=30):
    """
    Merges points into clusters based on spatial proximity (DBSCAN with
    haversine distance) AND temporal continuity (a cluster is split if
    there's a gap larger than time_gap_minutes between consecutive points).

    distance_m: max distance (meters) between points to be considered the same visit
    min_samples: DBSCAN min_samples (1 = a single isolated point is its own cluster)
    time_gap_minutes: if consecutive points in a spatial cluster are separated
                       by more than this, treat them as separate visits
    """
    if df.empty:
        return df.assign(cluster=[])

    coords = np.radians(df[["lat", "lon"]].values)
    eps = distance_m / EARTH_RADIUS_M  # convert meters to radians for haversine

    db = DBSCAN(eps=eps, min_samples=min_samples, metric="haversine")
    df = df.copy()
    df["spatial_cluster"] = db.fit_predict(coords)

    # Split spatial clusters further by time gaps, so a location you visit
    # on two different days doesn't get merged into one giant blob.
    df = df.sort_values("timestamp").reset_index(drop=True)
    cluster_id = 0
    cluster_ids = []
    prev_spatial = None
    prev_time = None

    for _, row in df.iterrows():
        if prev_spatial is None:
            cluster_id = 0
        elif row["spatial_cluster"] != prev_spatial:
            cluster_id += 1
        elif (row["timestamp"] - prev_time) > pd.Timedelta(minutes=time_gap_minutes):
            cluster_id += 1
        cluster_ids.append(cluster_id)
        prev_spatial = row["spatial_cluster"]
        prev_time = row["timestamp"]

    df["cluster"] = cluster_ids
    return df


def summarize_clusters(df):
    """Collapses each cluster into one representative row (centroid + time range + point count)."""
    summary = (
        df.groupby("cluster")
        .agg(
            lat=("lat", "mean"),
            lon=("lon", "mean"),
            start_time=("timestamp", "min"),
            end_time=("timestamp", "max"),
            point_count=("timestamp", "count"),
        )
        .reset_index(drop=True)
    )
    return summary


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python merge_timeline_points.py input.json output.csv")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]

    df = load_points(input_path)
    print(f"Loaded {len(df)} raw points")

    clustered = cluster_points(df, distance_m=50, time_gap_minutes=30)
    merged = summarize_clusters(clustered)
    print(f"Merged into {len(merged)} deduplicated visit points")

    merged.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")