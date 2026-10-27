"""Write timeline.json for the 2-minute Chicago sample (reference_minute.md plus minute two).

The timeline is the single source every machine renders from: picture, camera, style, text, clip slot, narration and sound cues.
Edit here, run `python3 make_timeline.py`, commit both files.
"""
import json
import os

P = {"fort": [-1035.9, 121.6], "dekoven": [-2461.3, 2133.4], "forks": [-2113.2, 187.9]}


def near(at, dx, h, dz, ty=0):
    x, z = P[at]
    return {"pos": [x + dx, h, z + dz], "target": [x, ty, z]}


def key(t, pos, target, ease="inout", fov=38):
    return {"t": t, "pos": pos, "target": target, "ease": ease, "fov": fov}


moods = {
    "dusk": {"skyTop": "#2b3b6b", "horizon": "#e3a27e", "glow": "#ff7a35", "hemiSky": "#8a9ccc", "hemiGround": "#2f2a2a", "hemi": 1.35,
             "sun": "#ff9a55", "sunI": 2.0, "sunAz": 255, "sunEl": 10, "fogNear": 4500, "fogFar": 15000, "lights": 1.0, "exposure": 1.35, "lamps": 0.6},
    "night": {"skyTop": "#02040b", "horizon": "#1b2a4f", "glow": "#000000", "hemiSky": "#4a63a8", "hemiGround": "#0b0b10", "hemi": 1.1,
              "sun": "#9fb0ff", "sunI": 1.6, "sunAz": 150, "sunEl": 38, "fogNear": 4500, "fogFar": 16000, "lights": 0.0, "exposure": 1.9, "lamps": 1.0},
    "morning": {"skyTop": "#5d8fc9", "horizon": "#e2e8ea", "glow": "#ffd6a6", "hemiSky": "#bcd4ec", "hemiGround": "#5a5040", "hemi": 1.05,
                "sun": "#ffe2b8", "sunI": 2.4, "sunAz": 115, "sunEl": 20, "fogNear": 7000, "fogFar": 24000, "lights": 0.0, "exposure": 1.0, "lamps": 0.0},
    "haze": {"skyTop": "#7b98bd", "horizon": "#ead8bf", "glow": "#ffcf96", "hemiSky": "#d2d6dc", "hemiGround": "#5c5244", "hemi": 1.15,
             "sun": "#ffd9a8", "sunI": 2.2, "sunAz": 215, "sunEl": 28, "fogNear": 6000, "fogFar": 22000, "lights": 0.0, "exposure": 1.05, "lamps": 0.0},
}

# fort framed from the south-southwest: the river runs behind it into the lake on the right
FORT_VIEW = {"pos": [P["fort"][0] - 95, 52, P["fort"][1] + 165], "target": [P["fort"][0] + 35, 4, P["fort"][1] - 45]}
dk = near("dekoven", 380, 250, -300)
OVERVIEW = ([1500, 7500, 9500], [-5500, 0, 2200])  # high in the southeast: lake, city, canal and railroad in one frame
camera = [
    key(0, [1950, 2150, 1700], [-2000, 0, -100]),
    key(9, [1700, 2000, 1500], [-2000, 0, -100]),             # slow push while the opening line plays
    key(20, [2300, 2350, 2000], [-1800, 0, 100]),            # drift wider while the lakefront recedes
    key(26, [900, 1500, 2300], [-2200, 0, 1200]),            # settle facing southwest, toward DeKoven Street
    key(27.4, [850, 1450, 2350], [-2250, 0, 1250]),
    key(31.4, dk["pos"], dk["target"]),                       # focus beat: where the fire started
    key(37.4, dk["pos"], dk["target"]),
    key(40.6, [700, 2300, 3000], [-2400, 0, 900]),            # ease out as the page fades
    key(41.4, [700, 2300, 3000], [-2400, 0, 900]),
    key(41.45, [700, 1500, 1400], [-1600, 0, 100], "linear"), # cut while the page is blank
    key(46.0, [500, 1300, 1250], [-1500, 0, 100]),
    key(50.0, FORT_VIEW["pos"], FORT_VIEW["target"]),         # featured build: ease down to the empty site
    key(56.0, FORT_VIEW["pos"], FORT_VIEW["target"]),
    key(60.0, [1100, 1900, 1700], [-1900, 0, 0]),             # pull out with the fort standing
    key(66, [700, 1600, 1500], [-2100, 0, 200]),
    key(74, [900, 1700, 1600], [-2200, 0, 250]),              # the town at the forks
    key(79, [1400, 2100, 2100], [-1700, 0, 400]),
    key(88, *OVERVIEW),                                       # zoom out: canal and railroad need the whole region
    key(101, [1200, 7200, 9000], [-5800, 0, 2000], "linear"),
    key(114, [1700, 2400, 2500], [-1900, 0, 600]),            # back to the city as it fills in
    key(131, [500, 1500, 2700], [-1900, 0, 1500]),            # slow push toward the southwest for the summer of 1871
]

