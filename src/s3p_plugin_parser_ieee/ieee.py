import dateparser
import pytz
import datetime
import time

from s3p_sdk.exceptions.parser import S3PPluginParserOutOfRestrictionException, S3PPluginParserFinish
from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument, S3PPlugin, S3PPluginRestrictions
from s3p_sdk.types.plugin_restrictions import FROM_DATE
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class IEEE(S3PParserBase):
    """
    A Parser payload that uses S3P Parser base class.
    """

    def __init__(self, refer: S3PRefer, plugin: S3PPlugin, restrictions: S3PPluginRestrictions, web_driver: WebDriver, url: str = None, categories: tuple | list = None):
        super().__init__(refer, plugin, restrictions)

        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self._driver = web_driver
        self._wait = WebDriverWait(self._driver, timeout=20)
        self.URL = url
        self.CATEGORIES = categories
        self.UTC = pytz.utc

    def _parse(self):
        """
                Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
                :return:
                :rtype:
                """
        self.logger.debug(F"Parser enter to {self.URL}")

        for page in self._encounter_pages():
            # Получение URL новой страницы
            for link in self._collect_doc_links(page):
                # Запуск страницы и ее парсинг
                self._parse_news_page(link)

    def _encounter_pages(self) -> str:
        _base = self.URL
        _cats = '&refinements=SubjectCategory:'

        _href = _base
        for category in self.CATEGORIES:
            _href += _cats + category

        _param = f'&pageNumber='
        page = 1
        while True:
            url = str(_href) + str(_param) + str(page)
            page += 1
            yield url

    def _collect_doc_links(self, url: str) -> list[str]:
        """
        Сбор ссылок из архива одного года
        :param url:
        :return:
        """
        try:
            self._initial_access_source(url)
            self._wait.until(ec.presence_of_all_elements_located((By.CLASS_NAME, 'List-results-items')))
        except Exception as e:
            raise NoSuchElementException() from e

        links = []

        try:
            articles = self._driver.find_elements(By.CLASS_NAME, 'List-results-items')
        except Exception as e:
            raise NoSuchElementException('list is empty') from e
        else:
            for i, el in enumerate(articles):
                try:
                    _web_link = el.find_element(By.CLASS_NAME, 'text-md-md-lh').find_element(By.TAG_NAME,
                                                                                             'a').get_attribute('href')
                except Exception as e:
                    raise NoSuchElementException(
                        'Страница не открывается или ошибка получения обязательных полей') from e
                else:
                    links.append(_web_link)
        return links

    def _parse_news_page(self, url: str) -> None:

        self.logger.debug(f'Start parse document by url: {url}')

        try:
            self._initial_access_source(url, 3)

            _title = self._driver.find_element(By.CLASS_NAME, 'document-title').text  # Title: Обязательное поле
            pub_date_text = self._driver.find_element(By.CLASS_NAME, 'doc-abstract-pubdate').text.replace(
                'Date of Publication: ', '')
            _published = dateparser.parse(pub_date_text)
            _weblink = url
        except Exception as e:
            raise NoSuchElementException(
                'Страница не открывается или ошибка получения обязательных полей') from e
        else:
            document = S3PDocument(
                None,
                _title,
                None,
                None,
                _weblink,
                None,
                {},
                _published,
                None,
            )
            try:
                _authors = self._driver.find_elements(By.XPATH, '/html/body/meta[@name="parsely-author"]')
                if _authors:
                    document.other['authors'] = []
                for author in _authors:
                    document.other['authors'].append(author.get_attribute('content'))
            except Exception:
                self.logger.debug('There aren\'t the authors in the page')

            try:
                self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(4)
                el_text = self._wait.until(ec.presence_of_element_located((By.ID, 'BodyWrapper')))
                if el_text:
                    document.text = el_text.text
            except Exception:
                self.logger.debug('There isn\'t a main text in the page')

            try:
                items = self._driver.find_elements(By.CLASS_NAME, 'doc-keywords-list-item')
                if items:
                    document.other['keywords'] = {}
                for item in items:
                    try:
                        name = self._driver.find_elements(By.XPATH, 'strong')
                        els = item.find_elements(By.CLASS_NAME, 'stats-keywords-list-item')
                        if els:
                            document.other.get('keywords')[name] = []
                        for el in els:
                            document.other.get('keywords').get(name).append(el.text)
                    except Exception as e:
                        self.logger.debug(f'There isn\'t an items of the keywords in the article; {e}')
            except Exception as e:
                self.logger.debug(f'There aren\'t the keywords in the page: {e}')

            try:
                self._find(document)
            except S3PPluginParserOutOfRestrictionException as e:
                if e.restriction == FROM_DATE:
                    self.logger.debug(f'Document is out of date range `{self._restriction.from_date}`')
                    raise S3PPluginParserFinish(self._plugin,
                                                f'Document is out of date range `{self._restriction.from_date}`', e)

    def _initial_access_source(self, url: str, delay: int = 2):
        self._driver.get(url)
        self.logger.debug('Entered on web page ' + url)
        time.sleep(delay)
        self._agree_cookie_pass()

    def _agree_cookie_pass(self):
        """
        Метод прожимает кнопку agree на модальном окне
        """
        cookie_agree_xpath = '//*[@id="onetrust-accept-btn-handler"]'

        try:
            cookie_button = self._driver.find_element(By.XPATH, cookie_agree_xpath)
            if WebDriverWait(self._driver, 5).until(ec.element_to_be_clickable(cookie_button)):
                cookie_button.click()
                self.logger.debug(F"Parser pass cookie modal on page: {self._driver.current_url}")
        except NoSuchElementException as e:
            self.logger.debug(f'modal agree not found on page: {self._driver.current_url}')
