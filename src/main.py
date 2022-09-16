import argparse
import zlog
import multiprocessing
import logging

from multiprocessing.synchronize import Event

from tennis import TennisFacility, User, Booker, Website, Availability, DateTime
from utils import load_json
from typing import List


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
        choices=["synthetic", "beton_poreux"],
        required=False,
        help="Surface type (synthetic or beton_poreux). If not specified, both will be considered.",
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

    data = load_json(args.data)

    tennis_facilities = []
    for tennis_facility in data["tennis_facilities"]:
        if (
            args.tennis_facility is not None
            and tennis_facility["name"] != args.tennis_facility
        ):
            continue

        tennis_facilities.append(TennisFacility.from_dict(tennis_facility))

    courts = []
    for tennis_facility in tennis_facilities:
        for court in tennis_facility.courts:
            if args.location and court.location.value != args.location:
                continue

            if args.surface_type and court.surface_type.value != args.surface_type:
                continue

            if args.court_id and court.id != args.court_id:
                continue

            courts.append(court)

    users = data["users"]
    users = []
    for user in data["users"]:
        if args.username and user["username"] != args.username:
            continue
        users.append(User(**user))

    website = Website(**data["website"])

    availabilities = []
    for court in courts:
        availabilities.append(
            Availability(date_time=DateTime(args.date, args.time), court=court)
        )
        logging.info(f"Will try to book availability: {availabilities[-1]}")

    manager = multiprocessing.Manager()
    booked = manager.Event()

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


if __name__ == "__main__":
    main()
