from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pyautogui
import time
import os


def init_driver(path="chromedriver.exe"):
    chrome_options = Options()

    chrome_options.add_argument("--user-data-dir=" + os.path.join(os.getcwd(), "selenium_temp_profile"))
    service = Service(path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    return driver


def login(driver):
    driver.get("https://monkeytype.com/")


    try:
        cookie_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "cookiePopupAccept"))
        )
        cookie_btn.click()
    except:
        print("No cookies popup found")


    try:
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.textButton[onclick*='openLogin']"))
        )
        login_btn.click()
    except:
        print("Login button not found")
        return

    user = pyautogui.prompt("Enter your username/email: ")
    pasw = pyautogui.password("Enter your password: ")


    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    pass_input = driver.find_element(By.NAME, "password")

    email_input.send_keys(user)
    pass_input.send_keys(pasw)

    driver.find_element(By.CSS_SELECTOR, "button.textButton").click()
    print("Logged in!")


def write_words(driver, delay=0.05):
    try:
        while True:
            active_word = driver.find_element(By.CSS_SELECTOR, ".word.active")
            letters = [l.text for l in active_word.find_elements(By.TAG_NAME, "letter")] + [" "]
            pyautogui.write(letters, interval=delay)
    except Exception:
        pass

def play_round(driver, delay):
    pyautogui.alert("Select mode & time, then press OK to start.")
    time.sleep(3)
    write_words(driver, delay)


def collect_results(driver):
    wpm = driver.find_element(By.CSS_SELECTOR, ".group.wpm .bottom").text
    acc = driver.find_element(By.CSS_SELECTOR, ".group.acc .bottom").text
    consis = driver.find_element(By.CSS_SELECTOR, ".group.consistency .bottom").text
    return wpm, acc, consis


def display_results(data):
    keys = list(data.keys())
    print(*keys, sep="\t")
    for i in range(len(data["wpm"])):
        print(*(data[key][i] for key in keys), sep="\t\t")
    print("-" * 40)


if __name__ == "__main__":
    driver = init_driver()
    data = {"wpm": [], "accu": [], "consis": [], "delay": []}

    try:
        login(driver)
        ans = "YES"
        while ans == "YES":
            delay = float(pyautogui.prompt("Enter the delay (seconds, 0 = instant)", default="0.1"))
            play_round(driver, delay)

            wpm, acc, consis = collect_results(driver)
            data["wpm"].append(wpm)
            data["accu"].append(acc)
            data["consis"].append(consis)
            data["delay"].append(delay)

            display_results(data)
            ans = pyautogui.confirm("Wanna type again?", buttons=["YES", "NO"])

    finally:
        driver.quit()



