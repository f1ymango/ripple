"""Compact map annotations for the sourced May incident; no exact crash geocode."""
import base64
from html import escape
import math

import pydeck as pdk


def reported_area(message, geometry):
    """Locate the named eastbound flyover near the named landmark, approximately.

    TD supplies no coordinates. Project Yip Kan Street's source vertices onto
    the eastbound flyover geometry. This locates the reported area, not the
    crash point, and is deliberately limited to the reviewed demo prose.
    """
    text = message.english.casefold()
    if not all(name in text for name in (
            "wong chuk hang road flyover", "yip kan street", "aberdeen tunnel")):
        return None
    roads = geometry["roads"]
    flyover = [r for r in roads if r["road_name"].casefold().endswith(
        "wong chuk hang road flyover") and r["path"][-1][0] > r["path"][0][0]]
    landmark = [p for r in roads if r["road_name"].casefold().endswith("yip kan street")
                for p in r["path"]]
    candidates = []
    scale = math.cos(math.radians(22.25))
    for road in flyover:
        for a, b in zip(road["path"], road["path"][1:]):
            dx, dy = (b[0] - a[0]) * scale, b[1] - a[1]
            length = dx * dx + dy * dy
            if not length:
                continue
            for p in landmark:
                t = max(0, min(1, (((p[0] - a[0]) * scale * dx
                                   + (p[1] - a[1]) * dy) / length)))
                point = [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])]
                distance = math.hypot((p[0] - point[0]) * scale, p[1] - point[1]) * 111320
                candidates.append((distance, road["edge_id"], point))
    if not candidates:
        return None
    distance, edge, point = min(candidates)
    if distance > 150:
        return None
    return {"position": point, "edge_id": edge}


def annotation(message, cleared, geometry):
    area = reported_area(message, geometry)
    if area is None:
        return None
    if cleared:
        title, when, colour = "Clearance reported", cleared, [42, 120, 214]
    else:
        text = message.english.casefold()
        title = ("All lanes closed" if "all lanes" in text else
                 "Partial closure" if "part of the lanes" in text else
                 "Traffic accident")
        when, colour = message.published, [202, 89, 20]
    return {**area, "colour": colour, "arrow": "↓",
            "label": f"{title}\nTD report · {when:%H:%M}\nApprox. location",
            "tooltip": f"{title}\nTD report · {when:%H:%M} HKT\n"
                       "WCH flyover, near Yip Kan St\n"
                       "Approximate location\n"
                       "Full report in source card below."}


def layers(item):
    """Draw text, padded box and arrow together to keep their bounds aligned."""
    colour = "rgb(" + ",".join(str(c) for c in item["colour"]) + ")"
    lines = item["label"].splitlines()
    text = "".join(
        f'<text x="92" y="{22 + i * 21}">{escape(line)}</text>'
        for i, line in enumerate(lines))
    # One image gives the text fixed padding inside its box, without separate
    # glyph and background measurements after resizing.
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="184" height="106" '
           f'viewBox="0 0 184 106"><rect x="1" y="1" width="182" height="75" '
           f'rx="5" fill="white" fill-opacity="0.98" stroke="{colour}" '
           f'stroke-width="2"/><g font-family="Arial, sans-serif" font-size="14" '
           f'fill="#283242" text-anchor="middle">{text}</g>'
           f'<path d="M92 77V100 M86 94L92 102L98 94" fill="none" '
           f'stroke="{colour}" stroke-width="2" stroke-linecap="round" '
           f'stroke-linejoin="round"/></svg>')
    icon = {"url": "data:image/svg+xml;base64," + base64.b64encode(
                svg.encode("utf-8")).decode("ascii"),
            "width": 184, "height": 106, "anchorX": 92, "anchorY": 106,
            "mask": False}
    data = [{**item, "icon": icon}]
    return [
        pdk.Layer("ScatterplotLayer", id="incident-location", data=data,
                  get_position="position", get_fill_color="colour", get_radius=1,
                  radius_min_pixels=5, stroked=True, get_line_color=[255, 255, 255],
                  line_width_min_pixels=2, pickable=True),
        pdk.Layer("IconLayer", id="incident-callout", data=data,
                  get_position="position", get_icon="icon", get_size=106,
                  size_units='"pixels"', billboard=True, pickable=True),
    ]
