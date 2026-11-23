"""
Entity classes.  Each class corresponds to one table (or view) of the
database; repositories turn query rows into these objects.
"""
from dataclasses import dataclass, field, fields
from datetime import date, datetime
from typing import Optional


def _from_row(cls, row):
    names = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in row.items() if k in names})


@dataclass
class User:
    user_id: int
    username: str
    first_name: str
    last_name: str
    email: str
    phone: str
    is_active: bool = True
    roles: set = field(default_factory=set)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def has_role(self, role):
        return role in self.roles

    from_row = classmethod(_from_row)


@dataclass
class Veterinarian:
    vet_id: int
    user_id: int
    clinic_id: int
    clinic_name: str
    shift: str
    license_no: str

    @property
    def shift_text(self):
        return "Morning shift (07:00 - 16:59)" if self.shift == "MORNING" else "Evening shift (17:00 - 06:59)"

    from_row = classmethod(_from_row)


@dataclass
class Session:
    """The user that is logged in."""
    user: User
    vet: Optional[Veterinarian] = None

    @property
    def user_id(self):
        return self.user.user_id

    def is_admin(self):
        return self.user.has_role("ADMIN")

    def is_vet(self):
        return self.user.has_role("VET")

    def is_volunteer(self):
        return self.user.has_role("VOLUNTEER")

    def is_adopter(self):
        return self.user.has_role("ADOPTER")


@dataclass
class Animal:
    animal_id: int
    display_name: str
    species_id: int
    species_name: str
    breed_name: str
    sex: str
    color: Optional[str]
    status: str
    age_weeks: int
    age_label: str
    is_neutered: bool = False
    description: Optional[str] = None
    photo_path: Optional[str] = None
    shelter_id: Optional[int] = None
    shelter_name: Optional[str] = None
    responsible_vet_name: Optional[str] = None

    from_row = classmethod(_from_row)


@dataclass
class Shelter:
    shelter_id: int
    shelter_name: str
    district_name: str
    address: str
    phone: str
    capacity: int
    accepted_species: Optional[str]
    animal_count: int
    occupancy_pct: Optional[int]
    partner_clinic: str
    cat_count: int = 0
    dog_count: int = 0
    latitude: float = 0
    longitude: float = 0

    from_row = classmethod(_from_row)


@dataclass
class FeedingPost:
    post_id: int
    user_id: int
    username: str
    full_name: str
    latitude: float
    longitude: float
    photo_path: str
    note: Optional[str]
    posted_at: datetime
    reaction_count: int = 0

    from_row = classmethod(_from_row)


@dataclass
class InjuryReport:
    report_id: int
    reported_at: datetime
    species_name: str
    condition_desc: str
    clinic_name: str
    vet_name: str
    shift: str
    status: str
    approx_age_weeks: Optional[int] = None
    color: Optional[str] = None
    district_name: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    species_id: Optional[int] = None
    result: Optional[str] = None

    from_row = classmethod(_from_row)


@dataclass
class VaccinationItem:
    schedule_id: int
    animal_id: int
    vaccine_code: str
    vaccine_name: str
    dose_label: str
    planned_date: date
    status: str = "PLANNED"
    done_date: Optional[date] = None

    from_row = classmethod(_from_row)


@dataclass
class Notification:
    notification_id: int
    notif_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    from_row = classmethod(_from_row)
