from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

from app import validators
from app.repositories import (EMOJIS, AdoptionRepository, AnimalRepository, CaseRepository, FeedingRepository,
                              LookupRepository, ShelterRepository)
from app.ui.map_panel import MapPanel
from app.ui.pages.base import Page
from app.ui.widgets import (ACCENT, CARD, DANGER, EMOJI_NAMES, FONT, FONT_BOLD, FONT_SMALL, FONT_SUB, MUTED, PRIMARY,
                            ChoiceBox, DataTable, Dialog, button, confirm, emoji_image, entry, error, fmt, form_row,
                            info, nice, photo_image, set_label_image, store_photo, text_value,
                            time_ago)

IMAGE_TYPES = [("Pictures", "*.jpg *.jpeg *.png *.bmp *.webp")]


class MapPage(Page):
    title = "Feeding map"
    subtitle = "Food left by volunteers in the last 24 hours. Your spots are orange. Click a pin to see the photo."

    def build(self):
        button(self.toolbar, "Refresh", self.refresh, kind="plain", width=100).pack(side="left", padx=4)
        button(self.toolbar, "+ Share a feeding spot", self.start_share, kind="accent", width=200).pack(side="left",
                                                                                                         padx=4)
        self.hint = ctk.CTkLabel(self.body, text="", font=FONT_BOLD, text_color=ACCENT, anchor="w")
        self.hint.pack(fill="x")
        self.map = MapPanel(self.body)
        self.map.pack(fill="both", expand=True, pady=(4, 0))

    def refresh(self):
        self.map.clear()
        self.map.stop_picking()
        self.hint.configure(text="")
        posts = FeedingRepository.active_posts()
        for p in posts:
            own = p.user_id == self.session.user_id
            self.map.add_marker(p.latitude, p.longitude, text="You" if own else p.username,
                                color=ACCENT if own else PRIMARY, data=p.post_id,
                                command=lambda m: PostDialog(self, m.data))
        self.hint.configure(text=f"{len(posts)} feeding spots in the last 24 hours", text_color=MUTED)

    def start_share(self):
        self.hint.configure(text="Click on the map where you left the food.", text_color=ACCENT)
        self.map.pick_location(self._picked)

    def _picked(self, coords):
        self.map.stop_picking()
        NewPostDialog(self, coords[0], coords[1], on_saved=self.refresh)


class NewPostDialog(Dialog):
    def __init__(self, page, lat, lon, on_saved):
        super().__init__(page, "Share a feeding spot", 520, 600)
        self.page, self.lat, self.lon, self.on_saved = page, lat, lon, on_saved
        self.photo_path = None
        ctk.CTkLabel(self, text="Share a feeding spot", font=FONT_SUB).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(self, text=f"Location: {lat:.5f}, {lon:.5f}", font=FONT_SMALL, text_color=MUTED).pack(
            anchor="w", padx=20)
        self.preview = ctk.CTkLabel(self, text="No photo yet", width=460, height=300, fg_color=("#eef1ef", "#333"),
                                    corner_radius=10)
        self.preview.pack(padx=20, pady=12)
        button(self, "Choose photo *", self.choose, kind="plain", width=160).pack(padx=20, anchor="w")
        ctk.CTkLabel(self, text="Note (optional)", font=FONT).pack(anchor="w", padx=20, pady=(12, 2))
        self.note = entry(self, width=460, placeholder="e.g. Left dry food and fresh water")
        self.note.pack(padx=20)
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(pady=18)
        button(bar, "Cancel", self.destroy, kind="plain", width=110).pack(side="left", padx=6)
        button(bar, "Share", self.save, kind="accent", width=140).pack(side="left", padx=6)

    def choose(self):
        path = filedialog.askopenfilename(parent=self, title="Choose a photo", filetypes=IMAGE_TYPES)
        if path:
            img = photo_image(path, 460, 300)
            if img is None:
                error("This file could not be opened as a picture.")
                return
            self.photo_path = path
            set_label_image(self.preview, img)

    def save(self):
        if not self.photo_path:
            error("Please add a photo of the feeding spot.")
            return
        note = self.note.get().strip()
        if len(note) > 255:
            error("The note can be at most 255 characters.")
            return
        stored = store_photo(self.photo_path, "posts")
        ok, _ = self.page.run(FeedingRepository.create_post, self.page.session.user_id, self.lat, self.lon, stored,
                              note)
        if ok:
            self.destroy()
            info("Thank you! Your feeding spot is on the map for 24 hours.")
            self.on_saved()


