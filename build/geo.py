"""Telecharge le GeoJSON des departements, extrait les 5 bretons, simplifie, projette en SVG."""
import json
import math
import urllib.request

URL = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
DEPTS = {"22": "Côtes-d'Armor", "29": "Finistère", "35": "Ille-et-Vilaine",
         "44": "Loire-Atlantique", "56": "Morbihan"}

data = json.load(urllib.request.urlopen(URL, timeout=60))
feats = [f for f in data["features"] if f["properties"]["code"] in DEPTS]
print("departements trouves:", sorted(f["properties"]["code"] for f in feats))

# bornes
minx = miny = 1e9
maxx = maxy = -1e9
polys = {}
for f in feats:
    code = f["properties"]["code"]
    geom = f["geometry"]
    coords = geom["coordinates"]
    if geom["type"] == "Polygon":
        coords = [coords]
    rings = [poly[0] for poly in coords]  # anneau exterieur seul
    polys[code] = rings
    for ring in rings:
        for x, y in ring:
            minx, miny = min(minx, x), min(miny, y)
            maxx, maxy = max(maxx, x), max(maxy, y)

print("bornes:", round(minx, 3), round(miny, 3), round(maxx, 3), round(maxy, 3))


def rdp_open(points, eps):
    if len(points) < 3:
        return points
    x0, y0 = points[0]
    x1, y1 = points[-1]
    dx, dy = x1 - x0, y1 - y0
    norm = math.hypot(dx, dy) or 1e-12
    dmax, imax = 0.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        d = abs(dy * px - dx * py + x1 * y0 - y1 * x0) / norm
        if d > dmax:
            dmax, imax = d, i
    if dmax > eps:
        return rdp_open(points[:imax + 1], eps)[:-1] + rdp_open(points[imax:], eps)
    return [points[0], points[-1]]


def rdp(points, eps):
    # anneau ferme : on coupe au point le plus eloigne du premier
    if len(points) > 2 and points[0] == points[-1]:
        points = points[:-1]
    if len(points) < 4:
        return points
    x0, y0 = points[0]
    k = max(range(len(points)), key=lambda i: (points[i][0] - x0) ** 2 + (points[i][1] - y0) ** 2)
    a = rdp_open(points[:k + 1], eps)
    b = rdp_open(points[k:] + [points[0]], eps)
    return a[:-1] + b


W, H = 640, 560
PAD = 18
# correction de la latitude (projection equirectangulaire ajustee)
lat0 = math.radians((miny + maxy) / 2)
sx = (W - 2 * PAD) / ((maxx - minx) * math.cos(lat0))
sy = (H - 2 * PAD) / (maxy - miny)
s = min(sx, sy)


def proj(x, y):
    return (PAD + (x - minx) * math.cos(lat0) * s,
            H - PAD - (y - miny) * s)


out = {}
for code, rings in polys.items():
    ring = max(rings, key=len)
    simp = rdp(ring, 0.012)
    pts = [proj(x, y) for x, y in simp]
    d = "M" + "L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + "Z"
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    out[code] = {"nom": DEPTS[code], "path": d, "label": [round(cx, 1), round(cy, 1)], "points": len(pts)}
    print(code, DEPTS[code], "points:", len(pts))

json.dump({"viewBox": f"0 0 {W} {H}", "depts": out},
          open("/opt/data/kanban/boards/brozapi/workspaces/t_a0972353/kervillage/build/carte.json", "w"),
          ensure_ascii=False)
print("carte.json ecrit")
