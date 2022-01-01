from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import json
import sqlite3




class JobListing:
    def __init__(self, title, company, location, link, easy_apply, remote):
        self.title = title
        self.company = company
        self.location = location
        self.link = link
        self.easy_apply = easy_apply
        self.remote = remote
        self.description = ""

    def set_description(self, description):
        self.description = description

    def get_easy_apply_str(self):
        if self.easy_apply:
            return "Easy Apply"
        else:
            return "Not Easy Apply"

    def __str__(self):
        return (
            self.title
            + ", "
            + self.company
            + ", "
            + self.location
            + ", "
            + self.link
            + ", "
            + self.description
            + ", "
            + self.get_easy_apply_str()
            + ", "
            + self.remote
        )

def process_config():
    with open("config.json", "r") as jsonfile:
        config = json.load(jsonfile)
    return config

def launch_driver(url):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    return driver

def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)
    return None

def login(driver, username, password):
    driver.find_element(By.ID, "session_key").send_keys(
        username)  # fill username
    driver.find_element(By.ID, "session_password").send_keys(
        password)  # fill password
    driver.find_element(
        By.XPATH, '//*[@id="main-content"]/section[1]/div/div/form/button').click()  # sign in
    driver.get("https://www.linkedin.com/jobs/")  # go to jobs page

def search(driver, job, location):
    driver.set_window_size(1080, 920)
    driver.find_element(
        By.XPATH, '//*[contains(@id, "jobs-search-box-keyword-id")]').send_keys(job)  # fill job title
    driver.find_element(
        By.XPATH, '//*[contains(@id, "jobs-search-box-location-id")]').send_keys(location)  # fill location
    driver.find_element(
        By.XPATH, '//*[@id="global-nav-search"]/div/div[2]/button[1]').click()  # search
    time.sleep(2)
    return driver.current_url

def get_job_listings(driver):
    listings = []
    driver.set_window_size(360, 640)
    scrollHeight = 0

    for i in range(25):
        soup = BeautifulSoup(driver.page_source, "html.parser")
        listing = soup.find_all(
            "li", {"class": "jobs-search-results__list-item"})[i]

        # scroll
        scrollHeight += 135.969
        driver.execute_script("window.scrollTo(0, " + str(scrollHeight) + ");")
        time.sleep(1)

        title = listing.find(
            "a", {"class": "job-card-list__title"}).text.strip()
        company = listing.find(
            class_="job-card-container__company-name").text.strip()
        location = listing.find(
            "li", {"class": "job-card-container__metadata-item"}).text.strip()
        link = listing.find(
            "a", {"class": "job-card-list__title"})["href"].strip()
        try:
            _easy_apply = listing.find(
                "li", {"class": "job-card-container__apply-method"}).text.strip()
            easy_apply = ("Easy Apply" in _easy_apply)
        except:
            easy_apply = False
        try:
            _remote = listing.find(
                class_="job-card-container__metadata-item--workplace-type").text.strip()
            remote = "Remote" if ("Remote" in _remote) else "Not Remote"
        except:
            remote = "Not Remote"
        listings.append(JobListing(
            title, company, location, link, easy_apply, remote))

    return listings

def apply(listing, driver, db, connection):
    driver.get("https://www.linkedin.com" + listing.link)
    time.sleep(2)
    driver.set_window_size(1080, 920)
    try:
        driver.find_element(By.CLASS_NAME, "jobs-apply-button").click()
    except NoSuchElementException:
        driver.back()
        return

    while True:
        try:
            driver.find_element(
                By.XPATH, "//button[@aria-label='Continue to next step']").click()
        except:
            break
    
    try:
        driver.find_element(
            By.XPATH, "//button[@aria-label='Review your application']").click()
        time.sleep(1)
    except Exception as e:
        print(e)

    try:
        driver.find_element(
            By.XPATH, "//button[@aria-label='Submit application']").click()
        
        db.execute("INSERT INTO listings (title, company, location, link, description, easy_apply, remote) VALUES (?, ?, ?, ?, ?, ?, ?)", (
            listing.title, listing.company, listing.location, listing.link, listing.description, listing.easy_apply, listing.remote))
        connection.commit()
        time.sleep(1)
    except Exception as e:
        print(e)


def next_page(driver, i, search_url):
    driver.set_window_size(360, 640)
    url = search_url + "&start=" + str(i*25)
    driver.get(url)
    


if __name__ == "__main__":

    driver = launch_driver("https://www.linkedin.com/")
    config = process_config()
    username = config["username"]
    password = config["password"]
    job_titles = config["job_titles"]
    locations = config["locations"]
    connection = create_connection("jobs.db")
    db = connection.cursor()
    db.execute("CREATE TABLE IF NOT EXISTS listings (id INTEGER PRIMARY KEY, title TEXT, company TEXT, location TEXT, link TEXT, description TEXT, easy_apply TEXT, remote TEXT)")
    connection.commit()
    pages = 40
    

    login(driver, username, password)

    for job in job_titles:
        for location in locations:
            search_url = search(driver, job, location)
            try:
                for i in range(1, pages + 1, 1):
                    listings = get_job_listings(driver)
                    listings = [x for x in listings if x.easy_apply]

                    for listing in listings:
                        apply(listing, driver, db, connection)

                    next_page(driver, i, search_url)
            except Exception as e:
                print(e)
        break
