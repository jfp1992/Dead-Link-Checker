from colorama import Fore
from selenium.common.exceptions import ElementClickInterceptedException, MoveTargetOutOfBoundsException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from base.custom_logging import StepCounter, xlogging
from base.driver_setup import driver, get_arg


class Xpath:
    """Allows quick templating of basic Xpaths or the start of longer ones
    example: //tag[@attribute='attribute value']
    :param tag: Examples: div, a, li, ul, Span, OtherAnything
    :param att: Examples: class@, class(), text(), @anything
    :param val: Value of attribute (after the =)
    :return: f"//{tag}[{attribute}='{value}']" """

    def __init__(self, tag=None, att=None, val=None, rel=None, index=None):
        if not tag and not att and not val:
            raise ValueError("No arguments passed for tag, attribute and value")
        if att[0] != "@" and att != "text":
            att = "@" + att
        else:
            att = att + "()"

        self.tag = tag
        self.att = att
        self.val = val
        self.rel = rel
        if index is not None:
            self.index = str(index)
        else:
            self.index = index

    def xpath_type_logic(self, xstart, xchain):
        if self.index is None:
            if self.rel is None:
                return xstart
            else:
                return xchain
        else:
            if self.rel is None:
                return f"{xstart}[{self.index}]"
            else:
                return f"{xchain}[{self.index}]"

    def absolute(self):
        xstart = f"//{self.tag}[{self.att}='{self.val}']"
        xchain = f"/{self.rel}::{self.tag}[{self.att}='{self.val}']"
        return self.xpath_type_logic(xstart, xchain)

    def starts_with(self):
        xstart = f"//{self.tag}[starts-with({self.att}, '{self.val}')]"
        xchain = f"/{self.rel}::{self.tag}[starts-with({self.att}, '{self.val}')]"
        return self.xpath_type_logic(xstart, xchain)

    def ends_with(self):
        xstart = f"//{self.tag}[ends-with({self.att}, '{self.val}')]"
        xchain = f"/{self.rel}::{self.tag}[ends-with({self.att}, '{self.val}')]"
        return self.xpath_type_logic(xstart, xchain)

    def contains(self):
        xstart = f"//{self.tag}[contains({self.att}, '{self.val}')]"
        xchain = f"/{self.rel}::{self.tag}[contains({self.att}, '{self.val}')]"
        return self.xpath_type_logic(xstart, xchain)


