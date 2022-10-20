import os


def get_full_driver_path(driver, operating_sys):
    driver_choice = driver
    os_choice = operating_sys

    if os_choice == 'Windows':
        if driver_choice == 'Chrome':
            return os.path.join(os.path.dirname(__file__), 'chromedriver.exe')
        if driver_choice == 'Firefox':
            return os.path.join(os.path.dirname(__file__), 'geckodriver.exe')
        if driver_choice == 'Edge':
            return os.path.join(os.path.dirname(__file__), 'msedgedriver.exe')

    elif os_choice == 'Linux':
        if driver_choice == 'Chrome':
            return os.path.join(os.path.dirname(__file__), 'chromedriver_lin')
        if driver_choice == 'Firefox':
            return os.path.join(os.path.dirname(__file__), 'geckodriver_lin')
        if driver_choice == 'Edge':
            return os.path.join(os.path.dirname(__file__), 'msedgedriver_lin')

    elif os_choice == 'Darwin':
        if driver_choice == 'Chrome':
            return os.path.join(os.path.dirname(__file__), 'chromedriver_mac')
        if driver_choice == 'Firefox':
            return os.path.join(os.path.dirname(__file__), 'geckodriver_mac')
        if driver_choice == 'Edge':
            return os.path.join(os.path.dirname(__file__), 'msedgedriver_mac')

    else:
        raise SystemExit("Invalid OS, please use 'Windows', 'Linux' or 'Darwin'(MACos)")
