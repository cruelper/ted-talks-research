
# -*- coding: utf-8 -*-

import time
import re
import datetime
import json
import os
import re


from urllib.request import urlopen
from urllib.parse import urljoin
from urllib.error import HTTPError
from bs4 import BeautifulSoup


class TEDScraper:

    BASE_URL = "https://www.ted.com/talks"
    LANG_URL = "https://www.ted.com/participate/translate/our-languages"

    def __init__(self, lang="en"):
        """
        :param str url:
        :param str lang="en":
        """
        self.lang = lang
        self.target_url = TEDScraper.BASE_URL  # target url
        self.target_page_list_url = ""
        self.target_page_list = 0     # number of pages in the talk list
        self.target_page_num = 0      # number of talk pages
        self.target_talk = ""         # talk title
        self.all_page_list = 0
        self.all_talk_page_num = 0    # total number of talk pages
        self.start_time = 0
        self.end_time = 0
        self.all_processing_time = 0  # executtion time

    @staticmethod
    def make_soup(url):
        """
        Return BeautifulSoup instance from URL

        :param str url:
        :rtype: bs4.BeautifulSoup
        """
        try:
            with urlopen(url) as res:
                # print("[DEBUG] in make_soup() : Found: {}".format(url))
                html = res.read()

        except HTTPError as e:
            print("[DEBUG] in make_soup() : Raise HTTPError exception:")
            print("[DEBUG] URL: {} {}".format(url, e))
            return None

        return BeautifulSoup(html, "lxml")

    @staticmethod
    def get_languages():
        """
        Return available language, the symbol and number of talk

        :rtype list
        """
        soup = TEDScraper.make_soup(TEDScraper.LANG_URL)
        lang_div = soup.find_all("div", {"class": "languages__list__language"})

        lang_info = []
        for ld in lang_div:
            lang_type = ld.find("a").get_text()
            lang_symbol = ld.find("a").attrs['href'].replace(
                "/talks?language=", "")
            lang_talks = ld.get_text().strip().replace(lang_type, "")
            lang_talks = re.match("\d*", lang_talks)
            lang_talks = lang_talks.group()

            # print("[DEBUG] get_language lang type: {:25} symbol: {:5} {}".format(lang_type, lang_symbol, lang_talks))

            lang_info.append(
                {"lang_type": lang_type, "lang_symbol": lang_symbol, "lang_talks": lang_talks})

        return lang_info

    @staticmethod
    def get_transcript_url(s, lang="en"):
        """
        Get a link from talk link to transcript

        :param str s:
        :rtype: str
        """
        r1 = "?language=" + lang
        r2 = "/transcript?language=" + lang

        is_match = re.match(".*(\?language=).*", s)
        if is_match:
            t_url = s.replace(r1, r2)
        else:
            t_url = s + r2

        return t_url

    def get_talk_titles(self, ta_soup):
        """
        Get talk title

        :param bs4.BeautifulSoup soup:
        :rtype: list
        """
        talk_titles = ta_soup.find("h1",attrs={'data-testid': 'talk-title'}).text
        return talk_titles

    def get_all_talk_titles(self, all_talk_links):
        """
        Return a list of the titles of all talks

        :param list all_talk_links:
        :rtype: list
        """
        all_talk_titles = []
        for all_talk_link in all_talk_links:
            for atl in all_talk_link:
                self.target_url = atl
                print("[DEBUG] get_all_talk_titles()\nTarget URL: {}".format(atl))
                soup = TEDScraper.make_soup(atl)
                title_list = self.get_talk_titles(soup)

                all_talk_titles.append(title_list)
                # time.sleep(1)

        return all_talk_titles

    def get_talk_posted_date(self, ta_soup):
        """
        Return a list of talk's posted date

        :param bs4.BeautifulSoup soup:
        :rtype: list
        """
        posted_dates = ta_soup.find("span",attrs={'data-testid': 'recorded-date'}).text

        return posted_dates

    def get_all_talk_posted_date(self, all_talk_links):
        """
        Return a list of posted dates for all talks

        :param list all_talk_links:
        :rtype: list
        """
        all_talk_posted_date = []
        for all_talk_link in all_talk_links:
            for atl in all_talk_links:
                soup = TEDScraper.make_soup(atl)
                posted_date = self.get_talk_posted_date(soup)
                all_talk_posted_date.append(posted_date)
                # time.sleep(1)

        return all_talk_posted_date

    def get_talk_links(self, ta_soup):
        """
        Get the link to each talk from the current talk list,
        and return a list of the link

        :param bs4.BeautifulSoup soup:
        :rtype: List
        """
        talk_links = ta_soup.find_all("div", {"class": "talk-link"})
        talk_addresses = [self._find_talk_a(tl) for tl in talk_links]
        talk_addresses = [urljoin(TEDScraper.BASE_URL, ta)
                          for ta in talk_addresses]

        return talk_addresses

    def get_all_talk_links(self):
        delay = 4
        print("Задержка на страницу: {}".format(delay))
        """
        Get all the lnks to each talk

        :rtype: list
        """
        all_talk_links = []
        page_counter = 1
        target_url = TEDScraper.BASE_URL

        while True:
            soup = TEDScraper.make_soup(target_url)
            talk_links = self.get_talk_links(soup)
            all_talk_links.append(talk_links)
            next_link = self.get_next_talk_list_a(soup)

            if next_link is None:
                break

            page_counter += 1
            print("[ FIND ] Now page: {}".format(page_counter))
            print("         {}".format(next_link))

            target_url = next_link
            time.sleep(4)

        return all_talk_links

    def get_all_talk_page_list(self):
        """
        Get all talk list page

        :rtype: list
        """
        target_url = TEDScraper.BASE_URL
        page_list = []

        page_counter = 1
        page_list.append(target_url)

        while True:
            # print("[DEBUG] target_url: {}".format(target_url))
            ta_soup = TEDScraper.make_soup(target_url)
            next_link = self.get_next_talk_list_a(ta_soup)

            if next_link is None:
                break

            page_counter += 1
            print("[ FIND ] Now page: {}".format(page_counter))
            print("         {}".format(next_link))
            target_url = next_link
            page_list.append(next_link)

        return page_list

    def get_next_talk_list_a(self, soup):
        """
        Get a link to the next talk list

        :param bs4.BeautifulSoup soup:
        :rtype: str
        """
        pagination_div = soup.find("div", {"class": "pagination"})
        next_link_a = pagination_div.find("a", {"class", "pagination__next"})

        if next_link_a is None:
            return None

        next_link = next_link_a.attrs['href']
        next_link = urljoin(TEDScraper.BASE_URL, next_link)

        # print("next page url: {}".format(next_link))

        return next_link


    def get_talk_transcript_time(self, tr_soup):
        """
        Get the transcript time of the target talk

        :param bs4.BeautifulSoup soup:
        :rtype: list
        """
        return 0


    def get_talk_transcrpit(self, soup, ta_url):
        from selenium import webdriver
        from selenium.webdriver.common.keys import Keys
        driver = webdriver.Firefox(executable_path="/home/cruelper/Ted talks project/geckodriver")
        driver.get(ta_url)
        elem = driver.find_element_by_css_selector("span.cursor-pointer inline hover:bg-red-300 css-82uonn")
        print(elem)
    

    def get_all_language_transcript(self, ta_url):
        """
        Get transcript of all languages available for target talk

        :param str talk_url:
        :rtype: dict
        """
        t_dict = {}

        try:
            available_lang = self.get_available_language(ta_url)
        except AttributeError as e:
            print(
                "[DEBUG] in get_all_language_transcript(): Raise AttributeError exception:")
            print("      {}".format(e))

            t_dict["none"] = "no transcript text found."
            return t_dict

        lang_num = len(available_lang)
        for i, al in enumerate(available_lang):
            tr_url = TEDScraper.get_transcript_url(ta_url, al)
            print(
                "                  [{:3}/{:3}] target language: {}".format(i + 1, lang_num, al))
            # print("[DEBUG] in get_all_language_transcript()")
            # print("[DEBUG] symbol: {:5} URL: {}\n".format(al, t_url))

            tr_soup = TEDScraper.make_soup(tr_url)
            if tr_soup is not None:
                t_dict[al] = self.get_talk_transcrpit(tr_soup)

                # [DEBUG] dump json file
                # with open("./dump_files/talk_info_al" + str(num) + ".json", "w") as f:
                #     json.dump(t_dict, f, indent=2)

        return t_dict

    def get_available_language(self, ta_url):
        """
        Get the language available for target talk

        :param str talk_url:
        :rtype: list
        """
        tr_url = TEDScraper.get_transcript_url(ta_url)
        tr_soup = TEDScraper.make_soup(tr_url)
        talk_transcript_language = self._find_transcript_language(tr_soup)

        available_lang = []
        for ttl in talk_transcript_language:
            available_lang.append(ttl.attrs["value"])

        return available_lang

    def dump_talk_info(self, ta_url, save_dir=None):
        """
        Dump talk info of each talk from talk list as JSON file

        :param str url:
        """
        # create save dir if not exist
        if save_dir is None:
            save_dir = "./dump_files"
            if not os.path.isdir("dump_files"):
                os.mkdir("dump_files")
                print("[ CREATE ] create default dump dir ...")
        else:
            save_dir = os.path.expanduser(save_dir)
            if not os.path.isdir(save_dir):
                print("[ CREATE ] create dump dir: {}".format(save_dir))
                os.makedirs(save_dir)

        self.target_url = ta_url
        ta_soup = TEDScraper.make_soup(ta_url)

        
        update_date = self._get_scrape_date()
        talk_date = self.get_talk_posted_date(ta_soup)
        talk_titles = self.get_talk_titles(ta_soup)
        talk_lang = self.lang
         
        talk_topics = self.get_talk_topics(ta_soup)
                
        views = self.get_talk_views(ta_soup)
        
        likes = self.get_talk_likes(ta_soup)

        talk_info = {
            "posted_date": talk_date,
            "talk_title": talk_titles,
            "talk_topics": talk_topics,
            "views": views,
            "likes": likes
        }
        
        #print("[ GET ] get scrape date ... {}".format(talk_titles))

        return talk_info
                

    def _find_talk_posted_date(self, soup):
        """
        Find the posted date from talk page

        :param bs4.BeautifulSoup soup:
        :rtype: str
        """
        return soup.find("div", {"class": "meta"}).find("span", {"class": "meta__val"}).get_text().strip()

    def _find_talk_a(self, soup):
        """
        Find the talk link address from talk page

        :param bs4.BeautifulSoup soup:
        :rtype: str
        """
        return soup.find("h4", {"class": "h9"}).find("a").attrs['href']

    def _find_talk_title(self, soup):
        """
        Find the talk title from talk page

        :param bs4.BeautifulSoup soup:
        :rtype: str
        """
        return soup.find("h4", {"class": "h9"}).find("a").get_text().strip()

    def get_talk_topics(self, soup):
        """
        Find the talk topics from talk page

        :param bs4.BeautifulSoup soup:
        :rtype: bs4.element.ResultSet
        """
        a_tags = soup.find_all("a", class_ = "inline-block py-1 underline capitalize")
        topics = [i.text.strip() for i in a_tags]
        return topics
    
    def get_talk_views(self, soup):
        a = soup.find("div", attrs={'data-testid': 'view-count'})
        return re.findall('</span>.*?<!-- -->', str(a))[0][7:-8]
        
    def get_talk_likes(self, soup):
        list = soup.find_all("div", class_ = "transition-opacity duration-300 inline-flex items-center opacity-100")   
        return re.findall('\(.*?\)', str(list[1]))[0][9:-9]
        

    def _find_transcript_para(self, soup):
        """
        Find the talk transcript paragraph from transcript page

        :param bs4.BeautifulSoup soup:
        :rtype: bs4.element.ResultSet
        """
        return soup.find_all("ul", {"class": "talk-transcript__para"})

    def _find_transcript_text(self, soup):
        """
        Find the talk transcript text from paragraph

        :param bs4.BeautifulSoup soup:
        :rtype: bs4.element.ResultSet
        """
        return soup.find("span", {"class": "talk-transcript__para__text"})

    def _find_transcript_time(self, soup):
        """
        Find the transcript time from transcript page

        :param bs4.BeautifulSoup soup:
        :rtype: bs4.element.ResultSet
        """
        return soup.find("data", {"class": "talk-transcript__para__time"})

    def _find_transcript_language(self, tr_soup):
        """
        Find the transcrtip language from transcript page

        :param bs4.BeautifulSoup tr_soup:
        :rtype: bs4.element.ResultSet
        """
        return tr_soup.find("select", {"class": "talk-transcript__language"}).find_all("option")

    def _format_string(self, s):
        """
        Return a formatted string

        :param str s:
        :rtype: str
        """
        return s.get_text().replace("\n", " ")

    def _format_filename(self, s):
        """
        Convert spaces in filenames to underscores

        :param str s:
        :rtype: str
        """
        return s.replace(" ", "_")

    def _get_scrape_date(self):
        """
        Return the date on which scraping was performed

        :rtype: datetime.date
        """
        today = datetime.date.today()
        return today.strftime('%Y-%m-%d')

    def _convert_date2str(self, date):
        """
        Convert datetime to str

        :param str date:
        :rtype: str
        """
        tdatetime = datetime.datetime.strptime(date, "%b %Y")
        tdatetime = tdatetime.strftime("%Y-%m-%d")
        # print("[DEBUG] _convert_date2str() {}".format(tdatetime))
        return tdatetime
