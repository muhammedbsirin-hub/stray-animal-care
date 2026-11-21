"""Map panel (tkintermapview, OpenStreetMap data).  Needs an internet connection for the map tiles."""
import customtkinter as ctk
import requests
import tkintermapview.map_widget as _mw
from tkintermapview import TkinterMapView

from app.config import ISTANBUL_CENTER

# Tile servers block the library's default User-Agent ("TkinterMapView"),
# so every tile request of the library is sent with our own application name.
USER_AGENT = "StrayAnimalCare/1.0 (university database course project)"
TILE_SERVER = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


class _RequestsWithAgent:
    def __getattr__(self, name):
        return getattr(requests, name)

    @staticmethod
    def get(url, **kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        headers["User-Agent"] = USER_AGENT
        kwargs.setdefault("timeout", 15)
        return requests.get(url, headers=headers, **kwargs)


_mw.requests = _RequestsWithAgent()


class MapPanel(ctk.CTkFrame):
    def __init__(self, master, zoom=11, **kw):
        super().__init__(master, corner_radius=10, **kw)
        self.map = TkinterMapView(self, corner_radius=10)
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
        """The next click on the map calls callback((lat, lon))."""
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
