"""Veterinarian screens: incoming cases, treatments, vaccination follow-up."""
import customtkinter as ctk

from app import validators
from app.repositories import AnimalRepository, CaseRepository, LookupRepository, ShelterRepository
from app.ui.pages.base import Page
from app.ui.widgets import (DANGER, FONT, FONT_BOLD, FONT_SMALL, FONT_SUB, MUTED, PRIMARY, ChoiceBox, DataTable,
                            Dialog, button, confirm, entry, error, fmt, form_row, info, nice, photo_image, text_value)


def _vet_banner(page):
    v = page.session.vet
    box = page.card()
    box.pack(fill="x", pady=(0, 10))
    ctk.CTkLabel(box, text=f"{v.clinic_name}   ·   {v.shift_text}", font=FONT_BOLD, text_color=PRIMARY).pack(
        anchor="w", padx=16, pady=10)


class CasesPage(Page):
    title = "Incoming cases"
    subtitle = ("Injured animals that volunteers are bringing to you. Mark each case as arrived or not arrived. "
                "Cases still open at the end of the day are closed automatically.")

    def build(self):
        button(self.toolbar, "Refresh", self.refresh, kind="plain", width=100).pack(side="left", padx=4)
        button(self.toolbar, "Did not arrive", self.not_arrived, kind="danger", width=140).pack(side="left", padx=4)
        button(self.toolbar, "Animal arrived", self.arrived, width=150).pack(side="left", padx=4)
        _vet_banner(self)
        self.table = DataTable(self.body, [("report_id", "Case", 55), ("reported_at", "Reported", 135),
                                           ("species_name", "Species", 65), ("condition_desc", "Condition", 330),
                                           ("approx_age_weeks", "Age (w)", 60), ("district_name", "Found in", 170),
                                           ("reporter_name", "Volunteer", 130), ("reporter_phone", "Phone", 105)],
                               height=9, key="report_id", on_double=lambda r: self.arrived())
        self.table.pack(fill="both", expand=True)
        ctk.CTkLabel(self.body, text="Closed today", font=FONT_SUB, anchor="w").pack(fill="x", pady=(14, 4))
        self.closed = DataTable(self.body, [("report_id", "Case", 55), ("reported_at", "Reported", 135),
                                            ("species_name", "Species", 65), ("condition_desc", "Condition", 400),
                                            ("status", "Result", 110), ("result", "Treatment", 170)],
                                height=6, key="report_id")
        self.closed.pack(fill="both", expand=True)

    def refresh(self):
        vet_id = self.session.vet.vet_id
        self.table.set_rows(CaseRepository.pending_for_vet(vet_id))
        self.closed.set_rows(CaseRepository.closed_today_for_vet(vet_id), formatters={"status": nice, "result": nice},
                             tag_fn=lambda r: ("muted",) if r.status == "NOT_ARRIVED" else ("green",))
        self.main.refresh_badge()

    def _selected(self):
        case = self.table.selected()
        if case is None:
            error("Select a case first.")
        return case

    def not_arrived(self):
        case = self._selected()
        if case and confirm(f"Case #{case.report_id}: mark as NOT arrived? The volunteer will be notified."):
            self.run(CaseRepository.mark_not_arrived, case.report_id, self.session.user_id)
            self.refresh()

    def arrived(self):
        case = self._selected()
        if case:
            ArrivalDialog(self, case)


