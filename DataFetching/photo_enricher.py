# vibe coded CrapCode just to download all the links of images of mks
from utils.logger_config import get_logger
from typing import Dict, Optional
import re
import time
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
import requests
import json

logger = get_logger(__name__)


class PhotoEnricher:
    """
    Enriches MK data with photo URLs by scraping the Knesset website using Selenium.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            # Add project root to sys.path to allow absolute imports

        })
        self.driver = None
        self._setup_selenium()

    def _setup_selenium(self):
        """Setup Chrome WebDriver with appropriate options to avoid detection"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(
                '--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option(
                'useAutomationExtension', False)
            chrome_options.add_argument(
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # Try to use ChromeDriver automatically (will download if needed)
            self.driver = webdriver.Chrome(options=chrome_options)

            # Execute script to hide webdriver property
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info(
                "Chrome WebDriver initialized successfully with anti-detection measures")

        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            logger.info(
                "Please make sure Chrome is installed or install ChromeDriver manually")
            self.driver = None

    def __del__(self):
        """Cleanup WebDriver on destruction"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def get_site_id(self, mk_id: int) -> Optional[str]:
        """
        Get the site_id for an MK using the OData API.

        Args:
            mk_id: The KnessetMember ID

        Returns:
            The site_id if found, None otherwise
        """
        url = f"https://knesset.gov.il/OdataV4/ParliamentInfo/KNS_MkSiteCode?$filter=KnsID%20eq%20{mk_id}"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            data = response.json()
            if data.get('value') and len(data['value']) > 0:
                site_id = data['value'][0].get('SiteId')
                logger.debug(f"Found site_id {site_id} for MK {mk_id}")
                return site_id
            else:
                logger.warning(f"No site_id found for MK {mk_id}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching site_id for MK {mk_id}: {e}")
            return None
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing site_id response for MK {mk_id}: {e}")
            return None

    def scrape_photo_url(self, site_id: str) -> Optional[str]:
        """
        Scrape the photo URL from the MK's personal details page using Selenium.

        Args:
            site_id: The site ID for the MK

        Returns:
            The photo URL if found, None otherwise
        """
        if not self.driver:
            logger.error("WebDriver not available, cannot scrape photos")
            return None

        url = f"https://main.knesset.gov.il/mk/Apps/mk/mk-personal-details/{site_id}"

        try:
            logger.debug(f"Loading page: {url}")
            self.driver.get(url)

            # Wait for the page to load - wait for the main content to be present
            try:
                # Wait for Angular/JavaScript to load - look for specific content or wait longer
                WebDriverWait(self.driver, 20).until(
                    lambda driver: driver.execute_script(
                        "return document.readyState") == "complete"
                )
                logger.debug(
                    f"Document ready state is complete for site_id {site_id}")

                # Try to execute any pending JavaScript challenges
                try:
                    # Look for the winsocks function and try to execute it if it exists
                    self.driver.execute_script("""
                        if (typeof winsocks === 'function') {
                            winsocks();
                        }
                    """)
                    logger.debug(
                        f"Attempted to execute winsocks challenge for site_id {site_id}")
                except Exception as e:
                    logger.debug(
                        f"Could not execute winsocks challenge for site_id {site_id}: {e}")

                # Give much more time for JavaScript/Angular to render the content after challenge
                time.sleep(15)

                # Wait for actual content to appear - look for real content elements
                try:
                    WebDriverWait(self.driver, 15).until(
                        lambda driver: len(
                            driver.page_source) > 1000 or 'lobby-img' in driver.page_source
                    )
                    logger.debug(
                        f"Page content appears to have loaded for site_id {site_id}")
                except TimeoutException:
                    logger.debug(
                        f"Timeout waiting for full content, but proceeding anyway for site_id {site_id}")

            except TimeoutException:
                logger.warning(f"Page load timeout for site_id {site_id}")
                # Don't return None immediately, try to scrape anyway

            # Give one more moment for any lazy-loaded images
            time.sleep(3)

            # Method 1: Look for div with specific classes that contain background-image style
            try:
                img_divs = self.driver.find_elements(
                    By.CSS_SELECTOR, "div.lobby-img, div.lobby-mk-previmg")
                for div in img_divs:
                    style = div.get_attribute('style')
                    if style and 'background-image' in style:
                        # Extract URL from background-image: url("...")
                        match = re.search(
                            r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
                        if match:
                            photo_url = match.group(1)
                            # Check if it contains globaldocs/MK/ as specified
                            if 'globaldocs/MK/' in photo_url:
                                logger.info(
                                    f"Found photo URL for site_id {site_id}: {photo_url}")
                                return photo_url
            except Exception as e:
                logger.debug(f"Method 1 failed for site_id {site_id}: {e}")

            # Method 2: Look for any elements with background-image containing globaldocs/MK/
            try:
                all_elements = self.driver.find_elements(
                    By.XPATH, "//*[@style]")
                for element in all_elements:
                    style = element.get_attribute('style')
                    if style and 'background-image' in style and 'globaldocs/MK/' in style:
                        match = re.search(
                            r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
                        if match:
                            photo_url = match.group(1)
                            logger.info(
                                f"Found photo URL (method 2) for site_id {site_id}: {photo_url}")
                            return photo_url
            except Exception as e:
                logger.debug(f"Method 2 failed for site_id {site_id}: {e}")

            # Method 3: Look for img tags with src containing globaldocs/MK/
            try:
                img_elements = self.driver.find_elements(By.TAG_NAME, "img")
                for img in img_elements:
                    src = img.get_attribute('src')
                    if src and 'globaldocs/MK/' in src:
                        logger.info(
                            f"Found photo URL in img tag for site_id {site_id}: {src}")
                        return src
            except Exception as e:
                logger.debug(f"Method 3 failed for site_id {site_id}: {e}")

            # Method 4: Search page source for any URLs containing globaldocs/MK/
            try:
                page_source = self.driver.page_source
                logger.debug(
                    f"Page source length for site_id {site_id}: {len(page_source)} characters")

                # Log page title for debugging
                page_title = self.driver.title
                logger.debug(f"Page title for site_id {site_id}: {page_title}")

                globaldocs_matches = re.findall(
                    r'https?://[^"\'\s]+globaldocs/MK/[^"\'\s]+', page_source)

                if globaldocs_matches:
                    photo_url = globaldocs_matches[0]  # Take the first match
                    logger.info(
                        f"Found photo URL via page source search for site_id {site_id}: {photo_url}")
                    return photo_url

                # Also search for any references to globaldocs (even without full URL)
                if 'globaldocs' in page_source.lower():
                    logger.debug(
                        f"Found 'globaldocs' text in page for site_id {site_id}, but no complete URLs")
                    # Try to find partial matches
                    partial_matches = re.findall(
                        r'[^"\'\s]*globaldocs[^"\'\s]*', page_source, re.IGNORECASE)
                    for match in partial_matches[:3]:  # Log first 3 matches
                        logger.debug(
                            f"Partial globaldocs match for site_id {site_id}: {match}")
                else:
                    logger.debug(
                        f"No 'globaldocs' text found in page source for site_id {site_id}")

            except Exception as e:
                logger.debug(f"Method 4 failed for site_id {site_id}: {e}")

            # Debug: Save page content for manual inspection if needed
            if logger.isEnabledFor(10):  # DEBUG level
                try:
                    debug_filename = f"debug_page_{site_id}.html"
                    with open(debug_filename, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    logger.debug(
                        f"Debug: Saved page source to {debug_filename}")
                except Exception as e:
                    logger.debug(f"Failed to save debug page source: {e}")

            logger.warning(
                f"No photo URL found for site_id {site_id} after all search methods")
            return None

        except WebDriverException as e:
            logger.error(
                f"WebDriver error scraping photo for site_id {site_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error scraping photo for site_id {site_id}: {e}")
            return None

    def enrich_mk_with_photo(self, mk_id: int, mk_data: Dict) -> Dict:
        """
        Enrich a single MK's data with photo URL.

        Args:
            mk_id: The MK ID
            mk_data: The existing MK data dictionary

        Returns:
            The enriched MK data dictionary
        """
        # Check if photo URL already exists
        if mk_data.get('PhotoURL'):
            logger.debug(f"MK {mk_id} already has photo URL, skipping")
            return mk_data

        # Get site_id
        site_id = self.get_site_id(mk_id)
        if not site_id:
            mk_data['PhotoURL'] = None
            mk_data['PhotoStatus'] = 'no_site_id'
            return mk_data

        # Add delay to be respectful to the server (longer delay for Selenium)
        time.sleep(2)

        # Scrape photo URL
        photo_url = self.scrape_photo_url(site_id)
        mk_data['PhotoURL'] = photo_url
        mk_data['SiteId'] = site_id

        if photo_url:
            mk_data['PhotoStatus'] = 'found'
            logger.info(
                f"Successfully enriched MK {mk_id} ({mk_data.get('FirstName', '')} {mk_data.get('LastName', '')}) with photo")
        else:
            mk_data['PhotoStatus'] = 'not_found'
            logger.warning(
                f"Could not find photo for MK {mk_id} ({mk_data.get('FirstName', '')} {mk_data.get('LastName', '')})")

        return mk_data

    def enrich_mks_data_file(self, mks_data_path: str = "mks_data.json", force_refresh: bool = False) -> None:
        """
        Enrich the MKs data file with photo URLs.

        Args:
            mks_data_path: Path to the MKs data JSON file
            force_refresh: If True, re-fetch photos even if they already exist
        """
        logger.info("Starting photo enrichment process...")

        # Load existing MKs data
        try:
            with open(mks_data_path, 'r', encoding='utf-8') as f:
                mks_data = json.load(f)
        except FileNotFoundError:
            logger.error(f"MKs data file not found at {mks_data_path}")
            return
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing MKs data file: {e}")
            return

        total_mks = len(mks_data)
        processed = 0
        enriched = 0

        logger.info(f"Processing {total_mks} MKs for photo enrichment...")

        for mk_id_str, mk_data in mks_data.items():
            mk_id = int(mk_id_str)
            processed += 1

            logger.info(
                f"Processing MK {processed}/{total_mks}: {mk_data.get('FirstName', '')} {mk_data.get('LastName', '')} (ID: {mk_id})")

            # Skip if already has photo and not forcing refresh
            if not force_refresh and mk_data.get('PhotoURL'):
                logger.debug(f"MK {mk_id} already has photo, skipping")
                continue

            # Enrich with photo
            enriched_data = self.enrich_mk_with_photo(mk_id, mk_data.copy())
            mks_data[mk_id_str] = enriched_data

            if enriched_data.get('PhotoURL'):
                enriched += 1

            # Save progress periodically (every 10 MKs)
            if processed % 10 == 0:
                self._save_mks_data(mks_data, mks_data_path)
                logger.info(
                    f"Progress saved: {processed}/{total_mks} processed, {enriched} enriched with photos")

        # Final save
        self._save_mks_data(mks_data, mks_data_path)

        logger.info(
            f"Photo enrichment completed! Processed {processed} MKs, enriched {enriched} with photos")

    def _save_mks_data(self, mks_data: Dict, file_path: str) -> None:
        """Save the MKs data to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(mks_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving MKs data: {e}")


def enrich_photos(force_refresh: bool = False) -> None:
    """
    Convenience function to enrich MKs data with photos.

    Args:
        force_refresh: If True, re-fetch photos even if they already exist
    """
    enricher = PhotoEnricher()
    enricher.enrich_mks_data_file(force_refresh=force_refresh)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Enrich MKs data with photo URLs")
    parser.add_argument("--force-refresh", dest="force_refresh",
                        action=argparse.BooleanOptionalAction,
                        help="Re-fetch photos even if they already exist")

    args = parser.parse_args()
    enrich_photos(force_refresh=args.force_refresh)
