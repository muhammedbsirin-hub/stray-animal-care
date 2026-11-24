import customtkinter as ctk

from app.db import DbError
from app.ui.widgets import CARD, FONT, FONT_TITLE, MUTED, error


class Page(ctk.CTkFrame):
    title = ""
    subtitle = ""

    def __init__(self, master, main):
        super().__init__(master, fg_color="transparent")
        self.main = main
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=self.title, font=FONT_TITLE, anchor="w").grid(row=0, column=0, sticky="w")
        self.toolbar = ctk.CTkFrame(header, fg_color="transparent", height=10, width=10)
        self.toolbar.grid(row=0, column=1, sticky="e")
        if self.subtitle:
            ctk.CTkLabel(header, text=self.subtitle, font=FONT, text_color=MUTED, anchor="w", justify="left",
                         wraplength=900).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, pady=(12, 0))
        self.build()

    @property
    def session(self):
        return self.main.session

    def card(self, master=None, **kw):
        return ctk.CTkFrame(master or self.body, corner_radius=12, fg_color=CARD, **kw)

    def build(self):
        pass

    def refresh(self):
        pass

    def run(self, fn, *args):
        try:
            return True, fn(*args)
        except DbError as e:
            error(str(e))
            return False, None
