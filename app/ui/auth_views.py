"""Login and registration screens."""
import customtkinter as ctk

from app import validators
from app.db import DbError
from app.repositories import LookupRepository, UserRepository
from app.services import AuthService
from app.ui.widgets import (FONT, FONT_SMALL, FONT_TITLE, MUTED, DANGER, PRIMARY, ChoiceBox, button, entry,
                            form_row, info)


class LoginView(ctk.CTkFrame):
    def __init__(self, master, app, username=""):
        super().__init__(master, fg_color=("#eef3ef", "#1f1f1f"))
        self.app = app
        card = ctk.CTkFrame(self, corner_radius=16, fg_color=("#ffffff", "#2b2b2b"))
        card.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(card, text="\U0001F43E  Stray Animal Care", font=FONT_TITLE, text_color=PRIMARY).pack(
            padx=50, pady=(36, 4))
        ctk.CTkLabel(card, text="Volunteers, veterinarians and shelters together", font=FONT, text_color=MUTED).pack(
            padx=50, pady=(0, 24))
        self.username = entry(card, width=300, placeholder="Username")
        self.username.pack(padx=50, pady=6)
        self.password = entry(card, width=300, placeholder="Password", show="•")
        self.password.pack(padx=50, pady=6)
        self.status = ctk.CTkLabel(card, text="", font=FONT_SMALL, text_color=DANGER, wraplength=300)
        self.status.pack(padx=50, pady=(4, 0))
        button(card, "Sign in", self.login, width=300).pack(padx=50, pady=(10, 6))
        ctk.CTkButton(card, text="New here? Create a volunteer account", fg_color="transparent", text_color=PRIMARY,
                      hover_color=("#e6f2ec", "#333333"), font=FONT, command=app.show_register).pack(
            padx=50, pady=(0, 30))
        if username:
            self.username.insert(0, username)
            self.after(100, self.password.focus_set)
        else:
            self.after(100, self.username.focus_set)
        self.password.bind("<Return>", lambda e: self.login())
        self.username.bind("<Return>", lambda e: self.password.focus_set())

    def login(self):
        try:
            session = AuthService.login(self.username.get(), self.password.get())
        except DbError as e:
            self.status.configure(text=str(e))
            return
        self.app.show_main(session)


class RegisterView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=("#eef3ef", "#1f1f1f"))
        self.app = app
        card = ctk.CTkFrame(self, corner_radius=16, fg_color=("#ffffff", "#2b2b2b"))
        card.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(card, text="Create a volunteer account", font=FONT_TITLE, text_color=PRIMARY).grid(
            row=0, column=0, columnspan=2, padx=40, pady=(28, 4))
        ctk.CTkLabel(card, text="Every new member joins as a Volunteer. Fields with * are required.",
                     font=FONT_SMALL, text_color=MUTED).grid(row=1, column=0, columnspan=2, pady=(0, 14))
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.grid(row=2, column=0, columnspan=2, padx=40)
        self.first = form_row(form, 0, "First name", entry(form), True)
        self.last = form_row(form, 1, "Last name", entry(form), True)
        self.username = form_row(form, 2, "Username", entry(form, placeholder="3-20 letters, digits, _"), True)
        self.email = form_row(form, 3, "E-mail", entry(form, placeholder="name@mail.com"), True)
        self.phone = form_row(form, 4, "Phone", entry(form, placeholder="05XXXXXXXXX"), True)
        self.district = form_row(form, 5, "District", ChoiceBox(form, placeholder="(optional)"))
        self.password = form_row(form, 6, "Password", entry(form, show="•"), True)
        self.password2 = form_row(form, 7, "Repeat password", entry(form, show="•"), True)
        self.rules = ctk.CTkLabel(form, text="", font=FONT_SMALL, text_color=MUTED, justify="left", anchor="w")
        self.rules.grid(row=8, column=1, sticky="w")
        self.status = ctk.CTkLabel(card, text="", font=FONT_SMALL, text_color=DANGER, wraplength=420)
        self.status.grid(row=3, column=0, columnspan=2, pady=(8, 0))
        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.grid(row=4, column=0, columnspan=2, pady=(10, 26))
        button(bar, "Back to sign in", app.show_login, kind="plain").pack(side="left", padx=6)
        button(bar, "Create account", self.register, width=180).pack(side="left", padx=6)
        self.password.bind("<KeyRelease>", lambda e: self._show_rules())
        self._show_rules()
        try:
            self.district.set_options([(d["district_id"], d["district_name"]) for d in LookupRepository.districts()])
        except DbError as e:
            self.status.configure(text=str(e))

    def _show_rules(self):
        problems = validators.password_problems(self.password.get())
        if not self.password.get():
            self.rules.configure(text="Password: 8+ characters, upper and lower case, digit, special character",
                                 text_color=MUTED)
        elif problems:
            self.rules.configure(text="Still needed: " + ", ".join(problems), text_color=DANGER)
        else:
            self.rules.configure(text="✓ Strong password", text_color=PRIMARY)

    def register(self):
        data = {"first_name": self.first.get().strip(), "last_name": self.last.get().strip(),
                "username": self.username.get().strip(), "email": self.email.get().strip(),
                "phone": self.phone.get().strip(), "district_id": self.district.value(),
                "password": self.password.get(), "password2": self.password2.get()}
        try:
            problem = AuthService.validate_registration(data)
            if problem:
                self.status.configure(text=problem)
                return
            UserRepository.register_volunteer(data)
        except DbError as e:
            self.status.configure(text=str(e))
            return
        info("Your volunteer account was created. You can sign in now.", "Welcome!")
        self.app.show_login(data["username"])
