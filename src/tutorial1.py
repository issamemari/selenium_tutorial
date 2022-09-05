import time
import argparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# courts 6, 7, 8, and 9 respectively
COURT_IDS = {
    "Covered": ["1111", "1112" , "1113", "1114"]
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--date", type=str, help="format: 01/01/2022", required=True)
    parser.add_argument("--time", type=str, help="format: 08h", required=True)
    args = parser.parse_args()

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(
        "https://v70-auth.paris.fr/auth/realms/paris/protocol/openid-connect/auth?client_id=moncompte&response_type=code&redirect_uri=https%3A%2F%2Fmoncompte.paris.fr%2Fmoncompte%2Fservlet%2Fplugins%2Foauth2%2Fcallback%3Fdata_client%3DauthData&scope=openid&state=88c23b0ff5a4&nonce=fc1ecde3094c"
    )

    username = driver.find_element(by="id", value="username")
    password = driver.find_element(by="id", value="password")

    username.send_keys("issa.memari@gmail.com")
    password.send_keys("P7a5bpkxAHTgGCE")

    driver.find_element(by="name", value="Submit").click()

    driver.execute_script(
        "window.open('https://tennis.paris.fr/tennis/jsp/site/Portal.jsp?page=recherche&view=recherche_creneau#!', 'new_window')"
    )

    driver.switch_to.window(driver.window_handles[1])

    when = driver.find_element(by="id", value="when")
    when.click()

    date = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, f"//div[@dateiso='{args.date}']"))
    )
    date.click()

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
        if t.text == args.time:
            t.click()
            found = True
            break

    if not found:
        print(f"Time {args.time} is not available")
        return

    # find buttons by XPATH
    reserve_buttons = driver.find_elements(
        by=By.XPATH, value="//button[@class='btn btn-darkblue medium rollover rollover-grey buttonAllOk']"
    )
    reserve_buttons = [b for b in reserve_buttons if b.is_displayed()]

    for button in reserve_buttons:
        if button.get_attribute("courtid") in COURT_IDS["Covered"]:
            driver.execute_script("arguments[0].click();", button)
            break

    # find input by XPATH
    inputs = driver.find_elements(
        by=By.XPATH, value="//input[@class='form-control required']"
    )

    inputs[0].send_keys("Azarova")
    inputs[1].send_keys("Anna")

    ajouter_button = driver.find_element(
        by=By.XPATH, value="//button[@class='btn btn-darkblue small addPlayer rollover rollover-grey']"
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

    import code
    code.interact(local=locals())

    time.sleep(1000)

    driver.quit()


if __name__ == "__main__":
    main()
