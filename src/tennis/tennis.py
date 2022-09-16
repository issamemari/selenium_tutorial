from dataclasses import dataclass
from typing import List
from enum import Enum


@dataclass
class TennisCourt:
    class Location(Enum):
        OUTDOOR = "outdoor"
        INDOOR = "indoor"

    class SurfaceType(Enum):
        SYNTHETIC = "synthetic"
        BETON_POREUX = "beton_poreux"

    id: str
    name: str
    facility_name: str
    location: Location
    surface_type: SurfaceType

    def __str__(self) -> str:
        return f"{self.facility_name} {self.name} ({self.id})"


@dataclass
class DateTime:
    date: str
    time: str

    def __str__(self) -> str:
        date = self.date.split("/")
        date = f"{date[2]}/{date[1]}/{date[0]}"
        time = self.time[:-1] + ":00:00"
        return f"{date} {time}"


@dataclass
class TennisFacility:
    name: str
    leaflet_index: int
    courts: List[TennisCourt]

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def from_dict(data: dict) -> "TennisFacility":
        courts = []
        for court in data["courts"]:
            courts.append(
                TennisCourt(
                    id=court["id"],
                    name=court["name"],
                    facility_name=data["name"],
                    location=TennisCourt.Location(court["location"]),
                    surface_type=TennisCourt.SurfaceType(court["surface_type"]),
                )
            )

        return TennisFacility(
            name=data["name"], leaflet_index=data["leaflet_index"], courts=courts,
        )


@dataclass
class Availability:
    date_time: DateTime
    court: TennisCourt

    def __str__(self) -> str:
        return f"{self.court} {self.date_time}"
