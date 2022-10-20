""" Allows for more readable logging of key steps during execution """
import logging
import os
import platform
import time
from datetime import datetime
from inspect import getframeinfo, stack

from colorama import Fore, Style

from base.driver_setup import driver, get_arg


def log_new_date_time():
    """Gets a new date and time
    :return: The date time"""
    current_date_time = datetime.now()
    date_time = current_date_time.strftime("%d_%m_%Y %H_%M_%S")  # Get current date and format date time
    return date_time


class StepCounter:
    step_no = 0
    date_time = log_new_date_time()
    start_logging = False
    test_title = "UndefinedTestTitle"
    img_counter = 0
    record_step_images = False
    path_root = None

    def take_screenshot(self, pic_filename, fullpage=False):
        """Take a screenshot of the view port
        :param pic_filename: String to be used as the image filename without the file extension
        :param fullpage: If set to True then the entire screen will saved
        :return: void"""

        save_folder = get_arg("url").split("://")[1].replace("/", "").replace('.', '-')

        if not os.path.isdir(os.path.join(StepCounter.path_root, save_folder)):
            os.mkdir(os.path.join(StepCounter.path_root, save_folder))

        full_path = os.path.join(StepCounter.path_root, save_folder, pic_filename)

        if not fullpage:
            driver.save_screenshot(full_path + ".png")
        else:
            driver.get_full_page_screenshot_as_file(full_path + ".png")

    def start(self, test_title):
        """Initiates a new set of steps by calling reset and w
        :param test_title: Title of the test
        :return: void"""
        self.log_result("")
        StepCounter.test_title = test_title
        StepCounter.start_logging = True
        with open(os.path.join(StepCounter.path_root, f"steps_{self.date_time}.txt"), "a") as f_start:
            f_start.write(
                f"""

{datetime.now().strftime("%d/%m/%Y %H_%M_%S")}
Test: {test_title}
Steps:
"""
            )

    def count_step(self, text_out, sleep_secs, substep=False):
        if not StepCounter.start_logging:
            return
        StepCounter.img_counter += 1
        if self.record_step_images:
            self.take_screenshot(f"{StepCounter.test_title}-{str(StepCounter.img_counter).zfill(4)}")
        if substep:
            with open(os.path.join(StepCounter.path_root, f"steps_{self.date_time}.txt"), "a") as f_step:
                if sleep_secs != 0:
                    f_step.write(f"\t{text_out}; wait duration: {sleep_secs} second(s).\n")
                else:
                    f_step.write(f"\t{text_out}.\n")

        if not substep:
            StepCounter.step_no += 1

            with open(os.path.join(StepCounter.path_root, f"steps_{self.date_time}.txt"), "a") as f_step:
                if sleep_secs != 0:
                    f_step.write(f"{str(StepCounter.step_no).zfill(2)}) {text_out}; wait duration: {sleep_secs} second(s).\n")
                else:
                    f_step.write(f"{str(StepCounter.step_no).zfill(2)}) {text_out}.\n")

    def reset(self, expected_result="", actual_result="", test_name="", test_passed=False):
        def reset_steps():
            StepCounter.step_no = 0
            StepCounter.img_counter = 0

        if test_passed:
            with open(os.path.join(StepCounter.path_root, f"steps_{self.date_time}.txt"), "a") as f_pass:
                f_pass.write(f"PASS: {test_name}\n")
                reset_steps()
        else:
            with open(os.path.join(StepCounter.path_root, f"steps_{self.date_time}.txt"), "a") as f_fail:
                f_fail.write(f"FAIL: {self.test_title}:\n")
                f_fail.write(f"Expected Result:\n{expected_result}\n")
                f_fail.write(f"\nActual Result:\n{actual_result}\n")
                reset_steps()
                raise Exception(f"Expected result: {expected_result}\nActual result: {actual_result}")

    def log_result(self, text):
        if not StepCounter.start_logging:
            return
        with open(os.path.join(StepCounter.path_root, f"results_{self.date_time}.txt"), "a") as file:
            file.write(f"{text}\n")


def xlogging(set_debug_level, text_out, log_as_step="n", sleep_secs=0, frame_stack=1):
    """This allows a specific wait time to be passed when sending a message to the console
    :param log_as_step: default is 'n', use count_step='y' if log should also be counted as a step to be logged to steps file
    :param set_debug_level: 1:DEBUG, 2:INFO, 3:, WARNING, 4:ERROR, 5:CRITICAL
    :param text_out: Message to be printed to the console
    :param sleep_secs: How long to wait before continuing with the program
    :param frame_stack: Set to true if the file calling this function == xpath_tools.py
    :return: Void"""

    caller = getframeinfo(stack()[frame_stack][0])

    if platform.system() == "Windows":
        f_name = caller.filename.split("\\")[-1]
    else:
        f_name = caller.filename.split("/")[-1]

    if set_debug_level == 1:
        debug_level = logging.debug
        log_level = "Debug: "
        color = Fore.WHITE
    elif set_debug_level == 2:
        debug_level = logging.info
        log_level = "Info: "
        color = Fore.GREEN
    elif set_debug_level == 3:
        debug_level = logging.warning
        log_level = "Warn: "
        color = Fore.YELLOW
    elif set_debug_level == 4:
        debug_level = logging.error
        log_level = "Error: "
        color = Fore.LIGHTRED_EX
    elif set_debug_level == 5:
        debug_level = logging.critical
        log_level = "CRITICAL: "
        color = Fore.RED
    else:
        debug_level = 2
        log_level = ""
        color = Fore.WHITE

    if log_as_step == "n":
        if sleep_secs != 0:
            if get_arg("colors") == "y":
                debug_level(
                    f"{f_name:<20}:{caller.lineno:<3}:{color}{log_level} {text_out}; wait duration: {sleep_secs} second(s){Style.RESET_ALL}"
                )
            else:
                debug_level(f"{f_name:<20}:{caller.lineno:<3}:{log_level} {text_out}; wait duration: {sleep_secs} second(s)")
        else:
            if get_arg("colors") == "y":
                debug_level(f"{f_name:<20}:{caller.lineno:<3}:{color}{log_level} {text_out}{Style.RESET_ALL}")
            else:
                debug_level(f"{f_name:<20}:{caller.lineno:<3}:{log_level} {text_out}")
        time.sleep(sleep_secs)

    if log_as_step == "y":
        if sleep_secs != 0:
            if get_arg("colors") == "y":
                debug_level(
                    f"{f_name:<20}:{caller.lineno:<3}:{Fore.LIGHTBLUE_EX}{log_level} {text_out}; wait duration: {sleep_secs} second(s){Style.RESET_ALL}"
                )
            else:
                debug_level(f"{f_name:<20}:{caller.lineno:<3}:{log_level} {text_out}; wait duration: {sleep_secs} second(s)")
            StepCounter().count_step(f"{log_level}{text_out}", sleep_secs)
        else:
            if get_arg("colors") == "y":
                debug_level(f"{f_name:<20}:{caller.lineno:<3}:{Fore.LIGHTBLUE_EX}{log_level} {text_out}{Style.RESET_ALL}")
            else:
                debug_level(f"{f_name:<20}:{caller.lineno:<3}:{log_level} {text_out}")
            StepCounter().count_step(f"{log_level}{text_out}", sleep_secs)
        time.sleep(sleep_secs)
