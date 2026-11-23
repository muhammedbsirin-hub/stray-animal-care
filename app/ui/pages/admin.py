"""Administrator screens."""
import customtkinter as ctk

from app import validators
from app.repositories import (AdoptionRepository, AnimalRepository, ClinicRepository, FeedingRepository,
                              LookupRepository, ReportRepository, ShelterRepository, UserRepository)
from app.ui.map_panel import MapPanel
from app.ui.pages.base import Page
from app.ui.pages.vet import CalendarDialog
from app.ui.pages.volunteer import PostDialog
from app.ui.widgets import (ACCENT, CARD, FONT, FONT_BOLD, FONT_SMALL, FONT_SUB, MUTED, PRIMARY, ChoiceBox,
                            DataTable, Dialog, button, confirm, entry, error, fmt, form_row, info, nice, text_value)


# =============================================================================== overview
class OverviewPage(Page):
    title = "Overview"
    subtitle = "The system at a glance."

    def build(self):
        button(self.toolbar, "Refresh", self.refresh, kind="plain", width=100).pack(side="left")
        self.grid_box = ctk.CTkFrame(self.body, fg_color="transparent")
        self.grid_box.pack(fill="x")
        for c in range(4):
            self.grid_box.grid_columnconfigure(c, weight=1)
        self.tiles = {}
        specs = [("in_shelters", "Animals in shelters"), ("under_treatment", "Under treatment"),
                 ("pending_applications", "Applications waiting"), ("open_cases", "Open injury cases"),
                 ("posts_24h", "Feeding posts (24 h)"), ("adoptions", "Adoptions"),
                 ("volunteers", "Active volunteers")]
        for i, (key, label) in enumerate(specs):
            tile = self.card(self.grid_box)
            tile.grid(row=i // 4, column=i % 4, sticky="nsew", padx=6, pady=6)
            num = ctk.CTkLabel(tile, text="-", font=("Segoe UI", 30, "bold"), text_color=PRIMARY)
            num.pack(anchor="w", padx=16, pady=(14, 0))
            ctk.CTkLabel(tile, text=label, font=FONT, text_color=MUTED).pack(anchor="w", padx=16, pady=(0, 14))
            self.tiles[key] = num
        ctk.CTkLabel(self.body, text="Shelters", font=FONT_SUB, anchor="w").pack(fill="x", pady=(16, 4))
        self.shelters = DataTable(self.body, [("shelter_name", "Shelter", 300), ("district_name", "District", 120),
                                              ("cat_count", "Cats", 60), ("dog_count", "Dogs", 60),
                                              ("animal_count", "Total", 60), ("capacity", "Capacity", 70),
                                              ("occupancy_pct", "Occupancy %", 90),
                                              ("partner_clinic", "Partner clinic", 260)], height=10, key="shelter_id")
        self.shelters.pack(fill="both", expand=True)

    def refresh(self):
        data = ReportRepository.overview()
        for k, lbl in self.tiles.items():
            lbl.configure(text=str(data[k]),
                          text_color=ACCENT if k == "pending_applications" and data[k] else PRIMARY)
        rows = ShelterRepository.summaries()
        self.shelters.set_rows(rows, tag_fn=lambda r: ("red",) if (r.occupancy_pct or 0) >= 90 else ())


# =============================================================================== applications
class ApplicationsPage(Page):
    title = "Adoption applications"
    subtitle = "Every application arrives here like a CV. Open one to approve or reject it."

    def build(self):
        self.filter = ctk.CTkSegmentedButton(self.toolbar, values=["Pending", "Approved", "Rejected", "All"],
                                             command=lambda v: self.refresh(), font=FONT)
        self.filter.set("Pending")
        self.filter.pack(side="left", padx=8)
        button(self.toolbar, "Open application", self.open, width=170).pack(side="left", padx=4)
        self.table = DataTable(self.body, [("application_id", "No", 45), ("applied_at", "Received", 135),
                                           ("applicant_name", "Applicant", 150), ("applicant_age", "Age", 45),
                                           ("district_name", "District", 100), ("animal_name", "Animal", 100),
                                           ("species_name", "Species", 60), ("shelter_name", "Shelter", 250),
                                           ("status", "Status", 90)], height=20, key="application_id",
                               on_double=lambda r: self.open())
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        status = {"Pending": "PENDING", "Approved": "APPROVED", "Rejected": "REJECTED"}.get(self.filter.get())
        self.table.set_rows(AdoptionRepository.dossiers(status), formatters={"status": nice},
                            tag_fn=lambda r: {"APPROVED": ("green",), "REJECTED": ("red",),
                                              "WITHDRAWN": ("muted",)}.get(r["status"], ()))
        self.main.refresh_badge()

    def open(self):
        row = self.table.selected()
        if row is None:
            error("Select an application first.")
            return
        DossierDialog(self, row["application_id"])


def checklist(d):
    """(ok?, text) lines shown in the dossier; hard rules are also checked by the database."""
    items = [(d["applicant_age"] >= 18, f"Age {d['applicant_age']} (18+ required)")]
    if d["ownership"] == "TENANT":
        items.append((bool(d["landlord_permission"]), "Tenant with landlord permission"))
    else:
        items.append((True, "Owns the home"))
    items.append((d["hours_alone_per_day"] <= 8, f"Animal alone {d['hours_alone_per_day']} h/day (8 h or less advised)"))
    items.append((d["pet_experience"] != "NONE", f"Experience: {nice(d['pet_experience'])}"))
    items.append((d["feeding_posts"] + d["injury_reports"] > 0,
                  f"Volunteer activity: {d['feeding_posts']} feeding posts, {d['injury_reports']} injury reports"))
    items.append((True, f"Previous adoptions: {d['previous_adoptions']}"))
    items.append((d["agrees_home_visit"] and d["agrees_neutering"] and d["agrees_vaccination"],
                  "Accepted home visits, neutering and vaccinations"))
    return items


class DossierDialog(Dialog):
    def __init__(self, page, application_id):
        super().__init__(page, f"Application #{application_id}", 760, 760)
        self.page, self.app_id = page, application_id
        d = AdoptionRepository.dossier(application_id)
        self.d = d
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(top, text=d["applicant_name"], font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ctk.CTkLabel(top, text=f"@{d['username']}  ·  {d['email']}  ·  {d['phone']}", font=FONT_SMALL, text_color=MUTED).pack(anchor="w")
        ctk.CTkLabel(top, text=f"Wants to adopt: {d['animal_name']} ({d['species_name']}, {d['age_label']}) from "
                               f"{d['shelter_name']}", font=FONT_BOLD, text_color=PRIMARY, wraplength=700,
                     justify="left").pack(anchor="w", pady=(6, 0))
        box = ctk.CTkScrollableFrame(self, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=12)

        def block(title, lines):
            card = ctk.CTkFrame(box, corner_radius=10, fg_color=CARD)
            card.pack(fill="x", padx=6, pady=5)
            ctk.CTkLabel(card, text=title, font=FONT_BOLD).pack(anchor="w", padx=12, pady=(8, 2))
            for left, right in lines:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=12)
                ctk.CTkLabel(row, text=left, font=FONT_SMALL, text_color=MUTED, width=170, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=right, font=FONT_SMALL, anchor="w", justify="left", wraplength=480).pack(
                    side="left", fill="x")
            ctk.CTkFrame(card, height=6, fg_color="transparent").pack()

        card = ctk.CTkFrame(box, corner_radius=10, fg_color=CARD)
        card.pack(fill="x", padx=6, pady=5)
        ctk.CTkLabel(card, text="Checklist", font=FONT_BOLD).pack(anchor="w", padx=12, pady=(8, 2))
        for ok, text in checklist(d):
            ctk.CTkLabel(card, text=("✓  " if ok else "⚠  ") + text, font=FONT_SMALL,
                         text_color=PRIMARY if ok else ACCENT, anchor="w").pack(anchor="w", padx=14)
        ctk.CTkFrame(card, height=6, fg_color="transparent").pack()
        block("Home and family", [
            ("Address", f"{d['full_address']} ({d['district_name']})"),
            ("Housing", nice(d["housing_type"])), ("Home", nice(d["ownership"])),
            ("People at home", str(d["household_size"])), ("Children", fmt(bool(d["has_children"]))),
            ("Other pets", (d["other_pets_note"] or "Yes") if d["has_other_pets"] else "No")])
        block("About the applicant", [
            ("Age", str(d["applicant_age"])), ("Experience", nice(d["pet_experience"])),
            ("Alone per day", f"{d['hours_alone_per_day']} hours"), ("Reason", d["reason"])])
        competing = AdoptionRepository.competing(application_id)
        if competing and d["status"] == "PENDING":
            ctk.CTkLabel(box, text=f"Note: {competing} other pending application(s) for the same animal will be "
                                   f"rejected automatically if you approve this one.", font=FONT_SMALL,
                         text_color=ACCENT, wraplength=680, justify="left").pack(anchor="w", padx=10, pady=6)
        if d["status"] == "PENDING":
            ctk.CTkLabel(self, text="Note to the applicant (required when rejecting):", font=FONT_SMALL).pack(
                anchor="w", padx=20, pady=(6, 0))
            self.note = entry(self, width=700)
            self.note.pack(padx=20)
            bar = ctk.CTkFrame(self, fg_color="transparent")
            bar.pack(pady=12)
            button(bar, "Close", self.destroy, kind="plain", width=110).pack(side="left", padx=6)
            button(bar, "Reject", self.reject, kind="danger", width=130).pack(side="left", padx=6)
            button(bar, "Approve adoption", self.approve, width=180).pack(side="left", padx=6)
        else:
            ctk.CTkLabel(self, text=f"Status: {nice(d['status'])}  ·  reviewed {fmt(d['reviewed_at'])}  "
                                    f"·  {d['admin_note'] or ''}", font=FONT_BOLD).pack(pady=12)

    def approve(self):
        if confirm(f"Approve the adoption of {self.d['animal_name']} by {self.d['applicant_name']}?"):
            ok, _ = self.page.run(AdoptionRepository.approve, self.app_id, self.page.session.user_id,
                                  self.note.get().strip())
            if ok:
                self.destroy()
                info("Approved. The animal is marked as adopted and the applicant was notified.")
                self.page.refresh()

    def reject(self):
        note = self.note.get().strip()
        if not note:
            error("Please write a short reason for the applicant.")
            return
        ok, _ = self.page.run(AdoptionRepository.reject, self.app_id, self.page.session.user_id, note[:255])
        if ok:
            self.destroy()
            info("The application was rejected and the applicant was notified.")
            self.page.refresh()


# =============================================================================== map
class AdminMapPage(Page):
    title = "Feeding map"
    subtitle = "Where volunteers left food. Blue = shelters, purple = clinics."

    def build(self):
        self.range = ctk.CTkSegmentedButton(self.toolbar, values=["Last 24 hours", "Last 7 days"],
                                            command=lambda v: self.refresh(), font=FONT)
        self.range.set("Last 24 hours")
        self.range.pack(side="left", padx=8)
        self.show_places = ctk.CTkCheckBox(self.toolbar, text="Shelters and clinics", font=FONT,
                                           command=self.refresh)
        self.show_places.select()
        self.show_places.pack(side="left", padx=8)
        self.count = ctk.CTkLabel(self.body, text="", font=FONT, text_color=MUTED, anchor="w")
        self.count.pack(fill="x")
        self.map = MapPanel(self.body)
        self.map.pack(fill="both", expand=True, pady=(4, 0))

    def refresh(self):
        self.map.clear()
        posts = FeedingRepository.active_posts() if self.range.get() == "Last 24 hours" \
            else FeedingRepository.recent_posts(7)
        for p in posts:
            self.map.add_marker(p.latitude, p.longitude, text=p.username, color=PRIMARY, data=p.post_id,
                                command=lambda m: PostDialog(self, m.data))
        if self.show_places.get():
            for s in ShelterRepository.summaries():
                self.map.add_marker(s.latitude, s.longitude, text=s.shelter_name.replace(" Municipality Animal", ""),
                                    color="#2563eb")
            for c in LookupRepository.clinics():
                self.map.add_marker(c["latitude"], c["longitude"], text=c["clinic_name"], color="#7c3aed")
        self.count.configure(text=f"{len(posts)} feeding posts")


# =============================================================================== daily vet report
class VetReportPage(Page):
    title = "Daily vet report"
    subtitle = "Arrivals and discharges per veterinarian, and which vet is caring for which animal."

    def build(self):
        self.range = ctk.CTkSegmentedButton(self.toolbar, values=["Today", "Yesterday", "Last 7 days"],
                                            command=lambda v: self.refresh(), font=FONT)
        self.range.set("Today")
        self.range.pack(side="left", padx=8)
        ctk.CTkLabel(self.body, text="Per veterinarian", font=FONT_SUB, anchor="w").pack(fill="x")
        self.stats = DataTable(self.body, [("vet_name", "Veterinarian", 200), ("clinic_name", "Clinic", 270),
                                           ("shift", "Shift", 80), ("arrived", "Arrived", 70),
                                           ("not_arrived", "Did not arrive", 100), ("discharged", "Discharged", 90)],
                               height=6, key="vet_id")
        self.stats.pack(fill="both", expand=True)
        ctk.CTkLabel(self.body, text="Animals under treatment now", font=FONT_SUB, anchor="w").pack(fill="x",
                                                                                                    pady=(12, 0))
        self.active = DataTable(self.body, [("display_name", "Animal", 110), ("species_name", "Species", 70),
                                            ("diagnosis", "Diagnosis", 240), ("condition_level", "Condition", 90),
                                            ("vet_name", "Veterinarian", 180), ("clinic_name", "Clinic", 250),
                                            ("started_at", "Since", 130)], height=6, key="treatment_id")
        self.active.pack(fill="both", expand=True)
        ctk.CTkLabel(self.body, text="Case log (arrived / not arrived)", font=FONT_SUB, anchor="w").pack(fill="x",
                                                                                                         pady=(12, 0))
        self.log = DataTable(self.body, [("changed_at", "Time", 135), ("report_id", "Case", 55),
                                         ("old_status", "From", 100), ("new_status", "To", 110),
                                         ("changed_by", "By", 120), ("clinic_name", "Clinic", 260)], height=6,
                             key="changed_at")
        self.log.pack(fill="both", expand=True)

    def refresh(self):
        days = {"Today": 0, "Yesterday": 1, "Last 7 days": 7}[self.range.get()]
        self.stats.set_rows(ReportRepository.vet_daily_stats(days), formatters={"shift": nice})
        self.active.set_rows(ReportRepository.active_treatments(), formatters={"condition_level": nice})
        rows = ReportRepository.case_log(days)
        for i, r in enumerate(rows):
            r["key"] = i
        self.log.key = "key"
        self.log.set_rows(rows, formatters={"old_status": nice, "new_status": nice})


# =============================================================================== shelters
class SheltersPage(Page):
    title = "Shelters"
    subtitle = "Animal counts are calculated from the animal table (never typed in)."

    def build(self):
        button(self.toolbar, "Delete", self.delete, kind="danger", width=100).pack(side="left", padx=4)
        button(self.toolbar, "Edit", self.edit, kind="plain", width=100).pack(side="left", padx=4)
        button(self.toolbar, "+ New shelter", lambda: ShelterDialog(self, None), width=150).pack(side="left", padx=4)
        self.table = DataTable(self.body, [("shelter_id", "No", 40), ("shelter_name", "Shelter", 280),
                                           ("district_name", "District", 110), ("phone", "Phone", 110),
                                           ("accepted_species", "Accepts", 90), ("animal_count", "Animals", 70),
                                           ("capacity", "Capacity", 70), ("partner_clinic", "Partner clinic", 260)],
                               height=20, key="shelter_id", on_double=lambda r: self.edit())
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.table.set_rows(ShelterRepository.summaries())

    def edit(self):
        s = self.table.selected()
        if s is None:
            error("Select a shelter first.")
            return
        ShelterDialog(self, s.shelter_id)

    def delete(self):
        s = self.table.selected()
        if s is None:
            error("Select a shelter first.")
            return
        if confirm(f"Delete {s.shelter_name}?"):
            ok, _ = self.run(ShelterRepository.delete, s.shelter_id)
            if ok:
                self.refresh()


class LocationPicker(ctk.CTkFrame):
    """Small map: the admin clicks the place instead of typing coordinates."""

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.coords = None
        self.label = ctk.CTkLabel(self, text="Click on the map to choose the location *", font=FONT_SMALL,
                                  text_color=MUTED, anchor="w")
        self.label.pack(fill="x")
        self.map = MapPanel(self, zoom=11, width=420, height=420)
        self.map.pack(fill="both", expand=True, pady=(4, 0))
        self.map.pick_location(self._picked)

    def _picked(self, coords):
        self.coords = (round(coords[0], 6), round(coords[1], 6))
        self.label.configure(text=f"Selected: {self.coords[0]:.5f}, {self.coords[1]:.5f}", text_color=PRIMARY)
        self.map.pick_location(self._picked)

    def set(self, lat, lon):
        self.coords = (float(lat), float(lon))
        self.map.show_pick(*self.coords)
        self.map.map.set_position(*self.coords)
        self.map.map.set_zoom(13)
        self.label.configure(text=f"Selected: {self.coords[0]:.5f}, {self.coords[1]:.5f}", text_color=PRIMARY)

    def error(self):
        return None if self.coords else "Click on the map to choose the location."


class ShelterDialog(Dialog):
    def __init__(self, page, shelter_id):
        super().__init__(page, "Shelter", 1000, 560)
        self.page, self.shelter_id = page, shelter_id
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(padx=20, pady=16, fill="both", expand=True)
        f = ctk.CTkFrame(top, fg_color="transparent")
        f.pack(side="left", anchor="n")
        self.location = LocationPicker(top)
        self.location.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.name = form_row(f, 0, "Name", entry(f, width=300), True)
        self.district = form_row(f, 1, "District", ChoiceBox(f, width=300), True)
        self.district.set_options([(d["district_id"], d["district_name"]) for d in LookupRepository.districts()])
        self.address = form_row(f, 2, "Address", entry(f, width=300), True)
        self.phone = form_row(f, 3, "Phone", entry(f, width=300, placeholder="0212XXXXXXX"), True)
        self.capacity = form_row(f, 4, "Capacity", entry(f, width=300), True)
        self.clinic = form_row(f, 5, "Partner clinic", ChoiceBox(f, width=300), True)
        self.clinic.set_options([(c["clinic_id"], c["clinic_name"]) for c in LookupRepository.clinics()])
        sp = ctk.CTkFrame(f, fg_color="transparent")
        form_row(f, 6, "Accepts", sp, True)
        self.species_boxes = {}
        for s in LookupRepository.species():
            cb = ctk.CTkCheckBox(sp, text=s["species_name"], font=FONT)
            cb.pack(side="left", padx=(0, 12))
            self.species_boxes[s["species_id"]] = cb
        if shelter_id:
            s = ShelterRepository.get(shelter_id)
            for w, v in ((self.name, s["shelter_name"]), (self.address, s["address"]), (self.phone, s["phone"]),
                         (self.capacity, s["capacity"])):
                w.insert(0, str(v))
            self.location.set(s["latitude"], s["longitude"])
            self.district.set_value(s["district_id"])
            self.clinic.set_value(s["partner_clinic_id"])
            for sid in s["species_ids"]:
                self.species_boxes[sid].select()
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(pady=12)
        button(bar, "Cancel", self.destroy, kind="plain", width=110).pack(side="left", padx=6)
        button(bar, "Save", self.save, width=130).pack(side="left", padx=6)

    def save(self):
        species = [sid for sid, cb in self.species_boxes.items() if cb.get()]
        err = validators.first_error(
            validators.min_length(self.name.get(), "Name", 3),
            None if self.district.value() else "Choose a district.",
            validators.min_length(self.address.get(), "Address", 5),
            validators.landline(self.phone.get()),
            validators.integer(self.capacity.get(), "Capacity", 1, 2000),
            self.location.error(),
            None if self.clinic.value() else "Choose a partner clinic.",
            None if species else "Choose at least one species.")
        if err:
            error(err)
            return
        data = {"shelter_name": self.name.get().strip(), "district_id": self.district.value(),
                "address": self.address.get().strip(), "phone": self.phone.get().strip(),
                "capacity": int(self.capacity.get()), "latitude": self.location.coords[0],
                "longitude": self.location.coords[1], "partner_clinic_id": self.clinic.value(), "species_ids": species}
        ok, _ = self.page.run(ShelterRepository.save, data, self.shelter_id)
        if ok:
            self.destroy()
            self.page.refresh()


# =============================================================================== clinics
class ClinicsPage(Page):
    title = "Clinics"
    subtitle = "Clinics where volunteers bring injured animals."

    def build(self):
        button(self.toolbar, "Delete", self.delete, kind="danger", width=100).pack(side="left", padx=4)
        button(self.toolbar, "Edit", self.edit, kind="plain", width=100).pack(side="left", padx=4)
        button(self.toolbar, "+ New clinic", lambda: ClinicDialog(self, None), width=150).pack(side="left", padx=4)
        self.table = DataTable(self.body, [("clinic_id", "No", 40), ("clinic_name", "Clinic", 280),
                                           ("district_name", "District", 110), ("address", "Address", 330),
                                           ("phone", "Phone", 110), ("vets", "Vets", 50)], height=20, key="clinic_id",
                               on_double=lambda r: self.edit())
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.table.set_rows(LookupRepository.clinics())

    def edit(self):
        c = self.table.selected()
        if c is None:
            error("Select a clinic first.")
            return
        ClinicDialog(self, c["clinic_id"])

    def delete(self):
        c = self.table.selected()
        if c is None:
            error("Select a clinic first.")
            return
        if confirm(f"Delete {c['clinic_name']}?"):
            ok, _ = self.run(ClinicRepository.delete, c["clinic_id"])
            if ok:
                self.refresh()


class ClinicDialog(Dialog):
    def __init__(self, page, clinic_id):
        super().__init__(page, "Clinic", 1000, 520)
        self.page, self.clinic_id = page, clinic_id
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(padx=20, pady=16, fill="both", expand=True)
        f = ctk.CTkFrame(top, fg_color="transparent")
        f.pack(side="left", anchor="n")
        self.location = LocationPicker(top)
        self.location.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.name = form_row(f, 0, "Name", entry(f, width=300), True)
        self.district = form_row(f, 1, "District", ChoiceBox(f, width=300), True)
        self.district.set_options([(d["district_id"], d["district_name"]) for d in LookupRepository.districts()])
        self.address = form_row(f, 2, "Address", entry(f, width=300), True)
        self.phone = form_row(f, 3, "Phone", entry(f, width=300, placeholder="0216XXXXXXX"), True)
        if clinic_id:
            c = ClinicRepository.get(clinic_id)
            for w, v in ((self.name, c["clinic_name"]), (self.address, c["address"]), (self.phone, c["phone"])):
                w.insert(0, str(v))
            self.location.set(c["latitude"], c["longitude"])
            self.district.set_value(c["district_id"])
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(pady=12)
        button(bar, "Cancel", self.destroy, kind="plain", width=110).pack(side="left", padx=6)
        button(bar, "Save", self.save, width=130).pack(side="left", padx=6)

    def save(self):
        err = validators.first_error(validators.min_length(self.name.get(), "Name", 3),
                                     None if self.district.value() else "Choose a district.",
                                     validators.min_length(self.address.get(), "Address", 5),
                                     validators.landline(self.phone.get()),
                                     self.location.error())
        if err:
            error(err)
            return
        data = {"clinic_name": self.name.get().strip(), "district_id": self.district.value(),
                "address": self.address.get().strip(), "phone": self.phone.get().strip(),
                "latitude": self.location.coords[0], "longitude": self.location.coords[1]}
        ok, _ = self.page.run(ClinicRepository.save, data, self.clinic_id)
        if ok:
            self.destroy()
            self.page.refresh()


# =============================================================================== veterinarians
class VetsPage(Page):
    title = "Veterinarians"
    subtitle = "Every clinic must keep at least one morning (07:00-16:59) and one evening (17:00-06:59) vet."

    def build(self):
        button(self.toolbar, "Close account", self.deactivate, kind="danger", width=140).pack(side="left", padx=4)
        button(self.toolbar, "Change clinic / shift", self.change, kind="plain", width=180).pack(side="left", padx=4)
        button(self.toolbar, "+ New veterinarian", lambda: VetDialog(self), width=180).pack(side="left", padx=4)
        self.table = DataTable(self.body, [("vet_name", "Veterinarian", 190), ("username", "Username", 80),
                                           ("clinic_name", "Clinic", 270), ("shift", "Shift", 80),
                                           ("license_no", "License", 100), ("phone", "Phone", 110),
                                           ("animals", "Animals", 65), ("is_active", "Active", 60)],
                               height=20, key="vet_id")
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.table.set_rows(UserRepository.list_vets(), formatters={"shift": nice},
                            tag_fn=lambda r: ("muted",) if not r["is_active"] else ())

    def change(self):
        v = self.table.selected()
        if v is None:
            error("Select a veterinarian first.")
            return
        dlg = Dialog(self, "Change clinic / shift", 480, 260)
        f = ctk.CTkFrame(dlg, fg_color="transparent")
        f.pack(padx=20, pady=16)
        clinic = form_row(f, 0, "Clinic", ChoiceBox(f, width=300), True)
        clinic.set_options([(c["clinic_id"], c["clinic_name"]) for c in LookupRepository.clinics()])
        clinic.set_value(v["clinic_id"])
        shift = form_row(f, 1, "Shift", ChoiceBox(f, [("MORNING", "Morning"), ("EVENING", "Evening")], width=300), True)
        shift.set_value(v["shift"])

        def save():
            ok, _ = self.run(UserRepository.update_vet, v["vet_id"], clinic.value(), shift.value())
            if ok:
                dlg.destroy()
                self.refresh()

        button(dlg, "Save", save, width=130).pack(pady=8)

    def deactivate(self):
        v = self.table.selected()
        if v is None:
            error("Select a veterinarian first.")
            return
        if confirm(f"Close the account of {v['vet_name']}? Animals will be moved to a colleague of the same clinic."):
            ok, _ = self.run(UserRepository.delete_account, v["user_id"], self.session.user_id)
            if ok:
                self.refresh()


class VetDialog(Dialog):
    def __init__(self, page):
        super().__init__(page, "New veterinarian", 560, 620)
        self.page = page
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(padx=20, pady=16, fill="x")
        self.first = form_row(f, 0, "First name", entry(f, width=300), True)
        self.last = form_row(f, 1, "Last name", entry(f, width=300), True)
        self.username = form_row(f, 2, "Username", entry(f, width=300), True)
        self.email = form_row(f, 3, "E-mail", entry(f, width=300), True)
        self.phone = form_row(f, 4, "Phone", entry(f, width=300, placeholder="05XXXXXXXXX"), True)
        self.password = form_row(f, 5, "First password", entry(f, width=300, show="•"), True)
        self.clinic = form_row(f, 6, "Clinic", ChoiceBox(f, width=300), True)
        self.clinic.set_options([(c["clinic_id"], c["clinic_name"]) for c in LookupRepository.clinics()])
        self.shift = form_row(f, 7, "Shift", ChoiceBox(f, [("MORNING", "Morning"), ("EVENING", "Evening")], width=300),
                              True)
        self.license = form_row(f, 8, "License no", entry(f, width=300, placeholder="TVHB-12345"), True)
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(pady=12)
        button(bar, "Cancel", self.destroy, kind="plain", width=110).pack(side="left", padx=6)
        button(bar, "Create", self.save, width=130).pack(side="left", padx=6)

    def save(self):
        d = {"first_name": self.first.get().strip(), "last_name": self.last.get().strip(),
             "username": self.username.get().strip(), "email": self.email.get().strip(),
             "phone": self.phone.get().strip(), "password": self.password.get(), "clinic_id": self.clinic.value(),
             "shift": self.shift.value(), "license_no": self.license.get().strip()}
        err = validators.first_error(validators.person_name(d["first_name"], "First name"),
                                     validators.person_name(d["last_name"], "Last name"),
                                     validators.username(d["username"]), validators.email(d["email"]),
                                     validators.phone(d["phone"]), validators.password(d["password"]),
                                     None if d["clinic_id"] else "Choose a clinic.",
                                     None if d["shift"] else "Choose a shift.",
                                     validators.license_no(d["license_no"]))
        if not err and UserRepository.username_taken(d["username"]):
            err = "This username is already taken."
        if not err and UserRepository.email_taken(d["email"]):
            err = "This e-mail address is already registered."
        if err:
            error(err)
            return
        ok, _ = self.page.run(UserRepository.create_vet, d)
        if ok:
            self.destroy()
            info("The veterinarian account was created.")
            self.page.refresh()


# =============================================================================== animals
class AnimalsPage(Page):
    title = "Animals"
    subtitle = "All animals in the system. New shelter animals get a vaccination calendar automatically."

    def build(self):
        self.status = ChoiceBox(self.toolbar, [(None, "All statuses"), ("IN_SHELTER", "In shelter"),
                                               ("UNDER_TREATMENT", "Under treatment"), ("ADOPTED", "Adopted"),
                                               ("RELEASED", "Released"), ("DECEASED", "Deceased")],
                                width=170, command=lambda v: self.refresh())
        self.status.set_value(None)
        self.status.pack(side="left", padx=4)
        self.search = entry(self.toolbar, width=160, placeholder="Search name / shelter")
        self.search.pack(side="left", padx=4)
        self.search.bind("<Return>", lambda e: self.refresh())
        button(self.toolbar, "Calendar", self.calendar, kind="plain", width=100).pack(side="left", padx=4)
        button(self.toolbar, "Edit", self.edit, kind="plain", width=80).pack(side="left", padx=4)
        button(self.toolbar, "+ Add to shelter", lambda: AnimalDialog(self), width=160).pack(side="left", padx=4)
        self.table = DataTable(self.body, [("animal_id", "No", 45), ("display_name", "Name", 110),
                                           ("species_name", "Species", 65), ("breed_name", "Breed", 130),
                                           ("sex", "Sex", 75), ("age_label", "Age", 85), ("status", "Status", 120),
                                           ("shelter_name", "Shelter", 300)],
                               height=20, key="animal_id", on_double=lambda r: self.calendar())
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.table.set_rows(AnimalRepository.search(self.status.value(), self.search.get().strip()),
                            formatters={"sex": nice, "status": nice})

    def calendar(self):
        a = self.table.selected()
        if a is None:
            error("Select an animal first.")
            return
        CalendarDialog(self, a.animal_id, read_only=True)

    def edit(self):
        a = self.table.selected()
        if a is None:
            error("Select an animal first.")
            return
        dlg = Dialog(self, f"Edit {a.display_name}", 520, 380)
        f = ctk.CTkFrame(dlg, fg_color="transparent")
        f.pack(padx=20, pady=16, fill="x")
        name = form_row(f, 0, "Name", entry(f, width=300))
        name.insert(0, a.display_name if not a.display_name.startswith("#") else "")
        color = form_row(f, 1, "Color", entry(f, width=300))
        color.insert(0, a.color or "")
        neutered = ctk.CTkCheckBox(f, text="Neutered", font=FONT)
        neutered.grid(row=2, column=1, sticky="w", pady=4)
        if a.is_neutered:
            neutered.select()
        desc = form_row(f, 3, "Description", ctk.CTkTextbox(f, width=300, height=80, font=FONT))
        desc.insert("1.0", a.description or "")

        def save():
            ok, _ = self.run(AnimalRepository.update_basic, a.animal_id, name.get().strip()[:40],
                             color.get().strip()[:40], bool(neutered.get()), text_value(desc)[:255])
            if ok:
                dlg.destroy()
                self.refresh()

        button(dlg, "Save", save, width=130).pack(pady=8)


class AnimalDialog(Dialog):
    def __init__(self, page):
        super().__init__(page, "Add an animal to a shelter", 560, 600)
        self.page = page
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(padx=20, pady=16, fill="x")
        self.species = form_row(f, 0, "Species", ChoiceBox(f, width=300, command=self.species_changed), True)
        self.species.set_options([(s["species_id"], s["species_name"]) for s in LookupRepository.species()])
        self.breed = form_row(f, 1, "Breed", ChoiceBox(f, width=300, placeholder="Unknown"))
        self.shelter = form_row(f, 2, "Shelter", ChoiceBox(f, width=300, placeholder="Choose species first"), True)
        self.name = form_row(f, 3, "Name", entry(f, width=300, placeholder="optional"))
        self.sex = form_row(f, 4, "Sex", ChoiceBox(f, [("MALE", "Male"), ("FEMALE", "Female"),
                                                       ("UNKNOWN", "Unknown")], width=300), True)
        self.sex.set_value("UNKNOWN")
        self.color = form_row(f, 5, "Color", entry(f, width=300))
        self.age = form_row(f, 6, "Age (weeks)", entry(f, width=300, placeholder="e.g. 10 or 104"), True)
        self.neutered = ctk.CTkCheckBox(f, text="Neutered", font=FONT)
        self.neutered.grid(row=7, column=1, sticky="w", pady=4)
        self.desc = form_row(f, 8, "Description", ctk.CTkTextbox(f, width=300, height=70, font=FONT))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(pady=12)
        button(bar, "Cancel", self.destroy, kind="plain", width=110).pack(side="left", padx=6)
        button(bar, "Add", self.save, width=130).pack(side="left", padx=6)

    def species_changed(self, species_id):
        self.breed.set_options([(None, "Unknown")] + [(b["breed_id"], b["breed_name"])
                                                      for b in LookupRepository.breeds(species_id)])
        self.shelter.set_options([(s["shelter_id"], f"{s['shelter_name']} ({s['animal_count']}/{s['capacity']})")
                                  for s in ShelterRepository.accepting(species_id)])

    def save(self):
        err = validators.first_error(None if self.species.value() else "Choose the species.",
                                     None if self.shelter.value() else "Choose a shelter.",
                                     validators.integer(self.age.get(), "Age (weeks)", 0, 1500))
        if err:
            error(err)
            return
        data = {"species_id": self.species.value(), "breed_id": self.breed.value(), "shelter_id": self.shelter.value(),
                "name": self.name.get().strip()[:40], "sex": self.sex.value() or "UNKNOWN",
                "color": self.color.get().strip()[:40], "age_weeks": int(self.age.get()),
                "is_neutered": bool(self.neutered.get()), "description": text_value(self.desc)[:255]}
        ok, _ = self.page.run(AnimalRepository.add_to_shelter, data)
        if ok:
            self.destroy()
            info("The animal was added and its vaccination calendar was created.")
            self.page.refresh()


# =============================================================================== users
class UsersPage(Page):
    title = "Users"
    subtitle = "Close accounts. A closed account keeps its data (soft delete) and cannot be reopened."

    def build(self):
        self.search = entry(self.toolbar, width=180, placeholder="Search")
        self.search.pack(side="left", padx=4)
        self.search.bind("<Return>", lambda e: self.refresh())
        button(self.toolbar, "Close account", self.close_account, kind="danger", width=140).pack(side="left", padx=4)
        self.table = DataTable(self.body, [("user_id", "No", 45), ("username", "Username", 120),
                                           ("full_name", "Name", 170), ("email", "E-mail", 230),
                                           ("phone", "Phone", 110), ("roles", "Roles", 170),
                                           ("is_active", "Active", 60)],
                               height=20, key="user_id")
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.table.set_rows(UserRepository.list_users(self.search.get().strip()),
                            tag_fn=lambda r: ("muted",) if not r["is_active"] else ())

    def close_account(self):
        u = self.table.selected()
        if u is None:
            error("Select a user first.")
            return
        if u["user_id"] == self.session.user_id:
            error("Use Settings to delete your own account.")
            return
        if confirm(f"Close the account of {u['username']}?"):
            ok, _ = self.run(UserRepository.delete_account, u["user_id"], self.session.user_id)
            if ok:
                self.refresh()
