import argparse
import json
import traceback
import zlog
import logging

from datetime import datetime
from booking import Booker
from threading import Thread, Event, get_ident

from exceptions import (
    AlreadyReservedException,
    CarnetIsEmptyException,
    DateTimeNotAvailableException,
)



def worker(booker, booked_event, search_url, court_ids, date, time):
    while True:
        try:
            booker.book_court(search_url, court_ids, date, time)
        except (
            AlreadyReservedException,
            CarnetIsEmptyException,
            DateTimeNotAvailableException,
        ) as e:
            dic = {
                "thread_id": get_ident(),
                "exception": str(e),
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            }
            logging.info("expected exception", dic)
            continue
        except Exception as e:
            dic = {
                "thread_id": get_ident(),
                "exception": str(e),
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "stacktrace": traceback.format_exc(),
            }
            logging.error("unexpected exception", dic)
            break
        else:
            booked_event.set()
            dic = {
                "thread_id": get_ident(),
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            }
            logging.info("court booked", dic)
            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config.json")
    parser.add_argument("--uncovered", action="store_true")
    parser.add_argument("--date", type=str, help="format: 01/01/2022", required=True)
    parser.add_argument("--time", type=str, help="format: 08h", required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    zlog.configure(pretty=True)

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
                config["login"]["url"], account["username"], account["password"]
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
