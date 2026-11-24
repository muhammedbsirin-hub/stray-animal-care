import io
import time

import customtkinter as ctk
import requests
import tkintermapview.map_widget as _mw
from tkintermapview import TkinterMapView

from app.config import ISTANBUL_CENTER, ROOT_DIR

USER_AGENT = "StrayAnimalCare/1.0 (university database course project)"
TILE_SERVER = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
CACHE_DIR = ROOT_DIR / ".tile_cache"
CACHE_DAYS = 30

LAT_MIN, LAT_MAX = 40.80, 41.45
LON_MIN, LON_MAX = 28.20, 29.60
MIN_ZOOM = 10


class _Response:

    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code
        self.raw = io.BytesIO(content)


class _CachedRequests:

    def __getattr__(self, name):
        return getattr(requests, name)

    @staticmethod
    def get(url, **kwargs):
        cache_file = None
        parts = url.rstrip(".png").split("/")[-3:]
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            cache_file = CACHE_DIR / parts[0] / parts[1] / f"{parts[2]}.png"
            if cache_file.exists() and time.time() - cache_file.stat().st_mtime < CACHE_DAYS * 86400:
                return _Response(cache_file.read_bytes())
        headers = dict(kwargs.pop("headers", None) or {})
        headers["User-Agent"] = USER_AGENT
        kwargs.pop("stream", None)
        kwargs.setdefault("timeout", 15)
        r = requests.get(url, headers=headers, **kwargs)
        if cache_file is not None and r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_bytes(r.content)
            except OSError:
                pass
        return _Response(r.content, r.status_code)


_mw.requests = _CachedRequests()


class IstanbulMapView(TkinterMapView):

    def set_zoom(self, zoom, relative_pointer_x=0.5, relative_pointer_y=0.5):
        super().set_zoom(max(zoom, MIN_ZOOM), relative_pointer_x, relative_pointer_y)

    def check_map_border_crossing(self):
        super().check_map_border_crossing()
        zoom = round(self.zoom)
        cx = (self.upper_left_tile_pos[0] + self.lower_right_tile_pos[0]) / 2
        cy = (self.upper_left_tile_pos[1] + self.lower_right_tile_pos[1]) / 2
        min_x, min_y = _mw.decimal_to_osm(LAT_MAX, LON_MIN, zoom)
        max_x, max_y = _mw.decimal_to_osm(LAT_MIN, LON_MAX, zoom)
        dx = min(max(cx, min_x), max_x) - cx
        dy = min(max(cy, min_y), max_y) - cy
        if dx or dy:
            self.upper_left_tile_pos = (self.upper_left_tile_pos[0] + dx, self.upper_left_tile_pos[1] + dy)
            self.lower_right_tile_pos = (self.lower_right_tile_pos[0] + dx, self.lower_right_tile_pos[1] + dy)


class MapPanel(ctk.CTkFrame):
    def __init__(self, master, zoom=11, **kw):
        super().__init__(master, corner_radius=10, **kw)
        self.map = IstanbulMapView(self, corner_radius=10)
        self.map.set_tile_server(TILE_SERVER, max_zoom=19)
        self.map.pack(fill="both", expand=True)
        self.map.set_position(*ISTANBUL_CENTER)
        self.map.set_zoom(zoom)
        self._pick_callback = None
        self._pick_marker = None
        self.map.add_left_click_map_command(self._clicked)

    def clear(self):
        self.map.delete_all_marker()
        self._pick_marker = None

    def add_marker(self, lat, lon, text="", color="#2e8b6e", command=None, data=None):
        return self.map.set_marker(lat, lon, text=text, data=data, command=command,
                                   marker_color_circle="white", marker_color_outside=color,
                                   text_color=color, font=("Segoe UI", 10, "bold"))

    def pick_location(self, callback):
        self._pick_callback = callback

    def stop_picking(self):
        self._pick_callback = None

    def show_pick(self, lat, lon, text="Selected place"):
        if self._pick_marker is not None:
            self._pick_marker.delete()
        self._pick_marker = self.map.set_marker(lat, lon, text=text, marker_color_circle="white",
                                                marker_color_outside="#c0392b", text_color="#c0392b")

    def _clicked(self, coords):
        if self._pick_callback:
            self.show_pick(*coords)
            cb = self._pick_callback
            cb(coords)