class Element:
    ignored_xpaths = [
        "//html",
        Xpath("h1", "text", "502 Bad Gateway").absolute(),
        Xpath("h1", "text", "504 ERROR").absolute(),
        Xpath("h1", "class", "page-header").absolute() + Xpath("h1", "text", "Access denied", "self").absolute(),
        Xpath("body", "text", "The website encountered an unexpected error. Please try again later.").absolute(),
        Xpath("div", "class", "ajax-progress").starts_with(),
        Xpath("input", "id", "cookie-agree").absolute(),
        Xpath("div", "class", "progress__percentage").absolute(),
        Xpath("div", "class", "progress").absolute(),
    ]

    def __init__(self, xpath, wait_time=0):
        self.xpath = xpath
        self.wait_time = wait_time

        self.log_win_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) to locate a single element's xpath, with a value of: {self.xpath}"
        )
        self.log_xpath_as_substep_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) to locate a single element's xpath, with a value of: {self.xpath}"
        )

        self.log_win = f"Locating a single element's xpath with a value of: {self.xpath}"
        self.log_xpath_as_substep = f"Locating a single element's xpath with a value of: {self.xpath}"

    def step_log(self, text):
        if not self.xpath in Element.ignored_xpaths:
            xlogging(2, text + "\n", frame_stack=4)
            StepCounter().count_step(text, 0, substep=True)

    def log_xpath(self):
        if get_arg("colors") == "y":
            if self.wait_time != 0:
                self.step_log(f"{Fore.CYAN}{self.log_win_custom_wait}")
            else:
                self.step_log(f"{Fore.LIGHTMAGENTA_EX}{self.log_win}")
        else:
            if self.wait_time != 0:
                self.step_log(f"{self.log_win_custom_wait}")
            else:
                self.step_log(f"{self.log_win}")

    def presence(self):
        self.log_win_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) to locate a single element's xpath, with an xpath of: {self.xpath}"
        )
        self.log_xpath_as_substep_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) to locate a single element's xpath, with an xpath of: {self.xpath}"
        )

        self.log_win = f"Locating a single element, with a value of: {self.xpath}"
        self.log_xpath_as_substep = f"Locating a single element's, with an xpath of: {self.xpath}"

        self.log_xpath()

        if self.xpath not in Element.ignored_xpaths:
            try:
                WebDriverWait(driver, self.wait_time, poll_frequency=0.01).until(ec.presence_of_element_located((By.XPATH, self.xpath)))
            except TimeoutException as e:
                StepCounter().log_result(f"\t Unable to find element: {self.xpath}")
                raise e
            except ElementClickInterceptedException as e:
                StepCounter().log_result(f"\t Element covered: {self.xpath}")
                raise e
            except MoveTargetOutOfBoundsException as e:
                StepCounter().log_result(f"\t Element is outside of view port, consider using Scroller class, element: {self.xpath}")
                raise e
        return WebDriverWait(driver, self.wait_time, poll_frequency=0.01).until(ec.presence_of_element_located((By.XPATH, self.xpath)))

    def presence_multi(self):
        self.log_win_custom_wait = f"Waiting up to: {self.wait_time} second(s) to locate multiple elements, with an xpath of: {self.xpath}"
        self.log_xpath_as_substep_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) to locate locate multiple elements, with an xpath of: {self.xpath}"
        )

        self.log_win = f"Locating locate multiple elements, with an xpath of: {self.xpath}"
        self.log_xpath_as_substep = f"Locating locate multiple elements, with an xpath of: {self.xpath}"

        self.log_xpath()

        try:
            WebDriverWait(driver, self.wait_time, poll_frequency=0.01).until(ec.presence_of_all_elements_located((By.XPATH, self.xpath)))
            return WebDriverWait(driver, self.wait_time, poll_frequency=0.01).until(
                ec.presence_of_all_elements_located((By.XPATH, self.xpath))
            )
        except TimeoutException:
            if self.xpath not in Element.ignored_xpaths:
                xlogging(3, f"Cannot find element {self.xpath}", frame_stack=2)
            return []

    def invisibility(self):
        self.log_win_custom_wait = f"Waiting up to: {self.wait_time} second(s) for an element to disappear, with an xpath of: {self.xpath}"
        self.log_xpath_as_substep_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) for an element to disappear, with an xpath of: {self.xpath}"
        )

        self.log_win = f"Waiting for an element to disappear, with an xpath of: {self.xpath}"
        self.log_xpath_as_substep = f"Waiting for an element to disappear, with an xpath of: {self.xpath}"

        self.log_xpath()

        if self.xpath not in Element.ignored_xpaths:
            try:
                WebDriverWait(driver, self.wait_time, poll_frequency=0.01).until(ec.invisibility_of_element_located((By.XPATH, self.xpath)))
            except TimeoutException as e:
                StepCounter().log_result(f"\t Element still visible: {self.xpath}")
                raise e
        return WebDriverWait(driver, self.wait_time, poll_frequency=0.01).until(ec.invisibility_of_element_located((By.XPATH, self.xpath)))

    def clickable(self):
        self.log_win_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) for an element to be clickable, with an xpath of: {self.xpath}"
        )
        self.log_xpath_as_substep_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) for an element to be clickable, with an xpath of: {self.xpath}"
        )

        self.log_win = f"Waiting for an element to be clickable, with an xpath of: {self.xpath}"
        self.log_xpath_as_substep = f"Waiting for an element to be clickable, with an xpath of: {self.xpath}"

        self.log_xpath()

        if self.xpath not in Element.ignored_xpaths:
            try:
                WebDriverWait(driver, self.wait_time, poll_frequency=0.01).until(ec.element_to_be_clickable((By.XPATH, self.xpath)))
            except TimeoutException as e:
                StepCounter().log_result(f"\t Unable to find element: {self.xpath}")
                raise e
            except ElementClickInterceptedException as e:
                StepCounter().log_result(f"\t Element covered: {self.xpath}")
                raise e
            except MoveTargetOutOfBoundsException as e:
                StepCounter().log_result(f"\t Element is outside of view port, consider using Scroller class, element: {self.xpath}")
                raise e
        return WebDriverWait(driver, self.wait_time, poll_frequency=0.01).until(ec.element_to_be_clickable((By.XPATH, self.xpath)))

    def is_present(self):
        self.log_win_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) to check the presence of an element, with an xpath of: {self.xpath}"
        )
        self.log_xpath_as_substep_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) to check the presence of an element, with an xpath of: {self.xpath}"
        )

        self.log_win = f"Waiting to check the presence of an element, with an xpath of: {self.xpath}"
        self.log_xpath_as_substep = f"Waiting to check the presence of an element, with an xpath of: {self.xpath}"

        self.log_xpath()

        if self.wait_time == 0:
            if self.xpath not in Element.ignored_xpaths:
                xlogging(3, f"Up to wait time for {self.xpath} is 0", frame_stack=2)
        try:
            WebDriverWait(driver, self.wait_time, poll_frequency=0.01).until(ec.presence_of_element_located((By.XPATH, self.xpath)))
            if self.xpath not in Element.ignored_xpaths:
                xlogging(2, f"Element {self.xpath} is present.", "y", frame_stack=2)
            return True
        except TimeoutException:
            if self.xpath not in Element.ignored_xpaths:
                xlogging(2, f"Element {self.xpath} is not present.", "y", frame_stack=2)
            return False

    def is_visible(self):
        self.log_win_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) to check if an element is visible, with an xpath of: {self.xpath}"
        )
        self.log_xpath_as_substep_custom_wait = (
            f"Waiting up to: {self.wait_time} second(s) to check if an element is visible, with an xpath of: {self.xpath}"
        )

        self.log_win = f"Waiting to check the if an element is visible, with an xpath of: {self.xpath}"
        self.log_xpath_as_substep = f"Waiting to check if an element is visible, with an xpath of: {self.xpath}"

        self.log_xpath()

        if self.wait_time == 0.0:
            xlogging(3, f"Up to wait time for {self.xpath} is 0", frame_stack=2)
        try:
            WebDriverWait(driver, self.wait_time, poll_frequency=0.01).until(ec.invisibility_of_element_located((By.XPATH, self.xpath)))
            xlogging(2, f"Element {self.xpath} is not visible.", "y", frame_stack=2)
            return False
        except TimeoutException:
            xlogging(2, f"Element {self.xpath} is visible.", "y", frame_stack=2)
            return True
