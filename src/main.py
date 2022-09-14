import argparse
import json
import zlog

from booking import Booker
from threading import Thread, Event


def worker(booker, booked_event, search_url, court_ids, date, time):
    while True:
        if booked_event.isSet():
            return

        success = booker.book_court(search_url, court_ids, date, time)
        if success:
            booked_event.set()
            return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config.json")
    parser.add_argument("--uncovered", action="store_true")
    parser.add_argument("--date", type=str, help="format: 01/01/2022", required=True)
    parser.add_argument("--time", type=str, help="format: 08h", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--headless", action="store_true", default=False)
    parser.add_argument("--logger-pretty", action="store_true", default=False)
    args = parser.parse_args()

    zlog.configure(pretty=args.logger_pretty)

    with open(args.config, "r") as f:
        config = json.load(f)

    court_ids = config["courts"]["covered"]
    if args.uncovered:
        court_ids = config["courts"]["uncovered"]

    booked_event = Event()

    threads = []
    for account in config["login"]["accounts"][:1]:
        for _ in range(args.workers):
            booker = Booker(
                config["login"]["url"],
                account["username"],
                account["password"],
                headless=args.headless,
            )
            thread = Thread(
                target=worker,
                args=(
                    booker,
                    booked_event,
                    config["search_url"],
                    court_ids,
                    args.date,
                    args.time,
                ),
            )
            threads.append(thread)
            thread.start()

    booked_event.wait()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