year = [
    {"t": 0, "v": 2026}, {"t": 9, "v": 2026},
    {"t": 13, "v": 1965, "ease": "in"},                       # accelerate out of today
    {"t": 23, "v": 1885, "ease": "linear"},                   # 8 years a second: each style change takes about 3 s
    {"t": 26, "v": 1873, "ease": "linear"},
    {"t": 27.4, "v": 1871.60, "ease": "out"},                 # passes the weeks after the fire in a fraction of a second
    {"t": 41.4, "v": 1871.60},
    {"t": 41.45, "v": 1803.0, "ease": "step"},
    {"t": 50.0, "v": 1803.4, "ease": "linear"},
    {"t": 56.0, "v": 1803.8, "ease": "linear"},               # the fort is born under the build clip (fortBorn 1803.6)
    {"t": 59, "v": 1804.5, "ease": "linear"},
    {"t": 61, "v": 1830.0, "ease": "inout"},
    {"t": 65, "v": 1830.95, "ease": "linear"},                # the survey grid draws outward from the forks
    {"t": 70.5, "v": 1833.6, "ease": "inout"},
    {"t": 76, "v": 1837.5, "ease": "linear"},
    {"t": 88, "v": 1848.2, "ease": "inout"},
    {"t": 101, "v": 1849.0, "ease": "linear"},                # time almost stops while canal and railroad are drawn
    {"t": 116, "v": 1869.8, "ease": "inout"},                 # then races: the city fills in along them
    {"t": 131, "v": 1871.5, "ease": "out"},
]