class ArrivalDialog(Dialog):
    """Animal arrived: register the animal, the examination and the prescription in one transaction."""

    def __init__(self, page, case):
        super().__init__(page, f"Case #{case.report_id} – animal arrived", 760, 780)
        self.page, self.case = page, case
        self.items = []
        ctk.CTkLabel(self, text=f"Case #{case.report_id}: {case.species_name}", font=FONT_SUB).pack(anchor="w", padx=20,
                                                                                                   pady=(14, 0))
        ctk.CTkLabel(self, text=f"Reported condition: {case.condition_desc}", font=FONT_SMALL, text_color=MUTED,
                     wraplength=700, justify="left").pack(anchor="w", padx=20)
        box = ctk.CTkScrollableFrame(self, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=12, pady=6)

        ctk.CTkLabel(box, text="Animal", font=FONT_BOLD).pack(anchor="w", padx=8, pady=(4, 0))
        a = ctk.CTkFrame(box, fg_color="transparent")
        a.pack(fill="x", padx=8)
        self.name = form_row(a, 0, "Name", entry(a, placeholder="optional"))
        self.breed = form_row(a, 1, "Breed", ChoiceBox(a, placeholder="Unknown"))
        self.breed.set_options([(None, "Unknown")] + [(b["breed_id"], b["breed_name"])
                                                      for b in LookupRepository.breeds(case.species_id)])
        self.sex = form_row(a, 2, "Sex", ChoiceBox(a, [("MALE", "Male"), ("FEMALE", "Female"), ("UNKNOWN", "Unknown")]),
                            True)
        self.sex.set_value("UNKNOWN")
        self.color = form_row(a, 3, "Color", entry(a))
        if case.color:
            self.color.insert(0, case.color)
        self.age = form_row(a, 4, "Age (weeks)", entry(a, placeholder="estimated"), True)
        if case.approx_age_weeks is not None:
            self.age.insert(0, str(case.approx_age_weeks))
        self.neutered = ctk.CTkCheckBox(a, text="Neutered", font=FONT)
        self.neutered.grid(row=5, column=1, sticky="w", pady=4)

        ctk.CTkLabel(box, text="Examination", font=FONT_BOLD).pack(anchor="w", padx=8, pady=(12, 0))
        t = ctk.CTkFrame(box, fg_color="transparent")
        t.pack(fill="x", padx=8)
        self.diagnosis = form_row(t, 0, "Diagnosis", entry(t, width=420), True)
        self.level = form_row(t, 1, "Condition", ChoiceBox(t, [("MILD", "Mild"), ("MODERATE", "Moderate"),
                                                               ("SEVERE", "Severe"), ("CRITICAL", "Critical")]), True)
        self.notes = form_row(t, 2, "Notes", ctk.CTkTextbox(t, width=420, height=70, font=FONT))

        ctk.CTkLabel(box, text="Prescription", font=FONT_BOLD).pack(anchor="w", padx=8, pady=(12, 0))
        p = ctk.CTkFrame(box, fg_color="transparent")
        p.pack(fill="x", padx=8)
        self.medicine = ChoiceBox(p, width=240, placeholder="Medicine")
        self.medicines = LookupRepository.medicines()
        self.medicine.set_options([(m["medicine_id"], f"{m['medicine_name']} ({m['form'].lower()})")
                                   for m in self.medicines])
        self.medicine.grid(row=0, column=0, padx=(0, 6))
        self.dosage = entry(p, width=190, placeholder="Dosage, e.g. 50 mg twice a day")
        self.dosage.grid(row=0, column=1, padx=6)
        self.days = entry(p, width=70, placeholder="Days")
        self.days.grid(row=0, column=2, padx=6)
        button(p, "Add", self.add_item, kind="plain", width=70).grid(row=0, column=3, padx=6)
        self.presc = DataTable(box, [("medicine", "Medicine", 260), ("dosage", "Dosage", 260),
                                     ("duration_days", "Days", 60)], height=4, key="medicine_id")
        self.presc.pack(fill="x", padx=8, pady=6)
        button(box, "Remove selected medicine", self.remove_item, kind="plain", width=200).pack(anchor="w", padx=8)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(pady=12)
        button(bar, "Cancel", self.destroy, kind="plain", width=110).pack(side="left", padx=6)
        button(bar, "Save and start treatment", self.save, width=230).pack(side="left", padx=6)

    def add_item(self):
        mid = self.medicine.value()
        err = validators.first_error(None if mid else "Choose a medicine.",
                                     validators.required(self.dosage.get(), "Dosage"),
                                     validators.integer(self.days.get(), "Days", 1, 90))
        if not err and any(i["medicine_id"] == mid for i in self.items):
            err = "This medicine is already in the prescription."
        if err:
            error(err)
            return
        self.items.append({"medicine_id": mid, "medicine": self.medicine.get(), "dosage": self.dosage.get().strip()[:60],
                           "duration_days": int(self.days.get())})
        self.presc.set_rows(self.items)
        self.dosage.delete(0, "end")
        self.days.delete(0, "end")

    def remove_item(self):
        row = self.presc.selected()
        if row:
            self.items.remove(row)
            self.presc.set_rows(self.items)

    def save(self):
        err = validators.first_error(validators.integer(self.age.get(), "Age (weeks)", 0, 1500),
                                     validators.required(self.diagnosis.get(), "Diagnosis"),
                                     None if self.level.value() else "Choose the condition level.")
        if err:
            error(err)
            return
        animal = {"name": self.name.get().strip(), "breed_id": self.breed.value(), "sex": self.sex.value() or "UNKNOWN",
                  "color": self.color.get().strip(), "age_weeks": int(self.age.get()),
                  "is_neutered": bool(self.neutered.get())}
        treatment = {"diagnosis": self.diagnosis.get().strip()[:255], "condition_level": self.level.value(),
                     "notes": text_value(self.notes)[:500]}
        ok, _ = self.page.run(CaseRepository.mark_arrived, self.case.report_id, self.page.session.vet, animal,
                              treatment, self.items)
        if ok:
            self.destroy()
            info("The animal is registered and the treatment started. The volunteer was notified.")
            self.page.refresh()


