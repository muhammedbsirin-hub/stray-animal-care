"""Reusable widgets: tables, choice boxes, dialogs, photos, emoji images."""
import shutil
import uuid
from datetime import date, datetime
from pathlib import Path
from tkinter import messagebox, ttk

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageOps

from app.config import MEDIA_DIR, ROOT_DIR

FONT = ("Segoe UI", 13)
FONT_BOLD = ("Segoe UI", 13, "bold")
FONT_SMALL = ("Segoe UI", 11)
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUB = ("Segoe UI", 15, "bold")
PRIMARY = "#2e8b6e"
PRIMARY_DARK = "#226b55"
ACCENT = "#e67e22"
DANGER = "#c0392b"
MUTED = "#6b7280"
CARD = ("#ffffff", "#2b2b2b")


# ================================================================ formatting
def fmt(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    return str(value)


def nice(enum_value):
    """'DISCHARGED_TO_SHELTER' -> 'Discharged to shelter'"""
    if enum_value is None:
        return ""
    return str(enum_value).replace("_", " ").capitalize()


def time_ago(moment):
    if moment is None:
        return ""
    sec = int((datetime.now() - moment).total_seconds())
    if sec < 60:
        return "just now"
    if sec < 3600:
        return f"{sec // 60} min ago"
    if sec < 86400:
        return f"{sec // 3600} h ago"
    return f"{sec // 86400} days ago"


# ================================================================ messages
def info(text, title="Information"):
    messagebox.showinfo(title, text)


def error(text, title="Please check"):
    messagebox.showerror(title, text)


def confirm(text, title="Are you sure?"):
    return messagebox.askyesno(title, text)


# ================================================================ table
def style_tables():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", font=("Segoe UI", 11), rowheight=28, background="#ffffff",
                    fieldbackground="#ffffff", borderwidth=0)
    style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#e8efe9",
                    foreground="#1f2937", relief="flat", padding=(6, 6))
    style.map("Treeview", background=[("selected", PRIMARY)], foreground=[("selected", "#ffffff")])


BOOLEAN_COLUMNS = {"on_map", "has_children", "has_other_pets", "landlord_permission"}


class DataTable(ctk.CTkFrame):
    """columns: list of (key, heading, width).  Rows are dicts or objects."""

    def __init__(self, master, columns, height=10, key="id", on_select=None, on_double=None):
        super().__init__(master, fg_color="transparent")
        self.columns = columns
        self.key = key
        self.rows = {}
        self.tree = ttk.Treeview(self, columns=[c[0] for c in columns], show="headings", height=height,
                                 selectmode="browse")
        for k, heading, width in columns:
            self.tree.heading(k, text=heading, anchor="w")
            self.tree.column(k, width=width, minwidth=40, anchor="w", stretch=True)
        bar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=bar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        bar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree.tag_configure("red", foreground=DANGER)
        self.tree.tag_configure("orange", foreground=ACCENT)
        self.tree.tag_configure("muted", foreground=MUTED)
        self.tree.tag_configure("bold", font=("Segoe UI", 11, "bold"))
        self.tree.tag_configure("green", foreground=PRIMARY_DARK)
        if on_select:
            self.tree.bind("<<TreeviewSelect>>", lambda e: on_select(self.selected()))
        if on_double:
            self.tree.bind("<Double-1>", lambda e: self.selected() is not None and on_double(self.selected()))

    @staticmethod
    def _get(row, k):
        return row.get(k) if isinstance(row, dict) else getattr(row, k, None)

    def set_rows(self, rows, tag_fn=None, formatters=None):
        formatters = formatters or {}
        self.tree.delete(*self.tree.get_children())
        self.rows = {}
        for i, row in enumerate(rows):
            iid = str(self._get(row, self.key) if self._get(row, self.key) is not None else i)
            self.rows[iid] = row
            values = []
            for k, _, _ in self.columns:
                v = self._get(row, k)
                if k in formatters:
                    values.append(formatters[k](v))
                elif k.startswith("is_") or k in BOOLEAN_COLUMNS:
                    values.append("" if v is None else ("Yes" if v else "No"))
                else:
                    values.append(fmt(v))
            tags = tag_fn(row) if tag_fn else ()
            self.tree.insert("", "end", iid=iid, values=values, tags=tags if isinstance(tags, tuple) else (tags,))

    def selected(self):
        sel = self.tree.selection()
        return self.rows.get(sel[0]) if sel else None


