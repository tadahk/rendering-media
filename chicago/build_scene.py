"""Turn raw open data into a compact scene for the renderer.

Everything is projected to metres around the mouth of the Chicago River:
x = east, z = south (three.js convention, y = up).

Every estimate is labelled in scene["notes"], so the video description can say what is data and what is reconstruction.
"""
import gzip
import json
import math
import os
import random

HERE = os.path.dirname(__file__)
LAT0, LON0 = 41.8885, -87.6120
KX = math.cos(math.radians(LAT0)) * 111320.0
KZ = 110540.0
FIRE_END = 1871.78  # Oct 10, 1871
random.seed(1871)


def P(lon, lat):
    return [round((lon - LON0) * KX, 1), round(-(lat - LAT0) * KZ, 1)]


# --- hand-drawn, approximate polygons (lon, lat); marked as estimates in notes ---------------------------------------
# Burned district of 1871, simplified from published fire maps.
BURN = [(-87.6415, 41.8685), (-87.6330, 41.8700), (-87.6245, 41.8755), (-87.6237, 41.8885), (-87.6230, 41.9000),
        (-87.6260, 41.9100), (-87.6320, 41.9250), (-87.6480, 41.9250), (-87.6480, 41.9000), (-87.6420, 41.8900),
        (-87.6390, 41.8850), (-87.6425, 41.8770), (-87.6425, 41.8690)]
# Shoreline before the lakefront landfills (approximate, from 1860s–1870s maps): land is west of this line.
SHORE_1871 = [(-87.6200, 41.8400), (-87.6235, 41.8600), (-87.6245, 41.8750), (-87.6243, 41.8870),
              (-87.6232, 41.8890), (-87.6228, 41.9000), (-87.6255, 41.9100), (-87.6300, 41.9200), (-87.6330, 41.9350)]
FORT_DEARBORN = (-87.6245, 41.8874)
# River channels the OpenStreetMap water query misses (the main stem and North Branch), traced along their courses: centreline, width in m.
RIVER_EXTRA = [
    ([(-87.6378, 41.8866), (-87.6355, 41.8873), (-87.6300, 41.8878), (-87.6245, 41.8880), (-87.6200, 41.8882),
      (-87.6150, 41.8885), (-87.6112, 41.8888)], 62),
    ([(-87.6378, 41.8866), (-87.6386, 41.8900), (-87.6400, 41.8950), (-87.6430, 41.9000), (-87.6475, 41.9050),
      (-87.6510, 41.9100), (-87.6555, 41.9150), (-87.6585, 41.9210)], 48),
]
DEKOVEN_ORIGIN = (-87.6417, 41.8692)  # 137 W. DeKoven Street (near the O'Leary barn)
WATER_TOWER = (-87.6244, 41.8972)
FORKS = (-87.6375, 41.8868)  # Wolf Point, where the branches meet


def line_x_at(line, z, pick=max):
    """x where a projected polyline crosses depth z (pick=max for the most easterly crossing)."""
    xs = []
    for (x1, z1), (x2, z2) in zip(line, line[1:]):
        if min(z1, z2) <= z <= max(z1, z2) and z1 != z2:
            xs.append(x1 + (z - z1) / (z2 - z1) * (x2 - x1))
    return pick(xs) if xs else None


def fill_model(shore_now):
    """Landfill timing: 120 m blocks between the 1871 shore and today's shore, filled outward 1872-1925."""
    old = [P(x, y) for x, y in SHORE_1871]
    now = [P(x, y) for x, y in shore_now]
    z0, z1 = min(p[1] for p in old), max(p[1] for p in old)
    x71, xnow = [], []
    for i in range(128):
        z = z0 + (z1 - z0) * i / 127
        a = line_x_at(old, z, min) or 0.0
        b = line_x_at(now, z, max)
        x71.append(round(a, 1))
        xnow.append(round(b if b is not None and b > a else a, 1))
    return {"z0": z0, "z1": z1, "x71": x71, "xnow": xnow, "start": 1872, "end": 1925, "block": 120}