class TreatmentsPage(Page):
    title = "Under treatment"
    subtitle = "Animals you are treating. Finish the treatment to discharge them to a shelter, release them, " \
               "or record that they died."

    def build(self):
        button(self.toolbar, "Finish treatment", self.finish, width=170).pack(side="left", padx=4)
        self.body.grid_columnconfigure(0, weight=3)
        self.body.grid_columnconfigure(1, weight=2)
        self.body.grid_rowconfigure(0, weight=1)
        self.table = DataTable(self.body, [("display_name", "Animal", 100),
                                           ("species_name", "Species", 65), ("age_label", "Age", 80),
                                           ("diagnosis", "Diagnosis", 230), ("condition_level", "Condition", 85),
                                           ("started_at", "Started", 130)], height=18, key="treatment_id",
                               on_select=self.show)
        self.table.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        side = self.card()
        side.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(side, text="Prescription", font=FONT_SUB).pack(anchor="w", padx=14, pady=(12, 4))
        self.presc = DataTable(side, [("medicine_name", "Medicine", 170), ("dosage", "Dosage", 170),
                                      ("duration_days", "Days", 50)], height=8, key="medicine_name")
        self.presc.pack(fill="both", expand=True, padx=12)
        self.notes = ctk.CTkLabel(side, text="", font=FONT_SMALL, text_color=MUTED, wraplength=380, justify="left")
        self.notes.pack(anchor="w", padx=14, pady=12)

    def refresh(self):
        self.table.set_rows(CaseRepository.active_treatments(self.session.vet.vet_id),
                            formatters={"condition_level": nice},
                            tag_fn=lambda r: ("red",) if r["condition_level"] == "CRITICAL" else ())
        self.presc.set_rows([])
        self.notes.configure(text="")

    def show(self, row):
        if row:
            self.presc.set_rows(CaseRepository.prescriptions(row["treatment_id"]))
            self.notes.configure(text=f"Notes: {row['notes'] or '-'}")

    def finish(self):
        row = self.table.selected()
        if row is None:
            error("Select a treatment first.")
            return
        FinishDialog(self, row)


class FinishDialog(Dialog):
    def __init__(self, page, row):
        super().__init__(page, "Finish treatment", 520, 380)
        self.page, self.row = page, row
        ctk.CTkLabel(self, text=f"{row['display_name']} ({row['species_name']}) – {row['diagnosis']}",
                     font=FONT_SUB, wraplength=470).pack(anchor="w", padx=20, pady=(18, 10))
        self.outcome = ctk.StringVar(value="DISCHARGED_TO_SHELTER")
        for v, t in (("DISCHARGED_TO_SHELTER", "Healthy – discharge to a shelter"),
                     ("RELEASED", "Healthy – release to where it was found"),
                     ("DECEASED", "Could not be saved")):
            ctk.CTkRadioButton(self, text=t, variable=self.outcome, value=v, font=FONT,
                               command=self.toggle).pack(anchor="w", padx=24, pady=4)
        ctk.CTkLabel(self, text="Shelter (only shelters that accept this species and have room):", font=FONT_SMALL,
                     text_color=MUTED).pack(anchor="w", padx=20, pady=(10, 2))
        self.shelter = ChoiceBox(self, width=470)
        self.shelter.set_options([(s["shelter_id"], f"{s['shelter_name']}  ({s['animal_count']}/{s['capacity']})")
                                  for s in ShelterRepository.accepting(row["species_id"])])
        self.shelter.pack(padx=20, anchor="w")
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(pady=18)
        button(bar, "Cancel", self.destroy, kind="plain", width=110).pack(side="left", padx=6)
        button(bar, "Finish", self.save, width=140).pack(side="left", padx=6)

    def toggle(self):
        self.shelter.configure(state="normal" if self.outcome.get() == "DISCHARGED_TO_SHELTER" else "disabled")

    def save(self):
        outcome = self.outcome.get()
        shelter = self.shelter.value() if outcome == "DISCHARGED_TO_SHELTER" else None
        if outcome == "DISCHARGED_TO_SHELTER" and shelter is None:
            error("Please choose a shelter.")
            return
        ok, _ = self.page.run(CaseRepository.finish_treatment, self.row["treatment_id"], self.page.session.user_id,
                              outcome, shelter)
        if ok:
            self.destroy()
            msg = "Treatment finished."
            if shelter:
                msg += " The animal is now in the shelter and its vaccination calendar was created."
            info(msg)
            self.page.refresh()