# ================================================================ choice box
class ChoiceBox(ctk.CTkOptionMenu):
    """Option menu that remembers (value, label) pairs."""

    def __init__(self, master, options=(), placeholder="Select...", command=None, width=260, **kw):
        self._pairs = []
        self._placeholder = placeholder
        self._cb = command
        super().__init__(master, values=[placeholder], width=width, command=self._changed, dynamic_resizing=False,
                         fg_color="#ffffff", button_color=PRIMARY, button_hover_color=PRIMARY_DARK,
                         text_color="#111827", dropdown_font=FONT, font=FONT, **kw)
        self.set_options(options)

    def set_options(self, options, keep=False):
        old = self.value() if keep else None
        self._pairs = list(options)
        self.configure(values=[lbl for _, lbl in self._pairs] or [self._placeholder])
        self.set(self._placeholder)
        if old is not None:
            self.set_value(old)

    def _changed(self, label):
        if self._cb:
            self._cb(self.value())

    def value(self):
        label = self.get()
        for v, lbl in self._pairs:
            if lbl == label:
                return v
        return None

    def set_value(self, value):
        for v, lbl in self._pairs:
            if v == value:
                self.set(lbl)
                return
        self.set(self._placeholder)


# ================================================================ dialogs and layout
class Dialog(ctk.CTkToplevel):
    def __init__(self, master, title, width=520, height=560):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.minsize(380, 300)
        self.transient(master.winfo_toplevel())
        self.after(120, self._activate)

    def _activate(self):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:
            pass


def form_row(parent, row, label, widget, required=False, hint=None):
    ctk.CTkLabel(parent, text=label + (" *" if required else ""), font=FONT, anchor="w").grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=5)
    widget.grid(row=row, column=1, sticky="we", pady=5)
    if hint:
        ctk.CTkLabel(parent, text=hint, font=FONT_SMALL, text_color=MUTED, anchor="w").grid(
            row=row, column=2, sticky="w", padx=8)
    return widget


def entry(master, width=260, placeholder="", show=None):
    return ctk.CTkEntry(master, width=width, placeholder_text=placeholder, font=FONT, show=show)


def button(master, text, command, kind="primary", width=140):
    colors = {"primary": (PRIMARY, PRIMARY_DARK), "accent": (ACCENT, "#c96b17"), "danger": (DANGER, "#962d22"),
              "plain": ("#6b7280", "#4b5563")}
    fg, hover = colors[kind]
    return ctk.CTkButton(master, text=text, command=command, fg_color=fg, hover_color=hover, width=width, font=FONT_BOLD)


def text_value(widget):
    return widget.get("1.0", "end").strip() if isinstance(widget, ctk.CTkTextbox) else widget.get().strip()


# ================================================================ photos
def resolve_media(path):
    if not path:
        return None
    p = Path(path)
    return p if p.is_absolute() else ROOT_DIR / p


def photo_image(path, max_w=420, max_h=320):
    """CTkImage that fits in max_w x max_h, or None."""
    p = resolve_media(path)
    if p is None or not p.exists():
        return None
    img = Image.open(p)
    img = ImageOps.exif_transpose(img)
    img.thumbnail((max_w, max_h))
    return ctk.CTkImage(light_image=img, dark_image=img, size=img.size)


def set_label_image(label, image, text=""):
    """
    Safely changes the picture of a CTkLabel.  CustomTkinter does not clear the
    inner Tk label when image=None, which later crashes with 'image doesn't exist'.
    """
    if image is None:
        label.configure(image=None)
        label._label.configure(image="")
        label.configure(text=text)
    else:
        label.configure(image=image)
        label.configure(text=text)
    label.current_image = image


def store_photo(source_path, folder):
    """Copies a chosen picture into media/<folder>/ (resized) and returns the relative path for the database."""
    target_dir = MEDIA_DIR / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex[:16]}.jpg"
    try:
        img = Image.open(source_path)
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((1280, 1280))
        img.save(target_dir / name, "JPEG", quality=85)
    except Exception:
        shutil.copy(source_path, target_dir / name)
    return f"media/{folder}/{name}"


# ================================================================ emoji pictures (tk cannot draw colour emoji)
EMOJI_CHARS = {"HEART": "❤️", "CLAP": "\U0001F44F", "PAW": "\U0001F43E", "STRONG": "\U0001F4AA",
               "THANKS": "\U0001F64F"}
EMOJI_NAMES = {"HEART": "Love", "CLAP": "Applause", "PAW": "Paw", "STRONG": "Strong", "THANKS": "Thank you"}
_emoji_cache = {}


def emoji_image(code, size=28):
    key = (code, size)
    if key not in _emoji_cache:
        img = Image.new("RGBA", (110, 110), (0, 0, 0, 0))
        try:
            font = ImageFont.truetype("seguiemj.ttf", 80)
            ImageDraw.Draw(img).text((8, 4), EMOJI_CHARS[code], font=font, embedded_color=True)
            bbox = img.getbbox()
            if bbox:
                img = img.crop(bbox)
        except OSError:
            ImageDraw.Draw(img).text((30, 40), EMOJI_NAMES[code][:2], fill="black")
        _emoji_cache[key] = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    return _emoji_cache[key]
