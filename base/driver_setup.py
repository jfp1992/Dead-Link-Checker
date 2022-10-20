import platform
import sys

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service

from drivers import relpath


def get_arg(key):
    for i in sys.argv:
        if i.split(":", maxsplit=1)[0] == key:
            return i.split(":", maxsplit=1)[1]
    return None


if get_arg("browser") is None or (get_arg("browser") != "Firefox" and get_arg("browser") != "Chrome"):
    raise Exception("'browser' argument is missing or incorrect, please pass 'browser:Firefox' or 'browser:Chrome'")

if get_arg("url") is None:
    raise Exception("'url' argument is missing. Example: 'url:https://www.google.com'")


class DriverSetup(object):
    _instance = None
    driver = None
    options = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DriverSetup, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        if get_arg("browser") == "Firefox" or get_arg("browser") == "Chrome":
            self.driver = getattr(webdriver, get_arg("browser"))(
                options=options, service=Service(relpath.get_full_driver_path(get_arg("browser"), platform.system()))
            )
        else:
            raise SystemExit("Argument required in position 2: browser:'Chrome' or 'Firefox'")

    def get_driver(self):
        return self.driver

    def set_driver(self, new_driver):
        self.driver = new_driver


if get_arg("browser") == "Firefox":
    from selenium.webdriver.firefox.options import Options
elif get_arg("browser") == "Chrome":
    from selenium.webdriver.chrome.options import Options

options = Options()

if get_arg("headless") == "n":
    options.headless = False
else:
    options.headless = True

if get_arg("browser") == "Chrome":
    options.add_argument("--window-size=1920,1080")

if get_arg("browser") == "Firefox":
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")

driver = DriverSetup().get_driver()
if not options.headless:
    driver.maximize_window()

if get_arg("user") and get_arg("pass") is not None:
    url = get_arg("url")
    split_url = url.split("://")
    auth_url = f"{split_url[0]}{'://'}{get_arg('user')}:{get_arg('pass')}@{split_url[1]}"
    driver.get(auth_url)


def interceptor(request):
    if request.path.endswith((".png", ".jpg", ".gif", ".webp", ".svg", ".jpeg")):
        request.abort()


driver.scopes = f".*{get_arg('url').split('://')[1].replace('/', '')}.*"

if get_arg("quick") == "y":
    driver.request_interceptor = interceptor