timeline = {
    "duration": 131,
    "fortBorn": 1803.6,
    "drift": {"degPerSec": 0.2, "bob": 0.03, "pauses": [[41.45, 45.8]]},  # orbit rests while the page draws in
    "stills": [12, 34, 92],
    "clearZones": [[P["fort"][0] - 95, P["fort"][1] + 165, 140]],   # no trees right in front of the fort camera
    "moods": moods,
    "camera": camera,
    "year": year,
    "points": {"canal": [-87.7300, 41.8105], "rail": [-87.7400, 41.8883], "river": [-87.6300, 41.8878], "lake": [-87.6150, 41.8800]},
    "features": [
        {"id": "canal", "kind": "canal", "width": 45,
         "pts": [[-87.6658, 41.8436], [-87.6760, 41.8380], [-87.6900, 41.8300], [-87.7100, 41.8200], [-87.7350, 41.8080], [-87.7650, 41.7980],
                 [-87.8000, 41.7880], [-87.8350, 41.7800], [-87.8800, 41.7650], [-87.9300, 41.7400]],
         "reveal": [{"t": 0, "v": 0}, {"t": 88.8, "v": 0}, {"t": 94.5, "v": 1, "ease": "inout"}]},
        {"id": "rail", "kind": "rail", "width": 22,
         "pts": [[-87.6395, 41.8890], [-87.6600, 41.8890], [-87.6900, 41.8889], [-87.7200, 41.8885], [-87.7600, 41.8880], [-87.8000, 41.8875], [-87.8370, 41.8870]],
         "reveal": [{"t": 0, "v": 0}, {"t": 94.8, "v": 0}, {"t": 100.0, "v": 1, "ease": "in"}]},
    ],
    "mood": [{"t": 0, "v": "dusk"}, {"t": 24, "v": "dusk"}, {"t": 28.5, "v": "night", "ease": "inout"}, {"t": 41.4, "v": "night"},
             {"t": 41.45, "v": "morning", "ease": "step"}, {"t": 104, "v": "morning"}, {"t": 122, "v": "haze", "ease": "inout"}, {"t": 131, "v": "haze"}],
    "fire": [{"t": 0, "v": 0}, {"t": 31.6, "v": 0}, {"t": 32.4, "v": 0.12, "ease": "out"}, {"t": 37.4, "v": 0.22, "ease": "linear"},
             {"t": 41.4, "v": 0.25}, {"t": 41.45, "v": 0, "ease": "step"}],
    "paper": [{"t": 0, "v": 0}, {"t": 37.6, "v": 0}, {"t": 41.0, "v": 1, "ease": "inout"}, {"t": 41.9, "v": 1}, {"t": 41.95, "v": 0, "ease": "step"}],
    "ink": [{"t": 0, "v": 1}, {"t": 41.4, "v": 1}, {"t": 41.45, "v": 0, "ease": "step"}, {"t": 42.0, "v": 0}, {"t": 46.0, "v": 1, "ease": "inout"}],
    "blueprint": [{"t": 0, "v": 0}, {"t": 61, "v": 0}, {"t": 64.5, "v": 1}, {"t": 68, "v": 1}, {"t": 71.5, "v": 0}],
    "ghost": [{"t": 0, "v": 0}, {"t": 15, "v": 0}, {"t": 17, "v": 1}, {"t": 27, "v": 1}, {"t": 30, "v": 0}],
    "fade": [{"t": 0, "v": 1}, {"t": 1.5, "v": 0, "ease": "out"}, {"t": 128, "v": 0}, {"t": 131, "v": 1, "ease": "inout"}],
    "overlays": [
        {"kind": "year", "t0": 9.5, "t1": 27.6},
        {"kind": "card", "t0": 17.0, "t1": 25.5, "text": "1870s–1920s", "sub": "the lakefront was filled in, block by block", "tone": "paper", "fade": 1.0},
        {"kind": "clock", "t0": 31.4, "t1": 39.6, "date": "Sunday, October 8, 1871", "hour": 21, "place": "DeKoven Street, Chicago",
         "y": 0.22, "tone": "dark", "fade": 1.0},
        {"kind": "title", "t0": 39.6, "t1": 45.0, "text": "CHICAGO", "sub": "The City That Burned", "fade": 1.0},
        {"kind": "label", "at": "fort", "t0": 45.4, "t1": 49.6, "text": "1803 · Fort Dearborn", "y": 6, "lift": 90, "fade": 1.0},
        {"kind": "label", "at": "river", "t0": 56.6, "t1": 60.4, "text": "Chicago River", "lift": 60, "fade": 1.0},
        {"kind": "label", "at": "lake", "t0": 56.6, "t1": 60.4, "text": "Lake Michigan", "lift": 40, "fade": 1.0},
        {"kind": "card", "t0": 65.5, "t1": 71.5, "text": "1830", "sub": "the town is surveyed", "tone": "paper", "fade": 1.0},
        {"kind": "card", "t0": 73.8, "t1": 81.5, "text": "Town of Chicago · 1833", "sub": "about 350 people · a city by 1837", "tone": "paper", "fade": 1.0},
        {"kind": "year", "t0": 76.5, "t1": 122},
        {"kind": "label", "at": "canal", "t0": 91.0, "t1": 100.5, "text": "Illinois & Michigan Canal · to the Mississippi", "lift": 70, "fade": 1.0},
        {"kind": "label", "at": "rail", "t0": 96.5, "t1": 104.5, "text": "Galena & Chicago Union Railroad", "lift": 70, "fade": 1.0},
        {"kind": "card", "t0": 117.0, "t1": 124.5, "text": "1870", "sub": "298,977 people · a city of wood", "tone": "paper", "fade": 1.0},
    ],
    "clips": [
        {"id": "fort", "t0": 50.0, "t1": 56.0, "dissolve": 0.8, "at": "fort",
         "prompt": "Illustrated architectural visualisation in soft graphite pencil on cream paper. "
                   "On an empty grassy bank where a river flows into a lake, a small 1803 frontier fort is built: first a faint pencil outline of the square stockade on the ground, "
                   "then timber posts rise, two square blockhouses and long low barracks frame up, and the drawing fills in with fine pencil detail. "
                   "Locked-off camera: the framing, horizon, river, lake and trees stay exactly where they are for the whole shot, and the water keeps its pale blue colour. "
                   "No cuts, no zoom, no change of view or background; the fort builds up in place. "
                   "Not photorealistic. No people, no animals, no text, no faces."},
    ],
    "narration": [
        {"id": "n1", "t": 0.8, "text": "Almost everything you're looking at was built after one night in October 1871."},
        {"id": "n1b", "t": 7.8, "text": "Let's go back."},
        {"id": "n2", "t": 40.2, "text": "This is the story of the city that burned, and what it did next."},
        {"id": "n3", "t": 50.6, "text": "In 1803 the United States Army built a small fort where a river met a lake."},
        {"id": "n4", "t": 65.6, "text": "In 1830 a surveyor drew a grid across the swamp."},
        {"id": "n5b", "t": 74.0, "text": "In 1833 about three hundred and fifty people incorporated the Town of Chicago. Four years later, it became a city."},
        {"id": "n6a", "t": 88.6, "text": "In 1848 a canal joined the lake to the Mississippi,"},
        {"id": "n6b", "t": 94.8, "text": "and the first train ran west."},
        {"id": "n6c", "t": 101.0, "text": "Chicago became the place where a continent's grain, timber and cattle changed hands."},
        {"id": "n7", "t": 116.5, "text": "By 1870, nearly three hundred thousand people. Most of their city was made of wood."},
        {"id": "n8", "t": 124.6, "text": "The summer of 1871 was dry."},
    ],
    "music": [{"id": "rise", "t0": 46.0, "t1": 131.0, "fadeIn": 4.0, "fadeOut": 4.0,
               "prompt": "Instrumental only, no vocals. A slow, hopeful orchestral dawn for a documentary about the founding of a city on a prairie by a lake: "
                         "warm sustained strings, soft piano, gentle French horn, no drums, no beat, quiet and spacious, building very gradually, key of D major, 60 bpm."}],
    "sound": [
        {"kind": "city", "t0": 0, "t1": 25, "gain": -30},
        {"kind": "wind", "t0": 0, "t1": 43.5, "gain": -32},
        {"kind": "fire", "t0": 31.6, "t1": 42.0, "gain": -31},
        {"kind": "pencil", "t0": 42.0, "t1": 46.0, "gain": -34},
        {"kind": "wind", "t0": 40.5, "t1": 131, "gain": -36},
        {"kind": "water", "t0": 42, "t1": 131, "gain": -38},
        {"kind": "pencil", "t0": 64.0, "t1": 68.0, "gain": -36},
        {"kind": "pencil", "t0": 88.8, "t1": 100.0, "gain": -38},
        {"kind": "town", "t0": 76, "t1": 131, "gain": -40},
    ],
}

out = os.path.join(os.path.dirname(__file__), "timeline.json")
with open(out, "w") as f:
    json.dump(timeline, f, indent=1, ensure_ascii=False)
print("wrote", out)
