from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from cryptography.fernet import Fernet
import logging
import time
import os
from getpass import getpass
import sys
import threading

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
            self.paused = False
            self.pause_event = threading.Event()
            self.pause_event.set()
        except Exception as e:
            logging.error(f"Failed to initialize the browser driver: {e}")
            sys.exit(1)

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
        try:
            logging.info(f"Navigating to {url}")
            self.driver.get(url)
        except Exception as e:
            logging.error(f"Failed to navigate to URL {url}: {e}")
            self.close()

    def fill_login_form(self, username, password):
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
        try:
            self.driver.execute_script("$('.btlogin').click();")
            logging.info("Login 'Entra' button clicked using jQuery.")
        except Exception as e:
            logging.error(f"Failed to click login button: {e}")
            self.close()

    def pause(self):
        """Mette in pausa il bot."""
        self.paused = True
        self.pause_event.clear()
        logging.info("Bot paused.")

    def resume(self):
        """Riprende l'esecuzione del bot."""
        self.paused = False
        self.pause_event.set()
        logging.info("Bot resumed.")

    def monitor_counter_and_click(self, counter_by, counter_value, link, s, target="1"):
        """Monitora il contatore e clicca il pulsante appena raggiunge il target."""
        end_time = time.time() + s
        cv = 0
        while time.time() < end_time or cv != 0:
            self.pause_event.wait()  # Aspetta se il bot è in pausa
            try:
                counter_element = self.driver.find_element(counter_by, counter_value)
                current_value = counter_element.text.strip()
                cv = current_value
                logging.info(f"Current counter value: {current_value}")

                if current_value == target:
                    logging.info("Target value reached; attempting to click the button.")
                    try:
                        button_xpath = "//section[@class='auction-action-bid hidden-xs']//a[contains(text(), 'PUNTA')]"
                        bid_button = self.driver.find_element(By.XPATH, button_xpath)
                        bid_button.click()
                        logging.info(f"Button clicked successfully at URL: {link}")
                    except Exception as e:
                        logging.warning("Bid button not found or failed to click. Retrying...")

                time.sleep(0.3)
            except Exception as e:
                logging.error(f"Failed to monitor counter: {e}")
                self.close()

        logging.info("Target value not reached within duration.")
        self.close()

    def close(self):
        logging.info("Closing the browser and exiting the program.")
        self.driver.quit()
        sys.exit(10)


# Esempio di utilizzo del bot con input dell'utente
if __name__ == "__main__":
    driver_path = "C:\\chromedriver-win64\\chromedriver.exe"
    bot = WebBot(driver_path)

    cached_username, cached_password = bot.load_cached_credentials()
    if cached_username and cached_password:
        username, password = cached_username, cached_password
    else:
        username = input("Enter Username: ")
        password = getpass("Enter Password: ")
        bot.cache_credentials(username, password)

    url = input("Insert URL: ")
    duration = int(input("How many seconds do you want to monitor the element? (e.g., 30): "))

    # Avvia thread di controllo pausa/ripresa
    def user_control():
        while True:
            cmd = input("Enter 'p' to pause, 'r' to resume: ").strip().lower()
            if cmd == 'p':
                bot.pause()
            elif cmd == 'r':
                bot.resume()

    control_thread = threading.Thread(target=user_control)
    control_thread.daemon = True
    control_thread.start()

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
        link=url,
        s=duration,
        target="0",
    )