class PostDialog(Dialog):

    def __init__(self, page, post_id):
        super().__init__(page, "Feeding spot", 540, 660)
        self.page, self.post_id = page, post_id
        self.me = page.session.user_id
        post = FeedingRepository.get(post_id)
        if post is None or post["is_deleted"]:
            ctk.CTkLabel(self, text="This post is not available any more.", font=FONT).pack(pady=40)
            return
        self.own = post["user_id"] == self.me
        self.expired = not post["on_map"]
        self.read_only = self.own or self.expired or not page.session.is_volunteer()
        img = photo_image(post["photo_path"], 500, 330)
        ctk.CTkLabel(self, image=img, text="" if img else "(photo not found)").pack(padx=20, pady=(18, 8))
        ctk.CTkLabel(self, text=f"{post['full_name']}  (@{post['username']})", font=FONT_SUB).pack(anchor="w", padx=20)
        ctk.CTkLabel(self, text=f"{time_ago(post['posted_at'])}  ·  {fmt(post['posted_at'])}", font=FONT_SMALL,
                     text_color=MUTED).pack(anchor="w", padx=20)
        if post["note"]:
            ctk.CTkLabel(self, text=post["note"], font=FONT, wraplength=480, justify="left").pack(anchor="w", padx=20,
                                                                                                 pady=(6, 0))
        self.summary = ctk.CTkFrame(self, fg_color="transparent")
        self.summary.pack(anchor="w", padx=16, pady=(10, 0))
        self.choice = ctk.CTkFrame(self, fg_color=CARD, corner_radius=10)
        self.choice.pack(fill="x", padx=20, pady=12)
        self.draw()

    def draw(self):
        for w in self.summary.winfo_children() + self.choice.winfo_children():
            w.destroy()
        counts = FeedingRepository.reaction_summary(self.post_id)
        if not counts:
            ctk.CTkLabel(self.summary, text="No emoji yet.", font=FONT_SMALL, text_color=MUTED).pack(side="left", padx=4)
        for code in EMOJIS:
            if counts.get(code):
                ctk.CTkLabel(self.summary, image=emoji_image(code, 22), text=f" {counts[code]}", compound="left",
                             font=FONT_BOLD).pack(side="left", padx=6)
        if self.read_only:
            if self.own:
                head = "This is your post. Supporters:"
            elif self.expired and self.page.session.is_volunteer():
                head = "This post is older than 24 hours, emojis cannot be changed. Supporters:"
            else:
                head = "Supporters:"
            ctk.CTkLabel(self.choice, text=head, font=FONT_BOLD, wraplength=470, justify="left").pack(
                anchor="w", padx=12, pady=(10, 4))
            people = FeedingRepository.reactions(self.post_id)
            text = "\n".join(f"{EMOJI_NAMES[r['emoji']]} – @{r['username']}" for r in people) or "Nobody yet."
            ctk.CTkLabel(self.choice, text=text, font=FONT_SMALL, justify="left").pack(anchor="w", padx=12,
                                                                                      pady=(0, 10))
            return
        mine = FeedingRepository.my_reaction(self.post_id, self.me)
        ctk.CTkLabel(self.choice, text="Support this volunteer:", font=FONT_BOLD).pack(anchor="w", padx=12,
                                                                                       pady=(10, 4))
        row = ctk.CTkFrame(self.choice, fg_color="transparent")
        row.pack(anchor="w", padx=8, pady=(0, 6))
        for code in EMOJIS:
            ctk.CTkButton(row, image=emoji_image(code, 30), text="", width=56, height=48, corner_radius=12,
                          fg_color=PRIMARY if code == mine else ("#f1f5f2", "#3a3a3a"),
                          hover_color=("#d9eee4", "#444"), command=lambda c=code: self.react(c)).pack(side="left",
                                                                                                    padx=4)
        if mine:
            ctk.CTkButton(self.choice, text="Remove my emoji", fg_color="transparent", text_color=DANGER, font=FONT_SMALL,
                          hover_color=("#fbeaea", "#3a2a2a"), command=self.remove).pack(anchor="w", padx=8,
                                                                                         pady=(0, 8))

    def react(self, code):
        ok, _ = self.page.run(FeedingRepository.react, self.post_id, self.me, code)
        if ok:
            self.draw()

    def remove(self):
        self.page.run(FeedingRepository.remove_reaction, self.post_id, self.me)
        self.draw()


