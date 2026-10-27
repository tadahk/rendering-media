"""Fetch the open data the Chicago model is built from. Runs on GitHub Actions (open internet).

Outputs content/chicago/data/*.json.gz:
  buildings.json.gz  City of Chicago building footprints in the study area: [[ring], height_m, year_built, stories]
  osm.json.gz        Lake/river water areas, coastline and street centrelines from OpenStreetMap (Overpass API)
  fields.txt         Column names of the city dataset, so the pipeline can be checked against reality
"""
import gzip
import json
import os
import sys
import time
import urllib.parse
import urllib.request

# Study area: the 1871 burned district plus the river mouth and lakefront, with margin.
SOUTH, WEST, NORTH, EAST = 41.850, -87.670, 41.928, -87.590
OUT = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "ai-town-content/1.0 (historical visualisation; contact admin@nascentia.net)"}


def get(url, data=None, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            print(f"  retry {i + 1}: {e}", flush=True)
            time.sleep(10 * (i + 1))
    raise SystemExit(f"failed: {url}")


def socrata_fields(dataset):
    meta = json.loads(get(f"https://data.cityofchicago.org/api/views/{dataset}.json"))
    return meta.get("name"), [(c.get("fieldName"), c.get("dataTypeName")) for c in meta.get("columns", [])]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def buildings(dataset):
    name, fields = socrata_fields(dataset)
    with open(os.path.join(OUT, "fields.txt"), "w") as f:
        f.write(f"{dataset}: {name}\n" + "\n".join(f"{a}\t{b}" for a, b in fields) + "\n")
    print(name, fields, flush=True)
    geom = next((a for a, b in fields if b in ("multipolygon", "polygon")), "the_geom")
    names = [a for a, _ in fields]
    pick = lambda *opts: next((o for o in opts if o in names), None)
    f_year = pick("year_built", "yearbuilt", "year_built_")
    f_stories = pick("stories", "no_stories", "num_stories")
    f_height = pick("height", "bldg_height", "max_height")
    out, offset, page = [], 0, 50000
    where = f"within_box({geom}, {NORTH}, {WEST}, {SOUTH}, {EAST})"
    while True:
        q = urllib.parse.urlencode({"$where": where, "$limit": page, "$offset": offset, "$order": ":id"})
        fc = json.loads(get(f"https://data.cityofchicago.org/resource/{dataset}.geojson?{q}"))
        feats = fc.get("features", [])
        for ft in feats:
            g, p = ft.get("geometry") or {}, ft.get("properties") or {}
            polys = g.get("coordinates") or []
            if g.get("type") == "Polygon":
                polys = [polys]
            stories = num(p.get(f_stories)) if f_stories else None
            height = num(p.get(f_height)) if f_height else None
            year = num(p.get(f_year)) if f_year else None
            for poly in polys:
                if not poly or len(poly[0]) < 4:
                    continue
                ring = [[round(x, 6), round(y, 6)] for x, y in poly[0]]
                out.append([ring, height, int(year) if year else None, stories])
        print(f"  buildings: {len(out)} (page at {offset})", flush=True)
        if len(feats) < page:
            break
        offset += page
    return out


def overpass():
    bbox = f"{SOUTH},{WEST},{NORTH},{EAST}"
    q = f"""[out:json][timeout:240];
(
  way["natural"="water"]({bbox});
  relation["natural"="water"]({bbox});
  way["waterway"="riverbank"]({bbox});
  way["natural"="coastline"](41.80,-87.70,41.98,-87.55);
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified)$"]({bbox});
  way["leisure"="park"]({bbox});
);
out geom;"""
    for host in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
        try:
            data = get(host, data=urllib.parse.urlencode({"data": q}).encode(), tries=2)
            j = json.loads(data)
            break
        except SystemExit:
            continue
    else:
        raise SystemExit("overpass failed")
    water, coast, roads, parks = [], [], [], []

    def line(el):
        return [[round(p["lon"], 6), round(p["lat"], 6)] for p in el.get("geometry", [])]

    for el in j["elements"]:
        t = el.get("tags", {})
        if el["type"] == "relation":
            for m in el.get("members", []):
                if m.get("role") == "outer" and m.get("geometry"):
                    water.append([[round(p["lon"], 6), round(p["lat"], 6)] for p in m["geometry"]])
            continue
        g = line(el)
        if t.get("natural") == "coastline":
            coast.append(g)
        elif t.get("natural") == "water" or t.get("waterway") == "riverbank":
            water.append(g)
        elif t.get("leisure") == "park":
            parks.append(g)
        elif "highway" in t:
            roads.append([t["highway"], t.get("name", ""), g])
    print(f"  water {len(water)} coast {len(coast)} roads {len(roads)} parks {len(parks)}", flush=True)
    return {"water": water, "coast": coast, "roads": roads, "parks": parks}


def save(name, obj):
    with gzip.open(os.path.join(OUT, name), "wt") as f:
        json.dump(obj, f, separators=(",", ":"))


if __name__ == "__main__":
    dataset = sys.argv[1] if len(sys.argv) > 1 else "syp8-uezg"
    save("osm.json.gz", overpass())
    save("buildings.json.gz", {"bbox": [SOUTH, WEST, NORTH, EAST], "dataset": dataset, "items": buildings(dataset)})
    print("done", flush=True)
