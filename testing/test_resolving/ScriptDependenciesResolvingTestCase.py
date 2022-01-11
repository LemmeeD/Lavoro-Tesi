import unittest
from pathlib import Path
import selenium
from entities.FirefoxHeadlessWebDriver import FirefoxHeadlessWebDriver
from entities.ScriptDependenciesResolver import ScriptDependenciesResolver


class ScriptDependenciesResolvingTestCase(unittest.TestCase):
    resolver = None
    headless_browser = None
    urls = None
    results = None

    @staticmethod
    def get_project_root_folder() -> Path:
        current = Path.cwd()
        while True:
            if current.name == 'LavoroTesi':
                return current
            else:
                current = current.parent

    @classmethod
    def setUpClass(cls) -> None:
        # PARAMETERS
        cls.urls = [
            'https://consent.youtube.com/ml?continue=https://www.youtube.com/feed/explore?gl%3DIT&gl=IT&hl=it&pc=yt&uxe=23983171&src=1',
            'https://www.google.com/doodles'
        ]
        # ELABORATION
        PRD = ScriptDependenciesResolvingTestCase.get_project_root_folder()
        cls.headless_browser = FirefoxHeadlessWebDriver(PRD)
        cls.resolver = ScriptDependenciesResolver(cls.headless_browser)
        cls.results = dict()
        for url in cls.urls:
            try:
                cls.results[url] = cls.resolver.search_script_application_dependencies(url)
            except selenium.common.exceptions.WebDriverException as e:
                print(f"!!! {str(e)} !!!")

    def test_1_debug_prints(self):
        for i, url in enumerate(self.results.keys()):
            print(f"url[{i+1}/{len(self.results.keys())}]: {url}")
            for j, script in enumerate(self.results[url]):
                print(f"--> script[{j+1}/{len(self.results[url])}].src={script.src}")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.headless_browser.close()


if __name__ == '__main__':
    unittest.main()
