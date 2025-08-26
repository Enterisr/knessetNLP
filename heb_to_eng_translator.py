import requests
from googletrans import Translator
import subprocess
import time
import docker
from docker import errors as docker_errors

from logger_config import get_logger

cmd = 'set-alias docker-start "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"'
LIBRE_DOCKER_PORT = 5000
logger = get_logger(__name__)


class HebToEngTranslator:

    def __init__(self, force_google=False):
        self.resolver = self._use_libre
        self.source_language = 'he'
        self.target_language = 'en'
        self._try_to_establish_docker_img()

    def translate(self, text: str) -> str:
        return self.resolver(text)

    def start_libre(self, client):

        image_name = "libretranslate/libretranslate:latest"

        try:
            image = client.images.get(image_name)
            logger.info(f"libretranslate docker image found: {image.tags}")
        except Exception:
            logger.info(
                "LibreTranslate image not found, pulling from Docker Hub...")
            try:
                # Pull the image
                image = client.images.pull(
                    "libretranslate/libretranslate", tag="latest")
                logger.info(
                    f"Successfully pulled LibreTranslate image: {image.tags}")
            except docker_errors.APIError as e:
                logger.error(f"Failed to pull LibreTranslate image: {e}")
                # Fall back to Google Translate if image pull fails
                self.resolver = self._use_google
                self.gTranslator = Translator()
                logger.warning("Falling back to Google Translate")

    def _start_docker_engine(self):
        try:
            # Try to check if Docker is running first
            client = docker.from_env()

            client.ping()  # Will raise an exception if Docker is not running
            print("Docker engine is already running")
            self.docker_process = None
            self.start_libre(client)
        except Exception:
            print("Starting Docker engine...")
            try:
                # lets assume its a win macchine
                self.docker_process = subprocess.Popen(
                    ["C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                # Wait for Docker to start
                time.sleep(10)
                print("Docker engine started")
            except Exception as e:
                print(f"Failed to start Docker engine: {e}")
                self.docker_process = None

    def _try_to_establish_docker_img(self):
        self._start_docker_engine()
        client = docker.from_env()
        # Check if container is already running
        try:
            existing_containers = client.containers.list(
                filters={"ancestor": "libretranslate/libretranslate:latest"})
            if existing_containers:
                logger.info(
                    f"LibreTranslate container already running: {existing_containers[0].id}")
            else:
                logger.info("Starting LibreTranslate container...")
                client.containers.run(
                    "libretranslate/libretranslate:latest",
                    ports={'5000/tcp': LIBRE_DOCKER_PORT},
                    detach=True)
                logger.info("LibreTranslate container started")
        except Exception as e:
            logger.error(f"Error managing LibreTranslate container: {e}")
            self.resolver = self._use_google
            self.gTranslator = Translator()
            logger.warning("Falling back to Google Translate")
        return True

    def _use_libre(self, text: str):

        try:
            resp = requests.post(f"http://localhost:{LIBRE_DOCKER_PORT}/translate", data={
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


if __name__ == "__main__":
    t = HebToEngTranslator()
    eng = t.translate("אמא שלך חמודה")
    print(eng)
