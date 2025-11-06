# monkeytype_bot_improved.py
# Requires: selenium, pyautogui (only for prompts), pandas (optional, for saving CSV)
# pip install selenium pyautogui pandas

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import pyautogui
import time
import os
import csv
import traceback

DEFAULT_DRIVER = "chromedriver.exe"
PROFILE_DIR = os.path.join(os.getcwd(), "selenium_temp_profile")
RESULTS_CSV = "monkeytype_results.csv"


def init_driver(path=DEFAULT_DRIVER, headless=False):
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    # avoid noise
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
    service = Service(path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    return driver


def accept_cookies(driver, timeout=8):
    try:
        cookie_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.ID, "cookiePopupAccept"))
        )
        cookie_btn.click()
    except Exception:
        # fine if it's not there
        pass


def open_login_modal(driver, timeout=8):
    try:
        login_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.textButton[onclick*='openLogin']"))
        )
        login_btn.click()
        return True
    except Exception:
        return False


def do_login(driver):
    driver.get("https://monkeytype.com/")
    accept_cookies(driver)

    if not open_login_modal(driver):
        print("Login button not found. Continue as guest or check selectors.")
        return

    # use GUI prompts for creds (keeps your flow). Could be replaced by environment vars.
    username = pyautogui.prompt("Enter username/email (cancel to skip login):")
    if not username:
        print("Skipping login.")
        return

    password = pyautogui.password("Enter password:")

    # Wait for inputs then fill
    try:
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        pass_input = driver.find_element(By.NAME, "password")
        email_input.clear()
        email_input.send_keys(username)
        pass_input.send_keys(password)
        # the login button in modal
        driver.find_element(By.CSS_SELECTOR, "button.textButton").click()
        # wait for either profile avatar or an element that indicates success
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".user .avatar, .userAvatar"))
        )
        print("Logged in.")
    except Exception:
        print("Login attempt failed (maybe creds were wrong or modal changed).")
        traceback.print_exc()


def focus_typing_area(driver):
    # clicking body / center to make typing target active
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.click()
        return True
    except Exception:
        return False


def get_active_word_text(driver):
    """
    Returns the text of the active word. The site uses <letter> tags (weird),
    so we collect text from children. If not found, returns None.
    """
    try:
        active = driver.find_element(By.CSS_SELECTOR, ".word.active")
        # letters often are spans or custom tags named 'letter'
        letters = active.find_elements(By.XPATH, ".//*")
        if not letters:
            return active.text or ""
        return "".join([l.text for l in letters])
    except Exception:
        return None


def is_round_finished(driver):
    # detect the results panel presence
    try:
        # When round ends, the results groups appear (wpm acc ...), use a short lookup
        groups = driver.find_elements(By.CSS_SELECTOR, ".group.wpm .bottom")
        return len(groups) > 0 and groups[0].text.strip() != ""
    except Exception:
        return False


def collect_results(driver, timeout=8):
    try:
        wpm = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".group.wpm .bottom"))
        ).text
        acc = driver.find_element(By.CSS_SELECTOR, ".group.acc .bottom").text
        consis = driver.find_element(By.CSS_SELECTOR, ".group.consistency .bottom").text
        # normalize to numbers when possible
        return wpm.strip(), acc.strip(), consis.strip()
    except Exception:
        return None, None, None


def type_round(driver, delay=0.05, max_idle=120):
    """
    Types the current round by repeatedly reading the active word and sending keystrokes
    using Selenium ActionChains (more reliable than pyautogui).
    Stops when results appear or when max_idle seconds elapsed (safety).
    """
    actions = ActionChains(driver)
    focus_typing_area(driver)
    start = time.time()
    last_action = time.time()

    while True:
        # safety timeout
        if time.time() - start > max_idle:
            print("Max idle reached, aborting round.")
            break

        if is_round_finished(driver):
            # round finished; break to collect results
            break

        word = get_active_word_text(driver)
        if word is None:
            # sometimes DOM hasn't loaded; small sleep and retry
            time.sleep(0.01)
            continue

        # sanity: if empty skip
        if word == "":
            time.sleep(0.01)
            continue

        # Type each character with ActionChains so it goes into the page's keyboard handler
        for ch in word + " ":  # include the required space after a word
            try:
                actions = ActionChains(driver)
                actions.send_keys(ch)
                actions.perform()
            except Exception:
                # fallback: use execute_script to dispatch keyboard event (rare)
                driver.execute_script(
                    """
                    const e = new KeyboardEvent('keydown', {key: arguments[0], bubbles: true});
                    document.dispatchEvent(e);
                    """,
                    ch,
                )
            last_action = time.time()
            # mimic human-ish typing
            if delay > 0:
                time.sleep(delay)

        # tiny sleep so DOM can update active word
        time.sleep(0.005)

    # wait a moment for results to render
    time.sleep(0.2)


def save_results_csv(row, path=RESULTS_CSV):
    header = ["timestamp", "wpm", "accuracy", "consistency", "delay"]
    exists = os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow(row)


def display_table(data):
    # simple console table
    print("WPM\tAccuracy\tConsistency\tDelay")
    for r in data:
        print(f"{r['wpm']}\t{r['acc']}\t{r['cons']}\t{r['delay']}")
    print("-" * 40)


def main():
    # config prompt
    chrome_path = pyautogui.prompt("Chromedriver path (leave blank for chromedriver.exe):", default=DEFAULT_DRIVER) or DEFAULT_DRIVER
    headless = pyautogui.confirm("Run headless?", buttons=["No", "Yes"]) == "Yes"

    driver = init_driver(path=chrome_path, headless=headless)
    results_history = []
    try:
        do_login(driver)
        # land on main page to start tests
        driver.get("https://monkeytype.com/")

        accept_cookies(driver)

        # main loop
        again = "YES"
        while again == "YES":
            # user selects mode/time on website manually, then clicks OK
            delay_str = pyautogui.prompt("Enter delay between keystrokes (seconds, 0 = instant). Example: 0.05", default="0.05")
            try:
                delay = float(delay_str)
            except Exception:
                delay = 0.05

            pyautogui.alert("Select mode & time on the page, then press OK here to start typing.")
            time.sleep(0.2)
            # ensure typing area is focused
            focus_typing_area(driver)

            # type until results appear
            type_round(driver, delay=delay)

            # collect results, retry a couple times if necessary
            wpm, acc, consis = collect_results(driver, timeout=5)
            if not wpm:
                # try a short poll
                for _ in range(5):
                    time.sleep(0.4)
                    wpm, acc, consis = collect_results(driver, timeout=1)
                    if wpm:
                        break

            # normalize default values
            wpm = wpm or "N/A"
            acc = acc or "N/A"
            consis = consis or "N/A"

            print(f"RESULTS: WPM={wpm} ACC={acc} CONS={consis} delay={delay}")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            results_history.append({"wpm": wpm, "acc": acc, "cons": consis, "delay": delay})
            save_results_csv([timestamp, wpm, acc, consis, delay])

            display_table(results_history)
            again = pyautogui.confirm("Wanna type again?", buttons=["YES", "NO"])

    except Exception:
        print("Unhandled error:")
        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
