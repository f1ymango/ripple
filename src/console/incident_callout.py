"""Compact map annotations for the sourced May incident; no exact crash geocode."""
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
        title = ("All lanes reported closed" if "all lanes" in text else
                 "Partial lane closure reported" if "part of the lanes" in text else
                 "Traffic accident reported")
        when, colour = message.published, [202, 89, 20]
    return {**area, "colour": colour, "arrow": "↓",
            "label": f"{title}\nWCH flyover · near Yip Kan St\nTD {when:%H:%M} · Approx. location",
            "tooltip": f"{message.incident_id} · archived TD report\n"
                       f"Approximate reported area on SUMO edge {area['edge_id']}; "
                       "not an exact crash coordinate.\n"
                       + ("TD reported clearance; earlier closure text is historical.\n" if cleared else "")
                       + message.english + "\n" + message.chinese}


def layers(item):
    """All elements share a geographic anchor, so the arrow follows pan/zoom."""
    data = [item]
    return [
        pdk.Layer("ScatterplotLayer", id="incident-location", data=data,
                  get_position="position", get_fill_color="colour", get_radius=1,
                  radius_min_pixels=5, stroked=True, get_line_color=[255, 255, 255],
                  line_width_min_pixels=2, pickable=True),
        pdk.Layer("TextLayer", id="incident-arrow", data=data,
                  get_position="position", get_text="arrow", get_size=30,
                  font_family='"Arial"', character_set='"auto"',
                  get_color="colour", get_pixel_offset=[0, -19],
                  get_text_anchor='"middle"', get_alignment_baseline='"center"'),
        pdk.Layer("TextLayer", id="incident-callout", data=data,
                  get_position="position", get_text="label", get_size=12,
                  font_family='"Arial"', character_set='"auto"',
                  get_color=[40, 50, 66], get_pixel_offset=[0, -40],
                  get_text_anchor='"middle"', get_alignment_baseline='"bottom"',
                  background=True, get_background_color=[255, 255, 255, 248],
                  background_padding=[10, 7], get_border_color="colour",
                  get_border_width=1, border_radius=6, pickable=True),
    ]
