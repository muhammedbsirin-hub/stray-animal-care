"""Main window: switches between sign-in, registration and the role based main view."""
import customtkinter as ctk

from app.config import APP_TITLE, NOTIFICATION_REFRESH_MS
from app.db import DbError
from app.repositories import CaseRepository, NotificationRepository
from app.services import AuthService
from app.ui.auth_views import LoginView, RegisterView
from app.ui.pages import (AdminMapPage, AdoptPage, AnimalsPage, ApplicationsPage, CasesPage, ClinicsPage, MapPage,
                          MyAdoptionsPage, MyApplicationsPage, MyPostsPage, MyReactionsPage, MyReportsPage,
                          NotificationsPage, OverviewPage, ReportInjuryPage, SettingsPage, SheltersPage, TreatmentsPage,
                          UsersPage, VaccinationPage, VetReportPage, VetsPage)
from app.ui.widgets import DANGER, FONT, FONT_BOLD, FONT_SMALL, MUTED, PRIMARY, error, style_tables


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        self.title(APP_TITLE)
        self.geometry("1320x820")
        self.minsize(1100, 680)
        style_tables()
        self.view = None
        self.show_login()

    def _swap(self, view):
        if self.view is not None:
            self.view.destroy()
        self.view = view
        view.pack(fill="both", expand=True)

    def show_login(self, username=""):
        self._swap(LoginView(self, self, username))

    def show_register(self):
        self._swap(RegisterView(self, self))

    def show_main(self, session):
        if session.is_vet():
            try:
                CaseRepository.close_old_cases()
            except DbError:
                pass
        self._swap(MainView(self, self, session))


def build_menu(session):
    items = []
    if session.is_admin():
        items += [("Overview", OverviewPage), ("Adoption applications", ApplicationsPage),
                  ("Feeding map", AdminMapPage), ("Daily vet report", VetReportPage),
                  ("Shelters", SheltersPage), ("Clinics", ClinicsPage),
                  ("Veterinarians", VetsPage), ("Animals", AnimalsPage), ("Users", UsersPage)]
    if session.is_vet():
        items += [("Incoming cases", CasesPage), ("Under treatment", TreatmentsPage),
                  ("Vaccination follow-up", VaccinationPage)]
    if session.is_volunteer():
        items += [("Feeding map", MapPage), ("My posts", MyPostsPage),
                  ("My emojis", MyReactionsPage), ("Report injured animal", ReportInjuryPage),
                  ("My reports", MyReportsPage), ("Adopt a friend", AdoptPage),
                  ("My applications", MyApplicationsPage)]
        if session.is_adopter():
            items.append(("My adoptions", MyAdoptionsPage))
    items += [("Notifications", NotificationsPage), ("Settings", SettingsPage)]
    return items


class MainView(ctk.CTkFrame):
    def __init__(self, master, app, session):
        super().__init__(master, fg_color=("#f3f6f4", "#1f1f1f"))
        self.app = app
        self.session = session
        self.pages = {}
        self.buttons = {}
        self.current = None
        self._poll_id = None
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=("#ffffff", "#262626"))
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=18, pady=14)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self.menu = build_menu(session)
        self._build_buttons()
        self.open_page(self.menu[0][0])
        self.refresh_badge()

    # ---------------------------------------------------------------- sidebar
    def _build_sidebar(self):
        u = self.session.user
        ctk.CTkLabel(self.sidebar, text="\U0001F43E Stray Animal Care", font=("Segoe UI", 16, "bold"),
                     text_color=PRIMARY).pack(padx=16, pady=(18, 10), anchor="w")
        ctk.CTkLabel(self.sidebar, text=u.full_name, font=FONT_BOLD, anchor="w").pack(padx=16, anchor="w")
        roles = [r.capitalize() for r in ("ADMIN", "VET", "VOLUNTEER", "ADOPTER") if u.has_role(r)]
        sub = " · ".join(roles)
        if self.session.vet:
            sub += f"\n{self.session.vet.clinic_name}\n{self.session.vet.shift_text}"
        ctk.CTkLabel(self.sidebar, text=sub, font=FONT_SMALL, text_color=MUTED, justify="left", anchor="w").pack(
            padx=16, pady=(0, 12), anchor="w")
        self.nav = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.nav.pack(fill="both", expand=True, padx=6)
        ctk.CTkButton(self.sidebar, text="Sign out", fg_color="transparent", text_color=DANGER, border_width=1,
                      border_color=DANGER, hover_color=("#fbeaea", "#3a2a2a"), font=FONT,
                      command=self.logout).pack(fill="x", padx=14, pady=14)

    def _build_buttons(self):
        for w in self.nav.winfo_children():
            w.destroy()
        self.buttons = {}
        for name, _ in self.menu:
            b = ctk.CTkButton(self.nav, text=name, anchor="w", font=FONT, height=36, corner_radius=8,
                              fg_color="transparent", text_color=("#1f2937", "#e5e7eb"),
                              hover_color=("#e6f2ec", "#333333"), command=lambda n=name: self.open_page(n))
            b.pack(fill="x", pady=2)
            self.buttons[name] = b

    def open_page(self, name):
        cls = dict(self.menu).get(name)
        if cls is None:
            return
        if self.current is not None:
            self.current.grid_remove()
        if name not in self.pages:
            self.pages[name] = cls(self.content, self)
        page = self.pages[name]
        page.grid(row=0, column=0, sticky="nsew")
        self.current = page
        for n, b in self.buttons.items():
            b.configure(fg_color=PRIMARY if n == name else "transparent",
                        text_color="#ffffff" if n == name else ("#1f2937", "#e5e7eb"))
        try:
            page.refresh()
        except Exception as e:  # keep the app alive, show the reason
            error(str(e))

    # ---------------------------------------------------------------- notifications
    def refresh_badge(self):
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
        try:
            n = NotificationRepository.unread_count(self.session.user_id)
            b = self.buttons.get("Notifications")
            if b is not None:
                b.configure(text=f"Notifications  ({n})" if n else "Notifications")
        except DbError:
            pass
        self._poll_id = self.after(NOTIFICATION_REFRESH_MS, self.refresh_badge)

    def reload_session(self):
        """Roles may change (e.g. ADOPTER after approval)."""
        new = AuthService.reload(self.session)
        if new.user.roles != self.session.user.roles:
            self.session = new
            self.menu = build_menu(new)
            self._build_buttons()
        else:
            self.session = new

    def logout(self):
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
        self.app.show_login()

    def destroy(self):
        if getattr(self, "_poll_id", None) is not None:
            try:
                self.after_cancel(self._poll_id)
            except Exception:
                pass
        super().destroy()
