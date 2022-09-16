import argparse
import zlog
import multiprocessing
import logging
import json

from multiprocessing.synchronize import Event

from tennis import (
    Facility,
    Court,
    User,
    Booker,
    Website,
    Availability,
    DateTime,
    Preferences,
)

from typing import List, Tuple


def load_data(data: str) -> Tuple[Website, List[User], List[Court]]:
    with open(data, "r") as f:
        data = json.load(f)

    tennis_facilities = [
        Facility.from_dict(tennis_facility)
        for tennis_facility in data["tennis_facilities"]
    ]

    courts = [
        court
        for tennis_facility in tennis_facilities
        for court in tennis_facility.courts
    ]

    users = [User(**user) for user in data["users"]]
    website = Website(**data["website"])

    return website, users, courts


def worker(
    website,
    headless: bool,
    users: List[User],
    availabilities: List[Availability],
    booked: Event,
) -> None:

    booker = Booker(website, headless)

    while True:
        if booked.is_set():
            return

        for user in users:
            for availability in availabilities:
                success = booker.book(user, availability)
                if success:
                    booked.set()
                    return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data.json")
    parser.add_argument(
        "--tennis-facility",
        type=str,
        default=None,
        required=False,
        help="Name of the tennis facility. If not specified, all tennis facilities will be considered.",
    )
    parser.add_argument(
        "--location",
        type=str,
        default=None,
        choices=["indoor", "outdoor"],
        required=False,
        help="Location (indoor or outdoor). If not specified, both will be considered.",
    )
    parser.add_argument(
        "--surface-type",
        type=str,
        default=None,
        choices=["synthetique", "beton_poreux"],
        required=False,
        help="Surface type (synthetique or beton_poreux). If not specified, both will be considered.",
    )
    parser.add_argument(
        "--court-id",
        type=str,
        default=None,
        required=False,
        help="Court ID. If not specified, all courts will be considered.",
    )
    parser.add_argument(
        "--username",
        type=str,
        default=None,
        required=False,
        help="Username. If not specified, all users will be used.",
    )
    parser.add_argument("--date", type=str, help="format: 01/01/2022", required=True)
    parser.add_argument("--time", type=str, help="format: 08h", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--headless", action="store_true", default=False)
    parser.add_argument("--logger-pretty", action="store_true", default=False)
    args = parser.parse_args()

    zlog.configure(pretty=args.logger_pretty)

    preferences = Preferences(
        tennis_facility=args.tennis_facility,
        location=args.location,
        surface_type=args.surface_type,
        court_id=args.court_id,
        username=args.username,
    )

    website, users, courts = load_data(args.data)

    users = [user for user in users if preferences.check(user)]
    for user in users:
        logging.info(f"Will use user: {user}")

    courts = [court for court in courts if preferences.check(court)]

    date_time = DateTime(args.date, args.time)
    availabilities = []
    for court in courts:
        availabilities.append(Availability(date_time, court))
        logging.info(f"Availability {availabilities[-1]} will be considered.")

    manager = multiprocessing.Manager()
    booked = manager.Event()

    logging.info(f"Starting {args.workers} workers.")

    processes = []
    for _ in range(args.workers):
        process = multiprocessing.Process(
            target=worker, args=(website, args.headless, users, availabilities, booked),
        )
        process.start()
        processes.append(process)

    booked.wait()

    for process in processes:
        process.terminate()

    for process in processes:
        process.join()

    logging.info("Done.")


if __name__ == "__main__":
    main()