class MyPostsPage(Page):
    title = "My posts"
    subtitle = "Your feeding photo history and the emojis you received. Posts stay on the map for 24 hours."

    def build(self):
        button(self.toolbar, "Delete selected post", self.delete, kind="danger", width=180).pack(side="left", padx=4)
        self.body.grid_columnconfigure(0, weight=3)
        self.body.grid_columnconfigure(1, weight=2)
        self.body.grid_rowconfigure(0, weight=1)
        self.table = DataTable(self.body, [("posted_at", "Date", 140), ("note", "Note", 260),
                                           ("on_map", "On map now", 90), ("reactions", "Emojis", 70)],
                               height=18, key="post_id", on_select=self.show)
        self.table.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        side = self.card()
        side.grid(row=0, column=1, sticky="nsew")
        self.photo = ctk.CTkLabel(side, text="Select a post", text_color=MUTED, height=260)
        self.photo.pack(padx=12, pady=12)
        self.reactions = DataTable(side, [("username", "From", 140), ("emoji_name", "Emoji", 100),
                                          ("reacted_at", "When", 130)], height=8, key="username")
        self.reactions.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def refresh(self):
        rows = FeedingRepository.my_posts(self.session.user_id)
        for r in rows:
            r["on_map"] = bool(r["on_map"])
        self.table.set_rows(rows, tag_fn=lambda r: ("green",) if r["on_map"] else ())
        set_label_image(self.photo, None, "Select a post")
        self.reactions.set_rows([])

    def show(self, row):
        if not row:
            return
        img = photo_image(row["photo_path"], 380, 260)
        set_label_image(self.photo, img, "" if img else "(photo not found)")
        people = FeedingRepository.reactions(row["post_id"])
        for p in people:
            p["emoji_name"] = EMOJI_NAMES[p["emoji"]]
        self.reactions.set_rows(people)

    def delete(self):
        row = self.table.selected()
        if not row:
            error("Select one of your posts first.")
            return
        if confirm("Delete this feeding post? It will disappear from the map."):
            self.run(FeedingRepository.delete_post, row["post_id"], self.session.user_id)
            self.refresh()


class MyReactionsPage(Page):
    title = "My emojis"
    subtitle = ("Emojis you gave to other volunteers. They can be changed or removed only while the post is on "
                "the map (24 hours).")

    def build(self):
        button(self.toolbar, "Change emoji", self.change, kind="plain", width=140).pack(side="left", padx=4)
        button(self.toolbar, "Remove emoji", self.remove, kind="danger", width=140).pack(side="left", padx=4)
        self.table = DataTable(self.body, [("reacted_at", "Given at", 140), ("emoji_name", "Emoji", 110),
                                           ("owner", "Volunteer", 160), ("posted_at", "Post date", 140),
                                           ("on_map", "On map", 80), ("note", "Post note", 320)],
                               height=18, key="post_id", on_double=lambda r: PostDialog(self, r["post_id"]))
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        rows = FeedingRepository.my_given_reactions(self.session.user_id)
        for r in rows:
            r["emoji_name"] = EMOJI_NAMES[r["emoji"]]
        self.table.set_rows(rows, tag_fn=lambda r: () if r["on_map"] else ("muted",))

    def _editable_row(self):
        row = self.table.selected()
        if not row:
            error("Select an emoji first.")
            return None
        if not row["on_map"]:
            error("This post is older than 24 hours and is no longer on the map, so its emoji cannot be changed.")
            return None
        return row

    def change(self):
        row = self._editable_row()
        if row:
            dlg = PostDialog(self, row["post_id"])
            dlg.bind("<Destroy>", lambda e: self.refresh() if e.widget is dlg else None)

    def remove(self):
        row = self._editable_row()
        if row:
            self.run(FeedingRepository.remove_reaction, row["post_id"], self.session.user_id)
            self.refresh()


