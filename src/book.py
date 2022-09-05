import time
import argparse
import json

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from typing import List


class DateTimeNotAvailableException(Exception):
    pass


class CarnetIsEmptyException(Exception):
    pass


def reformat_date_and_time(date: str, time: str):
    date = date.split("/")
    date = f"{date[2]}/{date[1]}/{date[0]}"
    time = time[:-1] + ":00:00"
    return f"{date} {time}"


def login(driver: webdriver.Chrome, url: str, username: str, password: str) -> None:
    driver.get(url)

    username_element = driver.find_element(by="id", value="username")
    password_element = driver.find_element(by="id", value="password")

    username_element.send_keys(username)
    password_element.send_keys(password)

    driver.find_element(by="name", value="Submit").click()


def book_court(
    driver: webdriver.Chrome,
    search_url: str,
    court_ids: List[str],
    date: str,
    time: str,
) -> None:

    driver.execute_script(f"window.open('{search_url}', 'new_window')")

    driver.switch_to.window(driver.window_handles[1])

    when = driver.find_element(by="id", value="when")
    when.click()

    try:
        date_element = driver.find_element(
            by=By.XPATH, value=f"//div[@dateiso='{date}']"
        )
        driver.execute_script("arguments[0].click();", date_element)
    except NoSuchElementException:
        raise DateTimeNotAvailableException(f"Date {date} not available")

    rechercher = driver.find_element(by="id", value="rechercher")
    rechercher.click()

    leaflets = driver.find_element(by=By.CLASS_NAME, value="leaflet-marker-pane")

    leaflets = leaflets.find_elements(by=By.XPATH, value=".//*")

    # Elisabeth is leaflet 18
    leaflets[18].click()

    link = driver.find_element(by=By.CLASS_NAME, value="accessTennisMap")
    link.send_keys("\n")

    times = driver.find_elements(by=By.CLASS_NAME, value="panel-title")

    found = False
    for t in times:
        if t.text == time:
            t.click()
            found = True
            break

    if not found:
        raise DateTimeNotAvailableException(
            f"Time {time} not available for date {date}"
        )

    reserve_buttons = driver.find_elements(
        by=By.XPATH,
        value="//button[@class='btn btn-darkblue medium rollover rollover-grey buttonAllOk']",
    )

    for button in reserve_buttons:
        if (
            button.get_attribute("datedeb") == reformat_date_and_time(date, time)
            and button.get_attribute("courtid") in court_ids
        ):
            driver.execute_script("arguments[0].click();", button)
            break

    inputs = driver.find_elements(
        by=By.XPATH, value="//input[@class='form-control required']"
    )

    inputs[0].send_keys("Azarova")
    inputs[1].send_keys("Anna")

    ajouter_button = driver.find_element(
        by=By.XPATH,
        value="//button[@class='btn btn-darkblue small addPlayer rollover rollover-grey']",
    )
    ajouter_button.click()

    inputs = driver.find_elements(
        by=By.XPATH, value="//input[@class='form-control required']"
    )

    inputs[2].send_keys("Memari")
    inputs[3].send_keys("Issa")
    inputs[3].send_keys("\t")

    submit_button = driver.find_element(by=By.ID, value="submitControle")
    submit_button.click()

    # find table tags
    tables = driver.find_elements(by=By.TAG_NAME, value="table")
    found = False
    for table in tables:
        if table.text.startswith("J’utilise 1 heure\nde mon carnet en ligne"):
            table.click()
            found = True
            break

    if not found:
        raise CarnetIsEmptyException("Carnet is empty")

    submit_button = driver.find_element(by=By.ID, value="submit")
    submit_button.click()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--config", type=str, default="config.json")
    parser.add_argument("--uncovered", action="store_true")
    parser.add_argument("--date", type=str, help="format: 01/01/2022", required=True)
    parser.add_argument("--time", type=str, help="format: 08h", required=True)
    args = parser.parse_args()

    options = webdriver.ChromeOptions()
    if args.headless:
        options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    with open(args.config, "r") as f:
        config = json.load(f)

    login(driver, **config["login"])

    court_ids = config["courts"]["covered"]
    if args.uncovered:
        court_ids = config["courts"]["uncovered"]

    try:
        book_court(driver, config["search_url"], court_ids, args.date, args.time)
    except Exception as e:
        print(e)

    time.sleep(1000)

    driver.quit()


if __name__ == "__main__":
    main()
