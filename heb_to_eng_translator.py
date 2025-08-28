import requests
from googletrans import Translator

import subprocess

from logger_config import get_logger
import time

cmd = 'set-alias docker-start "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"'
LIBRE_PORT = 5000
logger = get_logger(__name__)


class HebToEngTranslator:

    def __init__(self, force_google=False):
        self.resolver = self._use_libre
        self.source_language = 'he'
        self.target_language = 'en'
        self.start_libre_()

    def translate(self, text: str) -> str:
        return self.resolver(text)

    def start_libre_(self):
        process = subprocess.Popen(["libretranslate", "--load-only", "en,he", "--port", str(LIBRE_PORT)],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   text=True,
                                   bufsize=1,)
        logger.info("Starting LibreTranslate service")

        max_retries = 30
        retry_delay = 1
        for i in range(max_retries):
            try:
                health_check = requests.get(
                    f"http://localhost:{LIBRE_PORT}/languages")
                if health_check.status_code == 200:
                    logger.info("LibreTranslate service is up")
                    break
            except requests.exceptions.ConnectionError:
                logger.debug(
                    f"Waiting for LibreTranslate service to be ready ({i+1}/{max_retries})")
                time.sleep(retry_delay)
        else:
            logger.warning(
                "LibreTranslate service may not be fully initialized after timeout")

    def _use_libre(self, text: str):

        try:
            resp = requests.post(f"http://localhost:{LIBRE_PORT}/translate", data={
                "q": text,
                "source": self.source_language,
                "target": self.target_language,
                "format": "text"
            }, timeout=1000)
            return resp.json()['translatedText']
        except Exception as e:
            print(f"Error translating with Libre Translate: {e}")
            return text

    def _use_google(self, text: str) -> str:
        try:
            result = self.gTranslator.translate(
                text, src=self.source_language, dest=self.target_language)
            return result.text
        except Exception as e:
            print(f"Error translating with Google Translate: {e}")
            return text


if __name__ == "__main__":
    t = HebToEngTranslator()
    eng = t.translate("אמא שלך חמודה מאוד, אני מכיר אותה מקרוב")
    print(eng)
