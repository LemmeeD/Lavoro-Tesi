from pathlib import Path
from typing import List

import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from entities.FirefoxHeadlessWebDriver import FirefoxHeadlessWebDriver
from utils import file_utils, domain_name_utils


class TLDPageScraper:
    def __init__(self, headless_browser: FirefoxHeadlessWebDriver):
        self.headless_browser = headless_browser
        self.tld_list = list()

    def scrape_tld(self) -> List[str]:
        try:
            self.headless_browser.driver.get('https://www.iana.org/domains/root/db')
        except selenium.common.exceptions.WebDriverException:
            raise
        tld_table = WebDriverWait(self.headless_browser.driver, 10).until(
            ec.presence_of_element_located((By.XPATH, '//*[@id="tld-table"]'))
        )
        try:
            tbody = tld_table.find_element(By.TAG_NAME, "tbody")
        except selenium.common.exceptions.NoSuchElementException:
            raise
        try:
            trs = tbody.find_elements(By.TAG_NAME, "tr")
        except selenium.common.exceptions.NoSuchElementException:
            raise
        for i, tr in enumerate(trs):
            try:
                a = tr.find_element(By.TAG_NAME, "a")
                self.tld_list.append(domain_name_utils.insert_trailing_point(a.text[1:]))       # from '.it' to 'it.'
            except selenium.common.exceptions.NoSuchElementException:
                raise
        return self.tld_list

    def import_from_txt(self, filepath):
        try:
            f = open(filepath, "r")
            for line in f:
                # self.tld_list.append(domain_name_utils.insert_trailing_point(line[1:]))
                self.tld_list.append(line)
            f.close()
        except ValueError:
            raise
        except PermissionError:
            raise
        except FileNotFoundError:
            raise
        except OSError:
            raise

    @staticmethod
    def import_txt_from_input_folder(project_root_folder=Path.cwd()):
        try:
            result = file_utils.search_for_filename_in_subdirectory('input', 'tlds.txt', project_root_folder)
        except FileNotFoundError:
            raise
        file = result[0]
        tlds = list()
        try:
            f = open(str(file), "r")
            for line in f:
                # tlds.append(domain_name_utils.insert_trailing_point(line[1:]))
                tlds.append(line)
            f.close()
        except ValueError:
            raise
        except PermissionError:
            raise
        except FileNotFoundError:
            raise
        except OSError:
            raise
        return tlds

    def export_txt(self, filepath):
        try:
            with open(filepath, 'w') as f:  # 'w' or 'x'
                for tld in self.tld_list:
                    try:
                        f.write(f"{tld}\n")
                    except UnicodeEncodeError:
                        pass
                f.close()
        except PermissionError:
            raise
        except FileNotFoundError:
            raise
        except OSError:
            raise

    def close(self):
        self.headless_browser.close()