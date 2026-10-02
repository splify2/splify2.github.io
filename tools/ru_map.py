#!/usr/bin/env python3
"""Контур России для карты на главной: assets/ru-map.json.

Источник — Natural Earth 10m, admin 0, точка зрения России (ne_10m_admin_0_countries_rus,
https://www.naturalearthdata.com/, общественное достояние). Проекция — коническая равноугольная
Ламберта (центральный меридиан 100° в. д., стандартные параллели 50° и 70°): в ней Россия
выглядит привычно и не рвётся на 180-м меридиане. Те же формулы с теми же числами — в
assets/home.js, по ним на карту ставятся города.

Запуск разовый, результат лежит в репозитории:
    pip install --target /tmp/pyshp pyshp
    PYTHONPATH=/tmp/pyshp python3 tools/ru_map.py ПУТЬ/ne_10m_admin_0_countries_rus.shp
"""
import json, math, os, sys

import shapefile

LON0, LAT1, LAT2, LAT0 = 100.0, 50.0, 70.0, 60.0
W = 1000.0            # ширина viewBox; высота — по контуру
PAD = 8.0
TOL = 0.55            # допуск упрощения, единиц viewBox
MIN_AREA = 6.0        # острова меньше — не рисуются, единиц² viewBox

r = math.radians
n = math.log(math.cos(r(LAT1)) / math.cos(r(LAT2))) / math.log(
    math.tan(math.pi / 4 + r(LAT2) / 2) / math.tan(math.pi / 4 + r(LAT1) / 2))
F = math.cos(r(LAT1)) * math.tan(math.pi / 4 + r(LAT1) / 2) ** n / n
RHO0 = F / math.tan(math.pi / 4 + r(LAT0) / 2) ** n


def proj(lon, lat):
    if lon < 0:
        lon += 360
    rho = F / math.tan(math.pi / 4 + r(lat) / 2) ** n
    t = n * r(lon - LON0)
    return rho * math.sin(t), RHO0 - rho * math.cos(t)


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a]; bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1e-12
        best, bi = -1, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            d = abs(dy * px - dx * py + bx * ay - by * ax) / L
            if d > best:
                best, bi = d, i
        if best > tol:
            keep[bi] = True
            stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]


def area(pts):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) / 2


def main(shp):
    rd = shapefile.Reader(shp)
    names = [f[0] for f in rd.fields[1:]]
    shape = next(s.shape for s in rd.iterShapeRecords() if dict(zip(names, s.record))['ADM0_A3'] == 'RUS')
    parts = list(shape.parts) + [len(shape.points)]
    rings = [[proj(*p) for p in shape.points[a:b]] for a, b in zip(parts, parts[1:])]
    xs = [x for g in rings for x, _ in g]; ys = [y for g in rings for _, y in g]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    k = (W - 2 * PAD) / (x1 - x0)
    H = round((y1 - y0) * k + 2 * PAD, 1)
    tx, ty = PAD - x0 * k, PAD + y1 * k          # y вниз: Y = ty - y·k
    out = []
    for g in rings:
        g = [(x * k + tx, ty - y * k) for x, y in g]
        if area(g) < MIN_AREA:
            continue
        # Кольцо замкнуто (первая точка = последней): упрощается двумя дугами — до самой
        # дальней от начала точки и обратно, иначе отрезок вырождается в точку.
        far = max(range(len(g)), key=lambda i: math.hypot(g[i][0] - g[0][0], g[i][1] - g[0][1]))
        g = dp(g[:far + 1], TOL)[:-1] + dp(g[far:], TOL)
        if len(g) < 4:
            continue
        out.append('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in g[:-1]) + 'Z')
    data = {
        'source': 'Natural Earth 10m admin 0, RUS point of view',
        'w': W, 'h': H, 'd': ''.join(out),
        'proj': {'lon0': LON0, 'n': n, 'F': F, 'rho0': RHO0, 'k': k, 'tx': tx, 'ty': ty},
    }
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'ru-map.json')
    with open(dst, 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    print(f'{len(out)} контуров, {os.path.getsize(dst)} байт, viewBox 0 0 {W:g} {H}')


if __name__ == '__main__':
    main(sys.argv[1])