def fill_year(F, x, z):
    """Year the block containing (x, z) became land, or None if it was never lake (or is still lake)."""
    bx, bz = (math.floor(x / F["block"]) + 0.5) * F["block"], (math.floor(z / F["block"]) + 0.5) * F["block"]
    if not F["z0"] <= bz <= F["z1"]:
        return None
    f = (bz - F["z0"]) / (F["z1"] - F["z0"]) * 127
    i = min(126, int(f)); u = f - i
    a = F["x71"][i] * (1 - u) + F["x71"][i + 1] * u
    b = F["xnow"][i] * (1 - u) + F["xnow"][i + 1] * u
    fr = (bx - a) / max(b - a, 1.0)
    if fr < 0 or fr >= 1:
        return None
    return F["start"] + fr * (F["end"] - F["start"])


def inside(pt, poly):
    x, y = pt
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


def east_of(line, lon, lat):
    """True if (lon, lat) lies east of a north-south polyline (i.e. in the lake)."""
    for (x1, y1), (x2, y2) in zip(line, line[1:]):
        if min(y1, y2) <= lat <= max(y1, y2):
            t = (lat - y1) / (y2 - y1 + 1e-12)
            return lon > x1 + t * (x2 - x1)
    return False


def centroid(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def estimate_year(lon, lat, stories, burned):
    """Year for buildings with no year in the city data. Taller buildings are later; inside the burn area, after 1871."""
    if stories >= 30:
        lo, hi = 1960, 2022
    elif stories >= 12:
        lo, hi = 1905, 2015
    elif stories >= 5:
        lo, hi = 1880, 2010
    elif burned:
        lo, hi = 1872, 1896  # the burned district was largely rebuilt within twenty-five years
    else:
        lo, hi = 1876, 1930
    if burned:
        lo = max(lo, 1872)
    return round(random.uniform(lo, hi), 2)


def build():
    raw = json.load(gzip.open(os.path.join(HERE, "data", "buildings.json.gz")))
    osm = json.load(gzip.open(os.path.join(HERE, "data", "osm.json.gz")))
    notes = []
    segs = [w for w in osm["water"] if w[0] != w[-1]]
    segs = [w for w in segs if any(41.84 <= p[1] <= 41.94 and -87.68 <= p[0] <= -87.58 for p in w)]
    shore = chain(segs)
    F = fill_model(shore)
    blds, est = [], 0
    for ring, height, year, stories in raw["items"]:
        lon, lat = centroid(ring)
        stories = stories or 1
        burned = inside((lon, lat), BURN)
        h = height if height and height > 2 else max(3.5, stories * 3.9 + 1.5)
        if not year or year < 1800 or year > 2026:
            year, flag = estimate_year(lon, lat, stories, burned), 1
            est += 1
        else:
            flag = 0
            if burned and year <= 1871 and math.dist((lon, lat), WATER_TOWER) > 0.0015:
                year, flag = round(random.uniform(1872, 1880), 2), 1  # data says pre-fire, but the area burned
                est += 1
        pts = [P(x, y) for x, y in ring[:-1]]
        if pts:
            fy = fill_year(F, sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
            if fy is not None or east_of(SHORE_1871, lon, lat):
                year = max(year, (fy or 1890) + 2 + random.random() * 4)  # built on later landfill
        if len(pts) < 3:
            continue
        blds.append([pts, round(h, 1), round(year, 2), flag])
    notes.append(f"{len(blds)} buildings from City of Chicago footprints; {est} construction years estimated")

    # Lake: chain the Lake Michigan shoreline pieces (open ways) inside the study area, south to north.
    lake_today = [P(x, y) for x, y in shore] + [P(-87.50, shore[-1][1]), P(-87.50, shore[0][1])]
    lake_1871 = [P(x, y) for x, y in SHORE_1871] + [P(-87.50, SHORE_1871[-1][1]), P(-87.50, SHORE_1871[0][1])]
    notes.append("1871 shoreline and burned-district outline are simplified from period maps (approximate)")

    rivers = [[P(x, y) for x, y in w[:-1]] for w in osm["water"] if w[0] == w[-1] and len(w) > 8]
    for line, width in RIVER_EXTRA:
        rivers.append(buffer_line([P(x, y) for x, y in line], width / 2))
    notes.append("the river's main stem and North Branch are traced from their courses (OpenStreetMap water areas miss them)")
    parks = [[P(x, y) for x, y in w[:-1]] for w in osm["parks"] if w[0] == w[-1] and len(w) > 4]

    # spatial index of real buildings, so estimated older buildings retire when a real one takes their spot
    grid = {}
    for pts, h, year, flag in blds:
        cx = sum(p[0] for p in pts) / len(pts)
        cz = sum(p[1] for p in pts) / len(pts)
        grid.setdefault((int(cx // 30), int(cz // 30)), []).append((cx, cz, year))

    def replaced_by(px, pz, after):
        best = None
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for cx, cz, y in grid.get((int(px // 30) + dx, int(pz // 30) + dz), []):
                    if y > after and math.dist((cx, cz), (px, pz)) < 22 and (best is None or y < best):
                        best = y
        return best

    # 1871 wooden city: lots along today's streets (the grid was surveyed in the 1830s), inside the land of 1871.
    wood = []
    for kind, name, line in osm["roads"]:
        if kind in ("motorway", "trunk"):
            continue
        for (x1, y1), (x2, y2) in zip(line, line[1:]):
            a, b = P(x1, y1), P(x2, y2)
            L = math.dist(a, b)
            if L < 1:
                continue
            ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            nx, nz = -uz, ux
            step = 9.0
            n = int(L // step)
            for i in range(n):
                cx, cz = a[0] + ux * (i + 0.5) * step, a[1] + uz * (i + 0.5) * step
                for side in (-1, 1):
                    if random.random() < 0.61:  # half the earlier density: less clutter, more render time for the highlights
                        continue
                    px, pz = cx + nx * side * 17, cz + nz * side * 17
                    lon = LON0 + px / KX
                    lat = LAT0 - pz / KZ
                    if east_of(SHORE_1871, lon, lat) or any_water(rivers, px, pz):
                        continue
                    d = math.dist((lon, lat), FORKS) * 85.0  # km-ish from the forks
                    if d > 9:
                        continue
                    born = max(1831.2, 1831 + min(39, d * 6.5 + random.uniform(-3, 6)))  # after the 1830 survey
                    downtown = -87.6415 < lon < -87.6243 and 41.8755 < lat < 41.8875
                    floors = random.choice([3, 4, 4, 5]) if downtown else random.choice([1, 2, 2, 2, 3])
                    burned = inside((lon, lat), BURN)
                    ang = math.atan2(uz, ux)
                    w, dd = round(random.uniform(6, 8.5), 1), round(random.uniform(11, 18), 1)
                    if burned:
                        died = FIRE_END
                        # the rebuilt city: brick and stone downtown, frame houses further out
                        rb = FIRE_END + 0.2 + random.uniform(0, 2.5 + d * 2.5)
                        rfloors = random.choice([4, 5, 5, 6, 7]) if downtown else random.choice([2, 2, 3, 3, 4])
                        gone = replaced_by(px, pz, rb + 3) or (rb + random.uniform(40, 110))
                        wood.append([round(px, 1), round(pz, 1), round(ang, 3), w, dd, rfloors, round(rb, 2), round(gone, 2), 2])
                    else:
                        died = replaced_by(px, pz, born + 5) or (1871 + random.uniform(25, 80))
                    wood.append([round(px, 1), round(pz, 1), round(ang, 3), w, dd, floors, round(born, 2), round(died, 2),
                                 1 if downtown else 0])
    notes.append(f"{len(wood)} pre-fire and rebuilt-era buildings are procedural: placed along the 1830s street grid, sized from period norms")

    roads = []
    width = {"primary": 16, "secondary": 13, "tertiary": 11, "residential": 9, "unclassified": 8}
    for kind, name, line in osm["roads"]:
        if kind not in width:
            continue
        pts = [P(x, y) for x, y in line]
        lon, lat = line[len(line) // 2]
        d = math.dist((lon, lat), FORKS) * 85.0
        born = 1830 + d / 0.9 * 0.9 if d < 0.9 else 1831 + min(45, d * 6.5)  # 1830 plat drawn outward from the forks
        cx, cz = P(lon, lat)
        fy = fill_year(F, cx, cz)
        if fy is not None or east_of(SHORE_1871, lon, lat):
            born = max(born, (fy or 1895) + 1.5)  # streets on later landfill
        roads.append([pts, width[kind], round(born, 1)])
    notes.append(f"{len(roads)} streets from OpenStreetMap; opening years approximated by distance from the river forks")

    # 1803 groves: along the river branches and in scattered clusters on the wet prairie; never in the water
    trees = []
    river_pts = [p for r in rivers for p in r[::3]]
    cells = {}
    for p in river_pts:
        cells.setdefault((int(p[0] // 400), int(p[1] // 400)), []).append(p)
    def near_river(x, z, r=260):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for q in cells.get((int(x // 400) + dx, int(z // 400) + dz), []):
                    if abs(q[0] - x) < r and abs(q[1] - z) < r:
                        return True
        return False
    clusters = [(random.uniform(-9000, -1200), random.uniform(-8000, 7000), random.uniform(150, 450)) for _ in range(70)]
    for _ in range(140000):
        x, z = random.uniform(-9500, 0), random.uniform(-8500, 7500)
        lon, lat = LON0 + x / KX, LAT0 - z / KZ
        if east_of(SHORE_1871, lon, lat) or any_water(rivers, x, z):
            continue
        ok = near_river(x, z) or any(math.dist((x, z), (cx, cz)) < cr for cx, cz, cr in clusters) or random.random() < 0.03
        if ok:
            trees.append([round(x, 1), round(z, 1), round(random.uniform(10, 24), 1)])
        if len(trees) >= 26000:
            break
    notes.append(f"{len(trees)} trees for the 1803 landscape are illustrative, clustered along the river")

    scene = {
        "origin": [LON0, LAT0], "notes": notes, "buildings": blds, "wood": wood, "roads": roads, "trees": trees,
        "lake_today": lake_today, "lake_1871": lake_1871, "rivers": rivers, "parks": parks,
        "burn": [P(x, y) for x, y in BURN], "fill": F,
        "shore_today": [P(x, y) for x, y in shore], "shore_1871": [P(x, y) for x, y in SHORE_1871],
        "points": {"fort": P(*FORT_DEARBORN), "dekoven": P(*DEKOVEN_ORIGIN), "water_tower": P(*WATER_TOWER),
                   "forks": P(*FORKS)},
    }
    out = os.path.join(HERE, "data", "scene.json")
    with open(out, "w") as f:
        json.dump(scene, f, separators=(",", ":"))
    print("\n".join(notes), "\n", out, os.path.getsize(out) // 1024, "KB")


def buffer_line(pts, r):
    """A polygon of half-width r around a polyline (simple offset; fine for gentle curves)."""
    left, right = [], []
    for i, (x, z) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1
        nx, nz = -dz / L * r, dx / L * r
        left.append([round(x + nx, 1), round(z + nz, 1)])
        right.append([round(x - nx, 1), round(z - nz, 1)])
    return left + right[::-1]


_RIVER_BOXES = None


def any_water(rivers, x, z):
    global _RIVER_BOXES
    if _RIVER_BOXES is None:
        _RIVER_BOXES = [(min(p[0] for p in r), max(p[0] for p in r), min(p[1] for p in r), max(p[1] for p in r), r)
                        for r in rivers]
    for x0, x1, z0, z1, r in _RIVER_BOXES:
        if x0 <= x <= x1 and z0 <= z <= z1 and inside((x, z), r):
            return True
    return False


def chain(segs):
    """Join open shoreline pieces into one south-to-north line."""
    segs = [list(s) for s in segs]
    start = min(segs, key=lambda s: min(s[0][1], s[-1][1]))
    if start[0][1] > start[-1][1]:
        start.reverse()
    line = start
    segs.remove(start)
    while segs:
        end = line[-1]
        best = min(segs, key=lambda s: min(math.dist(end, s[0]), math.dist(end, s[-1])))
        if min(math.dist(end, best[0]), math.dist(end, best[-1])) > 0.003:
            break
        if math.dist(end, best[-1]) < math.dist(end, best[0]):
            best.reverse()
        line += best[1:]
        segs.remove(best)
    return line


if __name__ == "__main__":
    build()
