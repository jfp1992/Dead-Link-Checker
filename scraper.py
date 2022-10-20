import os
import time
import shutil

from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from base.custom_logging import StepCounter, xlogging
from base.driver_setup import driver, get_arg

from urllib.parse import urlparse, urljoin

import colorama

from base.record_time import RecordTime
from base.xpath_tools import Element

colorama.init()


GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW


class Scraper:
    def __init__(self, url):
        """
        :param url: # url to be scraped
        :type url: string
        """
        self.url = url  # url to start the scraping from

        self.cookie_policy_dismissed = False  # if the click action is successful, then this is set to True
        self.disclaimer_accepted = False  # if the click action is successful, then this is set to True

        self.internal_urls = set()  # list of unique urls of the same domain as the url to be scraped
        self.external_urls = set()  # list of unique urls of urls that are not part of the domain of the url to be scraped
        self.visited_urls = set()  # list of unique urls of the same domain as the url to be scraped that has already been visited

        self.hrefs = set()  # TODO: Make this a list and figure out a way to flag duplicates from the same page in a useful manner
        self.depth = 0  # Tracks how deep the scraper is in the tree
        self.base_url = True  # A flag indicating whether the current url being scraped is the base url from the arguments

        self.check_url = None  # Current url being scraped
        self.parent_url = None  # Referrer to current url being scraped

        if get_arg("ignore") is not None:
            self.ignore_partals = get_arg("ignore").split("|")  # list of url fragments that will be ignored when gathering hrefs
        else:
            self.ignore_partals = None

        self.processing_links = RecordTime("Processing links and images")  # Start and stop timer, used for limit rating
        self.broken_links_info = []  # list of lists containing response code, url being scraped and their referrer

    def is_valid(self, href):
        """Checks whether `url` is a valid URL."""
        parsed = urlparse(href)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def rate_limiter(self):
        """If a rate limit is set then wait up to that duration before continuing with the next request"""
        if not get_arg("rate"):
            return
        while self.processing_links.stop()[0] < int(get_arg("rate")):
            time.sleep(0.1)

    def go_to_url(self):
        """ Error handling for going to a page """
        neterror = True
        while neterror:
            try:
                if not self.base_url:
                    self.rate_limiter()
                driver.get(self.check_url)
                self.processing_links.start()  # Start timer
                neterror = False
            except TimeoutException:
                xlogging(4, f"UNABLE TO VISIT: {self.check_url} FROM: {self.parent_url}")
                self.broken_links_info.append([None, self.check_url, self.parent_url])
                return
            except WebDriverException:
                xlogging(4, "Page errored, waiting 30 seconds before trying again")
                time.sleep(30)

    def visited(self):
        """ Returns true if the currently scraped url is in the visited urls """
        if self.check_url in self.visited_urls:
            return True
        if "mailto:" in self.check_url:
            return True

    def dismiss_cookie_policy(self):
        """ Clicks an element using the xpath provided in the run time argument for cookie
        if the argument is populated and element is not already clicked """
        if not self.cookie_policy_dismissed and get_arg("cookie"):
            try:
                time.sleep(5)
                Element(get_arg("cookie"), 5).clickable().click()
                self.cookie_policy_dismissed = True
            except TimeoutException:
                xlogging(2, "Cannot find cookie policy, continuing")

    def accept_disclaimer(self):
        """ Clicks an element using the xpath provided in the run time argument for disclaimer
         if the argument is populated and element is not already clicked """
        if not self.disclaimer_accepted and get_arg("disclaimer"):
            try:
                Element(get_arg("disclaimer")).presence().click()
                self.disclaimer_accepted = True
            except TimeoutException:
                xlogging(2, "Cannot find disclaimer, continuing")

    def move_screenshot(self):
        """ Moved a screenshot from the domains folder to another based on the domain specifying error """
        save_folder = get_arg("url").split("://")[1].replace("/", "").replace('.', '-')
        filename = f"{self.check_url.replace(get_arg('url'), '').replace('/', '_').replace('.', '-')}.png"

        if not os.path.isdir(os.path.join(StepCounter.path_root, save_folder + "__error_pages")):
            os.mkdir(os.path.join(StepCounter.path_root, save_folder + "__error_pages"))

        shutil.move(
            os.path.join(StepCounter.path_root, save_folder, filename),
            os.path.join(StepCounter.path_root, save_folder + "__error_pages", filename),
        )

    def remove_image(self):
        """ Deleted an image from the domains folder """
        if not self.base_url:
            image_save_folder = get_arg("url").split("://")[1].replace("/", "").replace('.', '-')
            try:
                os.chmod(
                    f"{StepCounter.path_root}\\{image_save_folder}\\{self.check_url.replace(get_arg('url'), '').replace('/', '_').replace('.', '-')}.png", 0o777
                )
                os.remove(
                    f"{StepCounter.path_root}\\{image_save_folder}\\{self.check_url.replace(get_arg('url'), '').replace('/', '_').replace('.', '-')}.png"
                )
            except FileNotFoundError:
                xlogging(
                    4,
                    f"Unable to remove: {StepCounter.path_root}\\{image_save_folder}\\{self.check_url.replace(get_arg('url'), '').replace('/', '_').replace('.', '-')}.png",
                )

    def bad_page_response(self):
        """ Checks for 4## or 5## HTTP response codes """
        response_codes = driver.iter_requests()
        for response in response_codes:
            if str(response) == self.check_url:
                if str(response.response)[0] == "4" or str(response.response)[0] == "5":
                    xlogging(2, f"Response '{response.response}' for url:{self.check_url} from referer: {self.parent_url}")
                    self.broken_links_info.append([response.response, self.check_url, self.parent_url])
                    self.move_screenshot()
                    return True
                else:
                    self.remove_image()
                    return False

    def custom_ignore(self, href):
        """ Checks if any of the fragments provided in the runtime argument 'ignore' are in the href
        :param href: URL path to parse
        :type href: String
        :return: True/False
        :rtype: Bool
        """
        if not self.ignore_partals:
            return False
        for part in self.ignore_partals:
            if part in href:
                return True
        return False

    def get_all_website_links(self, url, parent_url):
        """ Returns all URLs that is found on `url` in which it belongs to the same website """
        self.check_url = url
        self.parent_url = parent_url
        urls = set()
        domain_name = urlparse(self.url).netloc

        if self.visited():
            return

        self.go_to_url()  # Go to url and handle network errors where possible
        self.visited_urls.add(self.check_url)

        if get_arg("url") not in driver.current_url:
            return

        if not self.base_url:
            if self.bad_page_response():
                return

        self.dismiss_cookie_policy()
        self.accept_disclaimer()

        if get_arg("maxdepth"):
            if self.depth == int(get_arg("maxdepth")):
                return

        try:
            hrefs = WebDriverWait(driver, 0, poll_frequency=0).until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href]")))
        except TimeoutException:
            xlogging(3, f"no a tags with href found at {self.check_url}")
            return

        for href in hrefs:
            try:
                href_element = href
                href = href.get_attribute("href")
            except StaleElementReferenceException:
                continue
            if href == "" or href is None:
                continue

            if href in self.hrefs:
                continue

            self.hrefs.add(href)

            if self.custom_ignore(href):
                continue

            href = urljoin(url, href)
            parsed_href = urlparse(href)
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path

            if href in self.visited_urls:
                continue
            if href in self.external_urls:
                continue

            if not self.is_valid(href):
                continue

            if href[-4] == ".":
                continue

            if href[-5] == ".":
                continue

            if domain_name not in href:
                xlogging(2, f"{GRAY}[!] External link: {href}{RESET}")
                self.external_urls.add(href)
                continue

            xlogging(2, f"{GREEN}[*] Internal link: {href}{RESET}")
            xlogging(2, f"Location in referrer: {href_element.location}")

            driver.execute_script("arguments[0].style.border='3px solid red'", href_element)
            StepCounter().take_screenshot(href.replace(get_arg("url"), "").replace("/", "_").replace('.', '-'), True)
            driver.execute_script("arguments[0].style.border='0px solid red'", href_element)

            urls.add(href)
            self.internal_urls.add(href)

        self.base_url = False

        return urls

    def _crawl(self, url, parent_url):
        """Loops through the returned list of urls which are each looped through to get a returned list of urls for each
        which are each looped through to get a returned list of urls for each
        which are each looped through to get a returned list of urls for each recursively."""

        xlogging(2, f"{YELLOW}[*] Crawling at depth {str(self.depth).ljust(3)}| {url}{RESET}")
        links = self.get_all_website_links(url, parent_url)  # Get links (after filtering) from current url

        if links is None:  # Leave
            self.depth -= 1
            return

        for link in links:
            if get_arg("maxdepth"):
                if self.depth == int(get_arg("maxdepth")):  # Leave
                    self.depth -= 1
                    return

            self.depth += 1
            self._crawl(link, url)  # Go deeper

        self.depth -= 1  # Leave

    def crawl(self):
        """Triggers the crawler to start gathering broken links"""
        self._crawl(self.url, None)
        return self.broken_links_info
