import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
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
        EC.element_to_be_clickable((By.XPATH, "//div[@dateiso='21/06/2022']"))
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

    time.sleep(1000)

    driver.quit()


if __name__ == "__main__":
    main()
