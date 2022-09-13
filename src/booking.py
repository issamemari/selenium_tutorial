import logging

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from webdriver_manager.chrome import ChromeDriverManager

from typing import List


def reformat_date_and_time(date: str, time: str):
    date = date.split("/")
    date = f"{date[2]}/{date[1]}/{date[0]}"
    time = time[:-1] + ":00:00"
    return f"{date} {time}"


class Booker:
    def __init__(self, login_url: str, username: str, password: str, headless: bool):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

        self.driver.get(login_url)

        username_element = self.driver.find_element(by="id", value="username")
        password_element = self.driver.find_element(by="id", value="password")

        username_element.send_keys(username)
        password_element.send_keys(password)

        self.driver.find_element(by="name", value="Submit").click()

        self.username = username

    def book_court(
        self, search_url: str, court_ids: List[str], date: str, time: str,
    ) -> None:

        self.driver.execute_script(f"window.open('{search_url}', '_blank').focus()")

        if len(self.driver.window_handles) > 1:
            self.driver.close()

        self.driver.switch_to.window(self.driver.window_handles[0])

        logging.info("Opened search page.")

        try:
            when = self.driver.find_element(by="id", value="when")
            self.driver.execute_script("arguments[0].click();", when)
        except NoSuchElementException:
            logging.error("Failed to find when element.", {"exception": str(e)})
            return False
        except Exception as e:
            logging.error("Unexpected exception.", {"exception": str(e)})
            return False

        try:
            date_element = self.driver.find_element(
                by=By.XPATH, value=f"//div[@dateiso='{date}']"
            )
            self.driver.execute_script("arguments[0].click();", date_element)
        except NoSuchElementException as e:
            logging.error(
                "Failed to find date element. Date {date} is not available.",
                {"exception": str(e)},
            )
            return False
        except Exception as e:
            logging.error("Unexpected exception.", {"exception": str(e)})
            return False

        logging.info(f"Chosen date {date}.")

        try:
            rechercher = self.driver.find_element(by="id", value="rechercher")
            self.driver.execute_script("arguments[0].click();", rechercher)
        except NoSuchElementException:
            logging.error("Failed to find rechercher element.", {"exception": str(e)})
            return False
        except Exception as e:
            logging.error("Unexpected exception.", {"exception": str(e)})
            return False

        logging.info("Searched for available courts.")

        try:
            leaflets = self.driver.find_element(
                by=By.CLASS_NAME, value="leaflet-marker-pane"
            )
            leaflets = leaflets.find_elements(by=By.XPATH, value=".//*")

            # Elisabeth is leaflet 18
            self.driver.execute_script("arguments[0].click();", leaflets[18])
        except NoSuchElementException:
            logging.error("Failed to find leaflet element.", {"exception": str(e)})
            return False
        except Exception as e:
            logging.error("Unexpected exception.", {"exception": str(e)})
            return False

        logging.info("Clicked on the Elisabeth leaflet on the map.")

        try:
            link = WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located((By.CLASS_NAME, "accessTennisMap"))
            )
        except:
            logging.error(
                "Failed to find accessTennisMap element.", {"exception": str(e)}
            )
            return False

        link.send_keys("\n")

        times = self.driver.find_elements(by=By.CLASS_NAME, value="panel-title")

        found = False
        for t in times:
            if t.text == time:
                t.click()
                found = True
                break

        if not found:
            logging.error(
                f"Failed to find time element. Time {time} is not available for date {date}.",
            )
            return False

        logging.info(f"Chosen time {time}.")

        reserve_buttons = self.driver.find_elements(
            by=By.XPATH,
            value="//button[@class='btn btn-darkblue medium rollover rollover-grey buttonAllOk']",
        )

        if len(reserve_buttons) == 0:
            logging.error(
                f"Failed to find any reserve buttons. Time {time} is not available for date {date}.",
            )
            return False

        clicked = False
        court_id = None
        for button in reserve_buttons:
            button_court_id = button.get_attribute("courtid")
            button_date = button.get_attribute("datedeb")
            if (
                button_date == reformat_date_and_time(date, time)
                and button_court_id in court_ids
            ):
                self.driver.execute_script("arguments[0].click();", button)
                clicked = True
                court_id = button_court_id
                break

        if not clicked:
            logging.error(
                f"Failed to click on the reserve button. Time {time} is not available for date {date}.",
            )
            return False

        logging.info(f"Clicked on the reserve button for court {court_id}")

        inputs = self.driver.find_elements(
            by=By.XPATH, value="//input[@class='form-control required']"
        )

        if len(inputs) == 0:
            logging.error(
                f"Failed to find any inputs for player information. Account {self.username} already has a reservation.",
            )
            return False

        inputs[0].send_keys("Azarova")
        inputs[1].send_keys("Anna")

        ajouter_button = self.driver.find_element(
            by=By.XPATH,
            value="//button[@class='btn btn-darkblue small addPlayer rollover rollover-grey']",
        )
        ajouter_button.click()

        inputs = self.driver.find_elements(
            by=By.XPATH, value="//input[@class='form-control required']"
        )

        inputs[2].send_keys("Memari")
        inputs[3].send_keys("Issa")
        inputs[3].send_keys("\t")

        logging.info("Player information filled")

        submit_button = self.driver.find_element(by=By.ID, value="submitControle")
        submit_button.click()

        # find table tags
        tables = self.driver.find_elements(by=By.TAG_NAME, value="table")
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

        submit_button = self.driver.find_element(by=By.ID, value="submit")
        submit_button.click()

        logging.info(
            "Court booked",
            {
                "court_date": date,
                "court_time": time,
                "court_id": court_id,
                "username": self.username,
            },
        )
        return True
