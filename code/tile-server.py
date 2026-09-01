"""tile-server"""
from flask import Flask, send_file, abort
import requests
from pathlib import Path
import time

app = Flask(__name__)

CACHE_DIR = Path("tile_cache")

# OpenStreetMap tile szerver
OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

# Cache könyvtár létrehozása
CACHE_DIR.mkdir(exist_ok=True)


def tile_path(z, x, y):
    return CACHE_DIR / str(z) / str(x) / f"{y}.png"


@app.route("/tiles/<int:z>/<int:x>/<int:y>.png")
def tiles(z, x, y):

    path = tile_path(z, x, y)

    # Már cache-ben van
    if path.exists():
        return send_file(
            path,
            mimetype="image/png",
            max_age=86400
        )

    # Könyvtár létrehozása
    path.parent.mkdir(parents=True, exist_ok=True)

    url = OSM_URL.format(z=z, x=x, y=y)

    headers = {
        "User-Agent": "TimelineViewer/1.0"
    }

    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        r.raise_for_status()

        with open(path, "wb") as f:
            f.write(r.content)

        # kis késleltetés, hogy ne terheljük az OSM-et
        time.sleep(0.1)

        return send_file(
            path,
            mimetype="image/png",
            max_age=86400
        )

    except Exception as e:
        print("Tile download error:", e)
        abort(404)


if __name__ == "__main__":
    print("Tile server running:")
    print("http://localhost:5000/tiles/{z}/{x}/{y}.png")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )