"""All pages of the menu, so app_window can import them from one place."""
from app.ui.pages.admin import (AdminMapPage, AnimalsPage, ApplicationsPage, ClinicsPage, OverviewPage, SheltersPage,
                                UsersPage, VetReportPage, VetsPage)
from app.ui.pages.vet import CasesPage, TreatmentsPage, VaccinationPage
from app.ui.pages.volunteer import (AdoptPage, MapPage, MyAdoptionsPage, MyApplicationsPage, MyPostsPage,
                                    MyReactionsPage, MyReportsPage, ReportInjuryPage)
from app.ui.pages.common import NotificationsPage, SettingsPage
