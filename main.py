import logging
import os

from base.custom_logging import StepCounter

selenium_logger = logging.getLogger("seleniumwire")
selenium_logger.setLevel(logging.ERROR)

logging.basicConfig(level=logging.INFO, format="%(levelname)-.4s:%(asctime)s:%(message)s")

from base.driver_setup import get_arg
from scraper import Scraper

path_root = os.path.dirname(__file__)
StepCounter.path_root = path_root

base_url = get_arg("url")

image_save_folder = get_arg("url").split("://")[1].replace("/", "").replace('.', '-')

for http_response, broken_url, referrer in Scraper(base_url).crawl():
    if http_response is not None:
        print(
            f"""
Response: {http_response}
At:       {broken_url}
Referer:  {referrer}
image:    {path_root}\\{image_save_folder}__error_pages\\{broken_url.replace(get_arg('url'), '').replace('/', '_').replace('.', '-')}.png
"""
        )
