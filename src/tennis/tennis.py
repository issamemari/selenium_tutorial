from dataclasses import dataclass
from typing import List
from enum import Enum


@dataclass
class Court:
    class Location(Enum):
        OUTDOOR = "outdoor"
        INDOOR = "indoor"

    class SurfaceType(Enum):
        SYNTHETIQUE = "synthetique"
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
class Facility:
    name: str
    leaflet_index: int
    courts: List[Court]

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def from_dict(data: dict) -> "Facility":
        courts = []
        for court in data["courts"]:
            courts.append(
                Court(
                    id=court["id"],
                    name=court["name"],
                    facility_name=data["name"],
                    location=Court.Location(court["location"]),
                    surface_type=Court.SurfaceType(court["surface_type"]),
                )
            )

        return Facility(
            name=data["name"], leaflet_index=data["leaflet_index"], courts=courts,
        )


@dataclass
class Availability:
    date_time: DateTime
    court: Court

    def __str__(self) -> str:
        return f"{self.court} {self.date_time}"
