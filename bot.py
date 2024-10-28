from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from cryptography.fernet import Fernet
import logging
import time
import os
from getpass import getpass
import sys

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_or_generate_key():
    """Carica la chiave di crittografia da un file o ne genera una nuova."""
    try:
        if not os.path.exists("secret.key"):
            key = Fernet.generate_key()
            with open("secret.key", "wb") as key_file:
                key_file.write(key)
            logging.info("New encryption key generated.")
            return key
        else:
            with open("secret.key", "rb") as key_file:
                logging.info("Encryption key loaded from file.")
                return key_file.read()
    except Exception as e:
        logging.error(f"Failed to load or create encryption key: {e}")
        sys.exit(1)


class WebBot:
    def __init__(self, driver_path):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        try:
            self.driver = webdriver.Chrome(service=Service(driver_path), options=options)
            logging.info("Browser driver initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize the browser driver: {e}")
            sys.exit(1)

        # Carica o genera una chiave di crittografia
        try:
            self.key = load_or_generate_key()
            self.cipher = Fernet(self.key)
        except Exception as e:
            logging.error(f"Failed to load or generate encryption key: {e}")
            sys.exit(1)

    def encrypt(self, text):
        return self.cipher.encrypt(text.encode()).decode()

    def decrypt(self, encrypted_text):
        return self.cipher.decrypt(encrypted_text.encode()).decode()

    def cache_credentials(self, username, password):
        try:
            with open("credentials.txt", "w") as f:
                f.write(f"{self.encrypt(username)}\n{self.encrypt(password)}")
            logging.info("Credentials cached successfully.")
        except Exception as e:
            logging.error(f"Failed to cache credentials: {e}")
            sys.exit(1)

    def load_cached_credentials(self):
        if os.path.exists("credentials.txt"):
            try:
                with open("credentials.txt", "r") as f:
                    lines = f.readlines()
                    if len(lines) == 2:
                        username = self.decrypt(lines[0].strip())
                        password = self.decrypt(lines[1].strip())
                        logging.info("Credentials loaded and decrypted successfully.")
                        return username, password
            except Exception as e:
                logging.error(f"Failed to load cached credentials: {e}")
                sys.exit(1)
        return None, None

    def go_to_url(self, url):
        """Naviga verso l'URL specificato."""
        try:
            logging.info(f"Navigating to {url}")
            self.driver.get(url)
        except Exception as e:
            logging.error(f"Failed to navigate to URL {url}: {e}")
            self.close()

    def fill_login_form(self, username, password):
        """Clicca il pulsante login_btn e inserisce username e password nei campi."""
        try:
            self.driver.execute_script("document.getElementById('login_btn').click();")
            time.sleep(2)
            logging.info("Initial login button clicked.")

            username_field = self.driver.find_element(By.ID, "field_email")
            username_field.send_keys(username)
            logging.info("Username entered.")

            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(password)
            logging.info("Password entered.")
        except Exception as e:
            logging.error(f"Failed to fill login form: {e}")
            self.close()

    def click_login_button(self):
        """Clicca il pulsante 'Entra' usando jQuery per inviare il modulo."""
        try:
            self.driver.execute_script("$('.btlogin').click();")
            logging.info("Login 'Entra' button clicked using jQuery.")
        except Exception as e:
            logging.error(f"Failed to click login button: {e}")
            self.close()

    def monitor_counter_and_click(self, counter_by, counter_value,link, s, target="1"):
        """Monitora il contatore e clicca il pulsante appena raggiunge il target."""
        end_time = time.time() + s
        # points = self.driver.find_element(By.ID, counter_value)
        cv = 0
        while time.time() < end_time or cv != 0:
            try:
                # Trova e legge il valore del contatore
                counter_element = self.driver.find_element(counter_by, counter_value)
                current_value = counter_element.text.strip()
                cv = current_value

                logging.info(f"Current counter value: {current_value}")

                # Quando il contatore raggiunge il target, tenta di cliccare il pulsante
                if current_value == target:
                    logging.info("Target value reached; attempting to click the button.")

                    # Usa XPath o CSS Selector
                    try:
                        button_xpath = "//section[@class='auction-action-bid hidden-xs']//a[contains(text(), 'PUNTA')]"
                        bid_button = self.driver.find_element(By.XPATH, button_xpath)
                        bid_button.click()
                        logging.info("Button clicked successfully via XPath.")
                        logging.info("You win at url:",link)
                    except Exception as e:
                        logging.warning("Bid button not found or failed to click. Retrying...")

                time.sleep(0.05)

            except Exception as e:
                logging.error(f"Failed to monitor counter: {e}")
                self.close()

        logging.info("Target value not reached within duration.")
        self.close()

        # Polling loop in Python per monitorare il tempo
        while time.time() < end_time:
            try:
                counter_element = self.driver.find_element(counter_by, counter_value)
                current_value = counter_element.text.strip()
                logging.info(f"Current counter value: {current_value}")

                if current_value == target:
                    logging.info("Target value reached; JavaScript is attempting to click the button repeatedly.")
                    time.sleep(0.1)  # Breve pausa per lasciare agire il JavaScript
            except Exception as e:
                logging.error(f"Failed to monitor counter: {e}")
                self.close()

            time.sleep(0.1)

        logging.info("Target value not reached within duration.")
        self.close()

    def close(self):
        """Chiudi il browser e termina il programma."""
        logging.info("Closing the browser and exiting the program.")
        self.driver.quit()
        sys.exit(10)


# Esempio di utilizzo del bot con input dell'utente
if __name__ == "__main__":
    driver_path = "C:\\chromedriver-win64\\chromedriver.exe"
    bot = WebBot(driver_path)

    # Carica le credenziali dalla cache o chiedile all'utente
    cached_username, cached_password = bot.load_cached_credentials()
    if cached_username and cached_password:
        username, password = cached_username, cached_password
    else:
        username = input("Enter Username: ")
        password = getpass("Enter Password: ")
        bot.cache_credentials(username, password)

    # Richiedi l'URL
    url = input("Insert URL: ")
    duration = int(input("How many seconds do you want to monitor the element? (e.g., 30): "))

    # Vai all'URL e avvia il processo di login e monitoraggio
    bot.go_to_url(url)
    time.sleep(5)

    bot.fill_login_form(username, password)
    time.sleep(2)
    bot.click_login_button()
    time.sleep(3)
    bot.monitor_counter_and_click(
        counter_by=By.CLASS_NAME,
        counter_value="text-countdown-progressbar",
        # button_selector=".bid-button.button-default.button-rounded.button-full.ripple-button.button-big-text.auction-btn-bid.button-mint-flat.bid-button-login.hidden-xs",
        link=url,
        s=duration,
        target="0",
    )