class VaccinationPage(Page):
    title = "Vaccination follow-up"
    subtitle = "Planned vaccinations of the shelter animals assigned to you. Overdue doses are red."

    def build(self):
        self.filter = ctk.CTkSegmentedButton(self.toolbar, values=["Overdue", "Next 7 days", "All planned"],
                                             command=lambda v: self.refresh(), font=FONT)
        self.filter.set("Next 7 days")
        self.filter.pack(side="left", padx=8)
        button(self.toolbar, "Open calendar", self.open_calendar, kind="plain", width=140).pack(side="left", padx=4)
        button(self.toolbar, "Mark as done", self.done, width=140).pack(side="left", padx=4)
        _vet_banner(self)
        self.table = DataTable(self.body, [("planned_date", "Planned", 100), ("display_name", "Animal", 110),
                                           ("species_name", "Species", 65), ("age_label", "Age", 85),
                                           ("shelter_name", "Shelter", 250), ("vaccine_code", "Vaccine", 75),
                                           ("dose_label", "Dose", 110), ("days_left", "Days left", 75)],
                               height=18, key="schedule_id", on_double=lambda r: self.open_calendar())
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        state = {"Overdue": "OVERDUE", "Next 7 days": "THIS_WEEK"}.get(self.filter.get())
        rows = AnimalRepository.due_for_vet(self.session.vet.vet_id, state)
        self.table.set_rows(rows, tag_fn=lambda r: ("red",) if r["due_state"] == "OVERDUE" else
                            ("orange",) if r["due_state"] == "THIS_WEEK" else ())

    def done(self):
        row = self.table.selected()
        if row is None:
            error("Select a vaccination first.")
            return
        if confirm(f"{row['display_name']}: {row['vaccine_code']} ({row['dose_label']}) was given today?"):
            ok, _ = self.run(AnimalRepository.complete_vaccination, row["schedule_id"], self.session.user_id)
            if ok:
                self.refresh()

    def open_calendar(self):
        row = self.table.selected()
        if row is None:
            error("Select a vaccination first.")
            return
        CalendarDialog(self, row["animal_id"])


class CalendarDialog(Dialog):
    def __init__(self, page, animal_id, read_only=False):
        super().__init__(page, "Vaccination calendar", 640, 560)
        self.page, self.animal_id = page, animal_id
        a = AnimalRepository.card(animal_id)
        ctk.CTkLabel(self, text=f"{a.display_name} – {a.species_name}, {a.age_label}", font=FONT_SUB).pack(
            anchor="w", padx=20, pady=(16, 0))
        ctk.CTkLabel(self, text=f"{a.shelter_name or '-'}  ·  followed by {a.responsible_vet_name or '-'}",
                     font=FONT_SMALL, text_color=MUTED).pack(anchor="w", padx=20)
        self.table = DataTable(self, [("planned_date", "Planned", 110), ("vaccine_name", "Vaccine", 230),
                                      ("dose_label", "Dose", 110), ("status", "Status", 80), ("done_date", "Done", 100)],
                               height=12, key="schedule_id")
        self.table.pack(fill="both", expand=True, padx=20, pady=10)
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(pady=(0, 14))
        button(bar, "Close", self.destroy, kind="plain", width=110).pack(side="left", padx=6)
        if not read_only:
            button(bar, "Undo 'done'", self.undo, kind="danger", width=140).pack(side="left", padx=6)
            button(bar, "Mark selected as done", self.done, width=200).pack(side="left", padx=6)
        self.load()

    def load(self):
        from datetime import date
        self.table.set_rows(AnimalRepository.schedule(self.animal_id), formatters={"status": nice},
                            tag_fn=lambda v: ("green",) if v.status == "DONE" else
                            ("red",) if v.planned_date < date.today() else ())

    def done(self):
        v = self.table.selected()
        if v is None or v.status != "PLANNED":
            error("Select a planned vaccination.")
            return
        ok, _ = self.page.run(AnimalRepository.complete_vaccination, v.schedule_id, self.page.session.user_id)
        if ok:
            self.load()
            self.page.refresh()

    def undo(self):
        v = self.table.selected()
        if v is None or v.status != "DONE":
            error("Select a vaccination that is marked as done.")
            return
        if not confirm(f"{v.vaccine_code} ({v.dose_label}) will be planned again. Continue?"):
            return
        ok, _ = self.page.run(AnimalRepository.undo_vaccination, v.schedule_id, self.page.session.user_id)
        if ok:
            self.load()
            self.page.refresh()