class ReportInjuryPage(Page):
    title = "Report an injured animal"
    subtitle = "Choose a clinic: a veterinarian of the current shift is assigned at random."

    def build(self):
        self.location = None
        self.body.grid_columnconfigure(1, weight=1)
        self.body.grid_rowconfigure(0, weight=1)
        left = self.card()
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        f = ctk.CTkFrame(left, fg_color="transparent")
        f.pack(padx=16, pady=14)
        self.species = form_row(f, 0, "Species", ChoiceBox(f), True)
        self.age = form_row(f, 1, "Approx. age (weeks)", entry(f, placeholder="optional, e.g. 30"))
        self.color = form_row(f, 2, "Color", entry(f, placeholder="optional"))
        self.condition = form_row(f, 3, "Condition", ctk.CTkTextbox(f, width=260, height=90, font=FONT), True)
        self.district = form_row(f, 4, "District", ChoiceBox(f, placeholder="(optional)"))
        self.clinic = form_row(f, 5, "Clinic", ChoiceBox(f, command=lambda v: self.show_clinic()), True)
        self.shift_label = ctk.CTkLabel(left, text="", font=FONT_BOLD, text_color=PRIMARY, justify="left")
        self.shift_label.pack(anchor="w", padx=16)
        button(left, "Send report", self.submit, kind="accent", width=200).pack(anchor="w", padx=16, pady=16)
        right = ctk.CTkFrame(self.body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        self.map_hint = ctk.CTkLabel(right, text="Click on the map where you found the animal (red pin).",
                                     font=FONT, text_color=MUTED, anchor="w")
        self.map_hint.pack(fill="x")
        self.map = MapPanel(right, zoom=11)
        self.map.pack(fill="both", expand=True, pady=(4, 0))

    def refresh(self):
        self.species.set_options([(s["species_id"], s["species_name"]) for s in LookupRepository.species()], keep=True)
        self.district.set_options([(d["district_id"], d["district_name"]) for d in LookupRepository.districts()],
                                  keep=True)
        self.clinics = LookupRepository.clinics()
        self.clinic.set_options([(c["clinic_id"], f"{c['clinic_name']} ({c['district_name']})") for c in self.clinics],
                                keep=True)
        self.map.clear()
        for c in self.clinics:
            self.map.add_marker(c["latitude"], c["longitude"], text=c["clinic_name"], color="#2563eb")
        if self.location:
            self.map.show_pick(*self.location, text="Animal")
        self.map.pick_location(self._picked)
        now = datetime.now()
        shift = "Morning shift (07:00-16:59)" if 7 <= now.hour < 17 else "Evening shift (17:00-06:59)"
        self.shift_label.configure(text=f"Now: {now:%H:%M}  →  {shift}")

    def show_clinic(self):
        c = next((c for c in self.clinics if c["clinic_id"] == self.clinic.value()), None)
        if c:
            self.map.map.set_position(c["latitude"], c["longitude"])
            self.map.map.set_zoom(13)

    def _picked(self, coords):
        self.location = coords
        self.map.show_pick(*coords, text="Animal")
        self.map.pick_location(self._picked)
        self.map_hint.configure(text=f"Location selected: {coords[0]:.5f}, {coords[1]:.5f}", text_color=PRIMARY)

    def submit(self):
        condition = text_value(self.condition)
        err = validators.first_error(
            None if self.species.value() else "Please choose the species.",
            validators.integer(self.age.get(), "Age (weeks)", 0, 1500, optional=True),
            validators.min_length(condition, "Condition", 5),
            None if len(condition) <= 500 else "Condition can be at most 500 characters.",
            None if self.clinic.value() else "Please choose a clinic.")
        if err:
            error(err)
            return
        lat, lon = self.location if self.location else (None, None)
        ok, result = self.run(CaseRepository.create_report, self.session.user_id, self.species.value(),
                              int(self.age.get()) if self.age.get().strip() else None, self.color.get().strip(),
                              condition, self.district.value(), lat, lon, self.clinic.value())
        if not ok:
            return
        _, vet_name, shift = result
        clinic = next(c for c in self.clinics if c["clinic_id"] == self.clinic.value())
        info(f"Please take the animal to:\n{clinic['clinic_name']}\n{clinic['address']}"
             f"\n\nYour veterinarian: {vet_name} ({shift.lower()} shift)", "Veterinarian assigned")
        for w in (self.age, self.color):
            w.delete(0, "end")
        self.condition.delete("1.0", "end")
        self.location = None
        self.map_hint.configure(text="Click on the map where you found the animal (red pin).", text_color=MUTED)
        self.main.refresh_badge()
        self.refresh()


class MyReportsPage(Page):
    title = "My reports"
    subtitle = "Injured animals you reported and what happened to them."

    def build(self):
        self.table = DataTable(self.body, [("reported_at", "Reported", 140),
                                           ("species_name", "Species", 70), ("clinic_name", "Clinic", 230),
                                           ("vet_name", "Veterinarian", 170), ("shift", "Shift", 80),
                                           ("status", "Status", 110), ("result", "Result", 170)],
                               height=18, key="report_id")
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        rows = CaseRepository.my_reports(self.session.user_id)
        self.table.set_rows(rows, tag_fn=lambda r: {"PENDING": ("orange",), "NOT_ARRIVED": ("muted",)}.get(r.status, ()),
                            formatters={"status": nice, "shift": nice, "result": nice})


class AdoptPage(Page):
    title = "Adopt a friend"
    subtitle = "Choose a shelter, meet its animals and send an application."

    def build(self):
        self.shelter = None
        self.back_btn = button(self.toolbar, "← All shelters", self.show_shelters, kind="plain", width=140)
        self.view_btn = button(self.toolbar, "Show animals", self.open_shelter, width=150)
        self.view_btn.pack(side="left", padx=4)
        self.shelters_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        self.shelters = DataTable(self.shelters_frame, [
            ("shelter_name", "Shelter", 280), ("district_name", "District", 110), ("address", "Address", 330),
            ("accepted_species", "Accepts", 90), ("animal_count", "Animals", 70)],
            height=20, key="shelter_id", on_double=lambda r: self.open_shelter())
        self.shelters.pack(fill="both", expand=True)
        self.animals_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        self.animals_frame.grid_columnconfigure(0, weight=3)
        self.animals_frame.grid_columnconfigure(1, weight=2)
        self.animals_frame.grid_rowconfigure(1, weight=1)
        self.shelter_title = ctk.CTkLabel(self.animals_frame, text="", font=FONT_SUB, anchor="w", justify="left")
        self.shelter_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.animals = DataTable(self.animals_frame, [
            ("display_name", "Name", 110), ("species_name", "Species", 70), ("breed_name", "Breed", 130),
            ("sex", "Sex", 80), ("age_label", "Age", 90), ("color", "Color", 100), ("is_neutered", "Neutered", 70)],
            height=16, key="animal_id", on_select=self.show_animal)
        self.animals.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.detail = ctk.CTkScrollableFrame(self.animals_frame, fg_color=CARD, corner_radius=12)
        self.detail.grid(row=1, column=1, sticky="nsew")
        self.show_shelters()

    def refresh(self):
        self.shelters.set_rows(ShelterRepository.summaries())
        if self.shelter:
            self.animals.set_rows(AnimalRepository.available_in_shelter(self.shelter.shelter_id),
                                  formatters={"sex": nice})

    def show_shelters(self):
        self.shelter = None
        self.animals_frame.pack_forget()
        self.back_btn.pack_forget()
        self.view_btn.pack(side="left", padx=4)
        self.shelters_frame.pack(fill="both", expand=True)

    def open_shelter(self):
        s = self.shelters.selected()
        if s is None:
            error("Select a shelter first.")
            return
        self.shelter = s
        self.shelters_frame.pack_forget()
        self.view_btn.pack_forget()
        self.back_btn.pack(side="left", padx=4)
        self.animals_frame.pack(fill="both", expand=True)
        self.shelter_title.configure(text=f"{s.shelter_name}\n{s.address}  ·  {s.phone}  ·  "
                                          f"accepts: {s.accepted_species}")
        self.animals.set_rows(AnimalRepository.available_in_shelter(s.shelter_id), formatters={"sex": nice})
        self._clear_detail("Select an animal to see its details and history.")

    def _clear_detail(self, text):
        for w in self.detail.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.detail, text=text, font=FONT, text_color=MUTED, wraplength=360).pack(pady=30)

    def show_animal(self, a):
        if a is None:
            return
        for w in self.detail.winfo_children():
            w.destroy()
        icon = "\U0001F431" if a.species_name == "Cat" else "\U0001F436"
        ctk.CTkLabel(self.detail, text=f"{icon}  {a.display_name}", font=FONT_SUB).pack(anchor="w", padx=12,
                                                                                         pady=(8, 2))
        facts = (f"{a.species_name} · {a.breed_name} · {nice(a.sex)}\nAge: {a.age_label}"
                 f"\nColor: {a.color or '-'}\nNeutered: {'Yes' if a.is_neutered else 'No'}"
                 f"\nFollowed by: {a.responsible_vet_name or '-'}")
        ctk.CTkLabel(self.detail, text=facts, font=FONT, justify="left").pack(anchor="w", padx=12)
        if a.description:
            ctk.CTkLabel(self.detail, text=a.description, font=FONT_SMALL, text_color=MUTED, wraplength=360,
                         justify="left").pack(anchor="w", padx=12, pady=(6, 0))
        ctk.CTkLabel(self.detail, text="Health history", font=FONT_BOLD).pack(anchor="w", padx=12, pady=(12, 2))
        treatments = CaseRepository.treatments_of_animal(a.animal_id)
        txt = "\n".join(f"• {fmt(t['started_at'])[:10]}  {t['diagnosis']} ({nice(t['outcome'])})"
                        for t in treatments) or "No treatment records."
        ctk.CTkLabel(self.detail, text=txt, font=FONT_SMALL, justify="left", wraplength=360).pack(anchor="w", padx=12)
        ctk.CTkLabel(self.detail, text="Vaccinations", font=FONT_BOLD).pack(anchor="w", padx=12, pady=(10, 2))
        vac = AnimalRepository.schedule(a.animal_id)
        done_mark, plan_mark = "✓", "○"
        txt = "\n".join(f"{done_mark if v.status == 'DONE' else plan_mark}  {fmt(v.done_date or v.planned_date)}  "
                        f"{v.vaccine_code} - {v.dose_label}" for v in vac[:10]) or "No vaccination plan."
        ctk.CTkLabel(self.detail, text=txt, font=FONT_SMALL, justify="left").pack(anchor="w", padx=12)
        button(self.detail, "Apply to adopt", lambda: self.apply(a), kind="accent", width=200).pack(anchor="w", padx=12,
                                                                                                    pady=16)

    def apply(self, animal):
        if AdoptionRepository.already_applied(self.session.user_id, animal.animal_id):
            error("You have already applied for this animal. See 'My applications'.")
            return
        ApplicationDialog(self, animal)


