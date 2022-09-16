import logging
import os

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager

from .tennis import Availability, Facility, Court
from .auth import User, Website

from typing import Union
from dataclasses import dataclass


@dataclass
class Preferences:
    tennis_facility: str = None
    location: str = None
    surface_type: str = None
    court_id: str = None
    username: str = None

    def check(self, obj: Union[Facility, Court]) -> bool:
        if isinstance(obj, Facility):
            return self._check_facility(obj)
        elif isinstance(obj, Court):
            return self._check_court(obj)
        elif isinstance(obj, User):
            return self._check_user(obj)
        raise TypeError(f"Unexpected type: {type(obj)}")

    def _check_facility(self, tennis_facility: Facility) -> bool:
        if self.tennis_facility is None:
            return True
        return tennis_facility == self.tennis_facility

    def _check_court(self, court: Court) -> bool:
        if self.location is not None and court.location.value != self.location:
            return False
        if (
            self.surface_type is not None
            and court.surface_type.value != self.surface_type
        ):
            return False
        if self.court_id is not None and court.id != self.court_id:
            return False
        return True

    def _check_user(self, user: User) -> bool:
        if self.username is not None and user.username != self.username:
            return False
        return True


class Booker:
    def __init__(self, website: Website, headless: bool = True):
        """
        Booker object. This object is used to book a tennis court on the
        website of Paris tennis.

        Parameters
        ----------
        website : Website
            Website object containing the login and search URLs.

        user : User
            User object containing the username and password.

        headless : bool, optional
            Whether to run the browser in headless mode or not, by default True
        """
        self.headless = headless
        self.website = website

    def _create_driver(self) -> webdriver.Chrome:
        """
        Create a Chrome driver. This method will create a Chrome driver with
        the appropriate options (headless, etc.).

        Returns
        -------
        webdriver.Chrome
            Chrome driver
        """
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")

        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

    def _login(self, driver: webdriver.Chrome, user: User) -> None:
        """
        Login to the website. This method will use the login URL and the
        username and password of the User object to login to the website.
        """
        driver.get(self.website.login_url)

        username_element = driver.find_element(by="id", value="username")
        password_element = driver.find_element(by="id", value="password")

        username_element.send_keys(user.username)
        password_element.send_keys(user.password)

        driver.find_element(by="name", value="Submit").click()

        logging.info(f"Logged in as {user.username}.")

    def book(self, user: User, availability: Availability) -> bool:
        """
        Book a tennis court. This method will login to the website, search for
        the availability, and book the court. It will return True if the
        booking was successful, and False otherwise.

        Parameters
        ----------
        availability : Availability
            Availability object containing the court_id and date and time of the
            booking.
        """

        driver = self._create_driver()

        self._login(driver, user)

        driver.execute_script(
            f"window.open('{self.website.search_url}', '_blank').focus()"
        )

        if len(driver.window_handles) > 1:
            driver.close()

        driver.switch_to.window(driver.window_handles[0])

        logging.info("Opened search page.")

        try:
            when = driver.find_element(by="id", value="when")
            driver.execute_script("arguments[0].click();", when)
        except NoSuchElementException as e:
            logging.error("Failed to find when element.", {"exception": str(e)})
            return False
        except Exception as e:
            logging.error("Unexpected exception.", {"exception": str(e)})
            return False

        try:
            date_element = driver.find_element(
                by=By.XPATH, value=f"//div[@dateiso='{availability.date_time.date}']"
            )
            driver.execute_script("arguments[0].click();", date_element)
        except NoSuchElementException as e:
            logging.error(
                f"Failed to find date element. Date {availability.date_time.date} is not available.",
                {"exception": str(e)},
            )
            return False
        except Exception as e:
            logging.error("Unexpected exception.", {"exception": str(e)})
            return False

        logging.info(f"Chosen date {availability.date_time.date}.")

        try:
            rechercher = driver.find_element(by="id", value="rechercher")
            driver.execute_script("arguments[0].click();", rechercher)
        except NoSuchElementException as e:
            logging.error("Failed to find rechercher element.", {"exception": str(e)})
            return False
        except Exception as e:
            logging.error("Unexpected exception.", {"exception": str(e)})
            return False

        logging.info("Searched for available courts.")

        try:
            leaflets = driver.find_element(
                by=By.CLASS_NAME, value="leaflet-marker-pane"
            )
            leaflets = leaflets.find_elements(by=By.XPATH, value=".//*")

            # Elisabeth is leaflet 18
            driver.execute_script("arguments[0].click();", leaflets[18])
        except NoSuchElementException as e:
            logging.error("Failed to find leaflet element.", {"exception": str(e)})
            return False
        except Exception as e:
            logging.error("Unexpected exception.", {"exception": str(e)})
            return False

        logging.info("Clicked on the Elisabeth leaflet on the map.")

        try:
            link = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CLASS_NAME, "accessTennisMap"))
            )
        except Exception as e:
            logging.error(
                "Failed to find accessTennisMap element.", {"exception": str(e)}
            )
            return False

        link.send_keys("\n")

        times = driver.find_elements(by=By.CLASS_NAME, value="panel-title")

        found = False
        for t in times:
            if t.text == availability.date_time.time:
                t.click()
                found = True
                break

        if not found:
            logging.error(
                f"Failed to find time element. {availability} is not available.",
            )
            return False

        logging.info(f"Chosen time {availability.date_time.time}.")

        reserve_buttons = driver.find_elements(
            by=By.XPATH,
            value="//button[@class='btn btn-darkblue medium rollover rollover-grey buttonHasReservation']",
        )

        reserve_buttons += driver.find_elements(
            by=By.XPATH,
            value="//button[@class='btn btn-darkblue medium rollover rollover-grey buttonAllOk']",
        )

        if len(reserve_buttons) == 0:
            logging.error(
                f"Failed to find any reserve buttons. {availability} is not available.",
            )

            pid = os.getpid()
            self._save_screenshot(driver, f"data/{pid}.png")
            self._save_page_source(driver, f"data/{pid}.html")
            return False

        clicked = False
        court_id = None
        for button in reserve_buttons:
            button_court_id = button.get_attribute("courtid")
            button_date = button.get_attribute("datedeb")
            if (
                button_date == str(availability.date_time)
                and button_court_id == availability.court.id
            ):
                driver.execute_script("arguments[0].click();", button)
                clicked = True
                court_id = button_court_id
                break

        if not clicked:
            logging.error(
                f"Failed to click on the reserve button. {availability} is not available.",
            )
            return False

        logging.info(f"Clicked on the reserve button for court {court_id}.")

        inputs = driver.find_elements(
            by=By.XPATH, value="//input[@class='form-control required']"
        )

        if len(inputs) == 0:
            logging.error(
                f"Failed to find any inputs for player information. Account {user.username} already has a reservation.",
            )
            return False

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

        logging.info("Player information filled")

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
            logging.error(f"Carnet seems empty for user {self.username}.",)
            return False

        logging.info("Carnet has available hours")

        submit_button = driver.find_element(by=By.ID, value="submit")
        submit_button.click()

        logging.info(
            "Court booked",
            {
                "court_date": availability.date_time.date,
                "court_time": availability.date_time.time,
                "court_id": availability.court.id,
                "username": user.username,
            },
        )
        return True

    def _save_screenshot(self, driver: webdriver.Chrome, path: str) -> None:
        # Ref: https://stackoverflow.com/a/52572919/
        original_size = driver.get_window_size()
        required_width = driver.execute_script(
            "return document.body.parentNode.scrollWidth"
        )
        required_height = driver.execute_script(
            "return document.body.parentNode.scrollHeight"
        )
        driver.set_window_size(required_width, required_height)
        driver.find_element_by_tag_name("body").screenshot(path)  # avoids scrollbar
        driver.set_window_size(original_size["width"], original_size["height"])

    def _save_page_source(self, driver: webdriver.Chrome, path: str) -> None:
        with open(path, "w") as f:
            f.write(driver.page_source)
