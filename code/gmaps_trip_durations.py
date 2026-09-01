"""
Get travel durations between two GPS coordinates using the Google Maps
Directions API, for driving, transit, bicycling, and walking.

Setup
-----
1. Get a Google Maps API key with the "Directions API" enabled:
   https://console.cloud.google.com/google/maps-apis/credentials
   (This uses standard API-key auth, not a personal Google account login —
   Google Maps has no concept of "logging in" for the Directions API, and
   scripting a sign-in to a personal account would violate Google's Terms
   of Service, so this uses the supported, official method instead.)

2. Install the client library:
   pip install googlemaps --break-system-packages

3. Set your API key as an environment variable:
   export GOOGLE_MAPS_API_KEY="your_key_here"

Usage
-----
   python gmaps_trip_durations.py
"""

import os
import googlemaps

MODES = ["driving", "transit", "bicycling", "walking"]


def get_durations(origin, destination, api_key=None, departure_time="now"):
    """
    origin / destination: (lat, lng) tuples
    Returns a dict like:
        {
            "driving":   {"duration_text": "12 mins", "duration_seconds": 720},
            "transit":   {"duration_text": "25 mins", "duration_seconds": 1500},
            "bicycling": {"duration_text": "18 mins", "duration_seconds": 1080},
            "walking":   {"duration_text": "55 mins", "duration_seconds": 3300},
        }
    A mode is omitted from the result if no route is found for it.
    """
    api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError(
            "No API key found. Set GOOGLE_MAPS_API_KEY or pass api_key=..."
        )

    client = googlemaps.Client(key=api_key)
    results = {}

    for mode in MODES:
        try:
            routes = client.directions(
                origin=origin,
                destination=destination,
                mode=mode,
                departure_time=departure_time,  # needed for accurate transit ETAs
            )
        except googlemaps.exceptions.ApiError as e:
            print(f"[{mode}] API error: {e}")
            continue

        if not routes:
            print(f"[{mode}] No route found from {origin} to {destination}")
            continue

        leg = routes[0]["legs"][0]
        results[mode] = {
            "duration_text": leg["duration"]["text"],
            "duration_seconds": leg["duration"]["value"],
        }
        df_record = {"transport": mode,
                     "transport_sec": leg["duration"]["value"],
                     "origin": origin,
                     "destination": destination}

    return df_record


if __name__ == "__main__":
    # Example: central Budapest -> Buda Castle
    origin = (47.4979, 19.0402)
    destination = (47.4964, 19.0398)

    durations = get_durations(origin, destination)

    print(f"\nTravel durations from {origin} to {destination}:\n")
    for mode, data in durations.items():
        print(f"  {mode:10s}: {data['duration_text']} ({data['duration_seconds']} s)")