class ApplicationDialog(Dialog):

    def __init__(self, page, animal):
        super().__init__(page, f"Adoption application – {animal.display_name}", 640, 760)
        self.page, self.animal = page, animal
        ctk.CTkLabel(self, text=f"Application for {animal.display_name} ({animal.species_name}, {animal.age_label})",
                     font=FONT_SUB).pack(anchor="w", padx=20, pady=(16, 0))
        ctk.CTkLabel(self, text="Fields with * are required. The shelter team will review your answers.",
                     font=FONT_SMALL, text_color=MUTED).pack(anchor="w", padx=20)
        box = ctk.CTkScrollableFrame(self, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=12, pady=8)
        f = ctk.CTkFrame(box, fg_color="transparent")
        f.pack(fill="x", padx=8)
        self.address = form_row(f, 0, "Full address", ctk.CTkTextbox(f, width=330, height=60, font=FONT), True)
        self.district = form_row(f, 1, "District", ChoiceBox(f, width=330), True)
        self.district.set_options([(d["district_id"], d["district_name"]) for d in LookupRepository.districts()])
        self.birth_year = form_row(f, 2, "Birth year", entry(f, width=330, placeholder="e.g. 1995"), True)
        self.housing = form_row(f, 3, "Housing", ChoiceBox(f, [("APARTMENT", "Apartment"),
                                                               ("HOUSE_WITH_GARDEN", "House with garden"),
                                                               ("DETACHED_HOUSE", "Detached house")], width=330), True)
        self.ownership = ctk.StringVar(value="OWNER")
        orow = ctk.CTkFrame(f, fg_color="transparent")
        form_row(f, 4, "Home", orow, True)
        for v, t in (("OWNER", "I own it"), ("TENANT", "I rent it")):
            ctk.CTkRadioButton(orow, text=t, variable=self.ownership, value=v, font=FONT,
                               command=self.toggle_tenant).pack(side="left", padx=(0, 12))
        self.landlord = ctk.CTkCheckBox(f, text="My landlord allows pets", font=FONT)
        self.landlord.grid(row=5, column=1, sticky="w", pady=2)
        self.household = form_row(f, 6, "People at home", entry(f, width=330, placeholder="1-20"), True)
        self.children_cb = ctk.CTkCheckBox(f, text="There are children at home", font=FONT)
        self.children_cb.grid(row=7, column=1, sticky="w", pady=4)
        self.other_pets = ctk.CTkCheckBox(f, text="I have other pets", font=FONT, command=self.toggle_pets)
        self.other_pets.grid(row=8, column=1, sticky="w", pady=4)
        self.pets_note = form_row(f, 9, "Which pets", entry(f, width=330, placeholder="e.g. one cat, 3 years old"))
        self.experience = form_row(f, 10, "Experience", ChoiceBox(f, [("NONE", "First time"),
                                                                      ("SOME", "Had pets before"),
                                                                      ("EXPERIENCED", "Very experienced")], width=330),
                                   True)
        self.hours = form_row(f, 11, "Hours alone per day", entry(f, width=330, placeholder="0-24"), True)
        self.reason = form_row(f, 12, "Why do you want to adopt?", ctk.CTkTextbox(f, width=330, height=90, font=FONT),
                               True)
        ctk.CTkLabel(f, text="Agreements *", font=FONT_BOLD).grid(row=13, column=0, sticky="w", pady=(10, 2))
        self.agree_visit = ctk.CTkCheckBox(f, text="I accept home visits after adoption", font=FONT)
        self.agree_neuter = ctk.CTkCheckBox(f, text="I will have the animal neutered", font=FONT)
        self.agree_vacc = ctk.CTkCheckBox(f, text="I will follow the vaccination calendar", font=FONT)
        for i, w in enumerate((self.agree_visit, self.agree_neuter, self.agree_vacc)):
            w.grid(row=13 + i, column=1, sticky="w", pady=3)
        self.status = ctk.CTkLabel(self, text="", font=FONT_SMALL, text_color=DANGER, wraplength=580)
        self.status.pack(padx=20)
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(pady=12)
        button(bar, "Cancel", self.destroy, kind="plain", width=110).pack(side="left", padx=6)
        button(bar, "Send application", self.submit, kind="accent", width=180).pack(side="left", padx=6)
        self.toggle_tenant()
        self.toggle_pets()

    def toggle_tenant(self):
        self.landlord.configure(state="normal" if self.ownership.get() == "TENANT" else "disabled")
        if self.ownership.get() == "OWNER":
            self.landlord.deselect()

    def toggle_pets(self):
        self.pets_note.configure(state="normal" if self.other_pets.get() else "disabled")

    def submit(self):
        address, reason = text_value(self.address), text_value(self.reason)
        tenant = self.ownership.get() == "TENANT"
        err = validators.first_error(
            validators.min_length(address, "Full address", 10),
            None if self.district.value() else "Please choose your district.",
            validators.birth_year(self.birth_year.get()),
            None if self.housing.value() else "Please choose your housing type.",
            None if not tenant or self.landlord.get() else "Tenants need the permission of the landlord.",
            validators.integer(self.household.get(), "People at home", 1, 20),
            None if not self.other_pets.get() or self.pets_note.get().strip() else "Please tell us about your other pets.",
            None if self.experience.value() else "Please choose your experience.",
            validators.integer(self.hours.get(), "Hours alone per day", 0, 24),
            validators.min_length(reason, "Reason", 20),
            None if (self.agree_visit.get() and self.agree_neuter.get() and self.agree_vacc.get())
            else "All three agreements must be accepted.")
        if err:
            self.status.configure(text=err)
            return
        form = {"full_address": address, "district_id": self.district.value(),
                "birth_year": int(self.birth_year.get()), "housing_type": self.housing.value(),
                "ownership": self.ownership.get(), "landlord_permission": bool(self.landlord.get()) if tenant else None,
                "household_size": int(self.household.get()), "has_children": bool(self.children_cb.get()),
                "has_other_pets": bool(self.other_pets.get()),
                "other_pets_note": self.pets_note.get().strip() if self.other_pets.get() else None,
                "pet_experience": self.experience.value(), "hours_alone_per_day": int(self.hours.get()),
                "reason": reason[:500], "agrees_home_visit": True, "agrees_neutering": True,
                "agrees_vaccination": True}
        ok, _ = self.page.run(AdoptionRepository.submit, self.page.session.user_id, self.animal.animal_id, form)
        if ok:
            self.destroy()
            info("Your application was sent to the shelter team. You will get a notification when it is reviewed.",
                 "Application sent")


class MyApplicationsPage(Page):
    title = "My applications"
    subtitle = "Adoption applications you sent. Pending ones can be withdrawn."

    def build(self):
        button(self.toolbar, "Withdraw selected", self.withdraw, kind="danger", width=170).pack(side="left", padx=4)
        self.table = DataTable(self.body, [("applied_at", "Sent", 140),
                                           ("display_name", "Animal", 120), ("species_name", "Species", 70),
                                           ("shelter_name", "Shelter", 260), ("status", "Status", 100),
                                           ("reviewed_at", "Reviewed", 140), ("admin_note", "Note", 280)],
                               height=18, key="application_id")
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        colors = {"APPROVED": ("green",), "REJECTED": ("red",), "WITHDRAWN": ("muted",), "PENDING": ("orange",)}
        self.table.set_rows(AdoptionRepository.my_applications(self.session.user_id),
                            tag_fn=lambda r: colors.get(r["status"], ()), formatters={"status": nice})
        self.main.reload_session()

    def withdraw(self):
        row = self.table.selected()
        if not row:
            error("Select an application first.")
            return
        if confirm("Withdraw this application?"):
            self.run(AdoptionRepository.withdraw, row["application_id"], self.session.user_id)
            self.refresh()


class MyAdoptionsPage(Page):
    title = "My adoptions"
    subtitle = "Your new friends and their vaccination calendar."

    def build(self):
        self.table = DataTable(self.body, [("contract_no", "Contract", 140), ("adopted_at", "Adopted", 140),
                                           ("display_name", "Name", 120), ("species_name", "Species", 70),
                                           ("breed_name", "Breed", 140), ("age_label", "Age", 90),
                                           ("shelter_name", "From shelter", 260)], height=7, key="adoption_id",
                               on_select=self.show)
        self.table.pack(fill="x")
        ctk.CTkLabel(self.body, text="Vaccination calendar", font=FONT_SUB, anchor="w").pack(fill="x", pady=(14, 4))
        self.vacc = DataTable(self.body, [("planned_date", "Planned", 110), ("vaccine_name", "Vaccine", 300),
                                          ("dose_label", "Dose", 120), ("status", "Status", 90),
                                          ("done_date", "Done on", 110)], height=10, key="schedule_id")
        self.vacc.pack(fill="both", expand=True)

    def refresh(self):
        self.table.set_rows(AdoptionRepository.my_adoptions(self.session.user_id))
        self.vacc.set_rows([])

    def show(self, row):
        if row:
            self.vacc.set_rows(AnimalRepository.schedule(row["animal_id"]), formatters={"status": nice},
                               tag_fn=lambda v: ("green",) if v.status == "DONE" else ())
