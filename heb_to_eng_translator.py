import requests
from googletrans import Translator
import subprocess
import time


class HebToEngTranslator:

    def __init__(self, force_google=False):
        self.resolver = self._use_libre
        self.source_language = 'he'
        self.target_language = 'en'
        self.docker_process = None  # Store the Docker process
#        if force_google or not self._try_to_establish_docker_img():
 #           self.gTranslator = Translator()
  #          self.resolver = self._use_google

    def translate(self, text: str) -> str:
        return self.resolver(text)

    def _try_to_establish_docker_img(self):
        # Start Docker container
        # todo: pull img if not exists
        self.docker_process = subprocess.Popen(
            ["docker", "run", "--rm", "-p", "5000:5000",
                "libretranslate/libretranslate"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(5)
        return True

    def _use_libre(self, text: str):

        try:
            resp = requests.post("http://localhost:5000/translate", data={
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

    def cleanup(self):
        """Clean up Docker container on exit"""
        if self.docker_process:
            self.docker_process.terminate()
            self.docker_process = None

    def __del__(self):
        """Ensure cleanup when object is destroyed"""
        self.cleanup()
