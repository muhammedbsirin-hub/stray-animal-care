import customtkinter as ctk

from app import validators
from app.repositories import NotificationRepository, UserRepository
from app.services import AuthService
from app.ui.pages.base import Page
from app.ui.widgets import (DANGER, FONT, FONT_BOLD, FONT_SMALL, FONT_SUB, MUTED, DataTable, Dialog,
                            button, confirm, entry, error, form_row, info, nice)


class NotificationsPage(Page):
    title = "Notifications"
    subtitle = "Only you can see these messages. Select one to read it."

    def build(self):
        button(self.toolbar, "Mark all as read", self.mark_all, kind="plain", width=150).pack(side="left", padx=4)
        button(self.toolbar, "Delete read ones", self.delete_read, kind="plain", width=150).pack(side="left", padx=4)
        button(self.toolbar, "Delete selected", self.delete, kind="danger", width=140).pack(side="left", padx=4)
        self.table = DataTable(self.body, [("created_at", "Date", 140), ("type", "Type", 150), ("title", "Title", 260),
                                           ("message", "Message", 520)], height=16, key="notification_id",
                               on_select=self.selected)
        self.table.pack(fill="both", expand=True)
        box = self.card()
        box.pack(fill="x", pady=(10, 0))
        self.detail_title = ctk.CTkLabel(box, text="", font=FONT_SUB, anchor="w")
        self.detail_title.pack(fill="x", padx=16, pady=(12, 2))
        self.detail = ctk.CTkLabel(box, text="Select a notification.", font=FONT, anchor="w", justify="left",
                                   wraplength=900, text_color=MUTED)
        self.detail.pack(fill="x", padx=16, pady=(0, 14))

    def refresh(self):
        rows = NotificationRepository.list(self.session.user_id)
        for r in rows:
            r.type = nice(r.notif_type)
        self.table.set_rows(rows, tag_fn=lambda r: ("bold",) if not r.is_read else ("muted",))
        self.main.refresh_badge()

    def selected(self, n):
        if n is None:
            return
        self.detail_title.configure(text=n.title)
        self.detail.configure(text=n.message, text_color=("#111827", "#e5e7eb"))
        if not n.is_read:
            NotificationRepository.mark_read(n.notification_id, self.session.user_id)
            n.is_read = True
            self.table.tree.item(str(n.notification_id), tags=("muted",))
            self.main.refresh_badge()

    def mark_all(self):
        self.run(NotificationRepository.mark_all_read, self.session.user_id)
        self.refresh()

    def delete(self):
        n = self.table.selected()
        if n is None:
            error("Select a notification first.")
            return
        self.run(NotificationRepository.delete, n.notification_id, self.session.user_id)
        self.detail_title.configure(text="")
        self.detail.configure(text="Notification deleted.", text_color=MUTED)
        self.refresh()

    def delete_read(self):
        if confirm("Delete all notifications you have already read?"):
            self.run(NotificationRepository.delete_read, self.session.user_id)
            self.refresh()


class PasswordDialog(Dialog):

    def __init__(self, master, text, on_ok):
        super().__init__(master, "Confirm with your password", 420, 230)
        self.on_ok = on_ok
        ctk.CTkLabel(self, text=text, font=FONT, wraplength=360, justify="left").pack(padx=20, pady=(20, 10))
        self.pw = entry(self, width=360, placeholder="Current password", show="•")
        self.pw.pack(padx=20)
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(pady=16)
        button(bar, "Cancel", self.destroy, kind="plain", width=110).pack(side="left", padx=6)
        button(bar, "Confirm", self.ok, kind="danger", width=130).pack(side="left", padx=6)
        self.pw.bind("<Return>", lambda e: self.ok())

    def ok(self):
        password = self.pw.get()
        self.destroy()
        self.on_ok(password)


class SettingsPage(Page):
    title = "Settings"
    subtitle = "Your profile, password and account."

    def build(self):
        self.body.grid_columnconfigure((0, 1), weight=1)
        prof = self.card()
        prof.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 10))
        ctk.CTkLabel(prof, text="Profile", font=FONT_SUB).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))
        f = ctk.CTkFrame(prof, fg_color="transparent")
        f.grid(row=1, column=0, sticky="w", padx=16)
        self.username = form_row(f, 0, "Username", ctk.CTkLabel(f, text="", font=FONT_BOLD, anchor="w"))
        self.first = form_row(f, 1, "First name", entry(f), True)
        self.last = form_row(f, 2, "Last name", entry(f), True)
        self.email = form_row(f, 3, "E-mail", entry(f), True)
        self.phone = form_row(f, 4, "Phone", entry(f), True)
        button(prof, "Save profile", self.save_profile).grid(row=2, column=0, sticky="w", padx=16, pady=14)

        pw = self.card()
        pw.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 10))
        ctk.CTkLabel(pw, text="Change password", font=FONT_SUB).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))
        g = ctk.CTkFrame(pw, fg_color="transparent")
        g.grid(row=1, column=0, sticky="w", padx=16)
        self.old_pw = form_row(g, 0, "Current password", entry(g, show="•"), True)
        self.new_pw = form_row(g, 1, "New password", entry(g, show="•"), True)
        self.new_pw2 = form_row(g, 2, "Repeat new password", entry(g, show="•"), True)
        ctk.CTkLabel(pw, text="8+ characters, upper and lower case, a digit and a special character.",
                     font=FONT_SMALL, text_color=MUTED).grid(row=2, column=0, sticky="w", padx=16)
        button(pw, "Change password", self.change_password, width=170).grid(row=3, column=0, sticky="w", padx=16,
                                                                             pady=14)
        row = 1
        if self.session.vet:
            work = self.card()
            work.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 10))
            v = self.session.vet
            ctk.CTkLabel(work, text="Work information", font=FONT_SUB).pack(anchor="w", padx=16, pady=(14, 4))
            ctk.CTkLabel(work, text=f"Clinic: {v.clinic_name}\nShift: {v.shift_text}\nLicense no: {v.license_no}",
                         font=FONT, justify="left").pack(anchor="w", padx=16, pady=(0, 14))
            row += 1
        if self.session.is_admin() or self.session.is_vet():
            return
        danger = self.card()
        danger.grid(row=row, column=0, columnspan=2, sticky="ew")
        ctk.CTkLabel(danger, text="Delete account", font=FONT_SUB, text_color=DANGER).pack(anchor="w", padx=16,
                                                                                           pady=(14, 2))
        ctk.CTkLabel(danger, text="Your account will be closed. Your feeding posts are hidden, your emojis are removed "
                                  "and your pending applications are withdrawn. Records such as reports and adoptions "
                                  "are kept for the shelters.", font=FONT_SMALL, text_color=MUTED, wraplength=900,
                     justify="left").pack(anchor="w", padx=16)
        button(danger, "Delete my account", self.delete_account, kind="danger", width=180).pack(anchor="w", padx=16,
                                                                                                pady=14)

    def refresh(self):
        u = UserRepository.get(self.session.user_id)
        self.username.configure(text=u.username)
        for w, val in ((self.first, u.first_name), (self.last, u.last_name), (self.email, u.email),
                       (self.phone, u.phone)):
            w.delete(0, "end")
            w.insert(0, val)

    def save_profile(self):
        first, last = self.first.get().strip(), self.last.get().strip()
        email, phone = self.email.get().strip(), self.phone.get().strip()
        err = validators.first_error(validators.person_name(first, "First name"),
                                     validators.person_name(last, "Last name"),
                                     validators.email(email), validators.phone(phone))
        if not err and UserRepository.email_taken(email, self.session.user_id):
            err = "This e-mail address is used by another account."
        if err:
            error(err)
            return
        ok, _ = self.run(UserRepository.update_profile, self.session.user_id, first, last, email, phone)
        if ok:
            self.main.reload_session()
            self.main.refresh_badge()
            info("Your profile was saved.")

    def change_password(self):
        if not AuthService.verify_password(self.session.user_id, self.old_pw.get()):
            error("The current password is wrong.")
            return
        err = validators.password(self.new_pw.get(), self.new_pw2.get())
        if not err and self.new_pw.get() == self.old_pw.get():
            err = "The new password must be different from the current one."
        if err:
            error(err)
            return
        ok, _ = self.run(UserRepository.change_password, self.session.user_id, self.new_pw.get())
        if ok:
            for w in (self.old_pw, self.new_pw, self.new_pw2):
                w.delete(0, "end")
            self.main.refresh_badge()
            info("Your password was changed.")

    def delete_account(self):
        if not confirm("Do you really want to delete your account? This cannot be undone from the app."):
            return

        def do(password):
            if not AuthService.verify_password(self.session.user_id, password):
                error("The password is wrong. Your account was not deleted.")
                return
            ok, _ = self.run(UserRepository.delete_account, self.session.user_id, self.session.user_id)
            if ok:
                info("Your account was deleted. Goodbye!")
                self.main.logout()

        PasswordDialog(self, "Enter your password to delete your account.", do)
