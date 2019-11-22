import scrapy
import logging
import time

from scrapy.http.response import Response

logger = logging.getLogger('pycurser')


def return_twitter_msg(d_word: dict) -> str:
    s_word = d_word["word"]
    s_type = d_word["type"]
    s_url = d_word["url"]

    # adjectives in catalan come as adj + female termination, so I am getting the first part because it's easier
    if s_type == "adj":
        s_word = s_word.split(" ")[0]

    logger.info("Using word: '{}'".format(s_word))

    if s_type == "f":
        first_str = "puta"
    elif s_type == "m":
        first_str = "puto"
    elif s_type == "fs":
        first_str = "putes"
    elif s_type == "ms":
        first_str = "putos"
    elif s_type == "adj" or s_type == "adv":
        first_str = "puto"
    elif s_type == "v" or s_type == "v*":
        first_str = "fuck"
    elif s_type == 'símb':
        first_str = "puto"
    else:
        first_str = "fuck"  # should never fall here but whatever
    return "{first} {word}\n\nDefinició: {url}".format(first=first_str, word=s_word, url=s_url)


class DiccionariWordSpider(scrapy.Spider):

    def __init__(self, kwargs):
        self.name = "diccionariWord"
        scrapy.Spider.__init__(self)

        self.allowed_domains = ["diccionari.cat"]
        self.word = kwargs["word"]

        self.start_urls = [
            f'http://www.diccionari.cat/cgi-bin/AppDLC3.exe?APP=CERCADLC&GECART={self.word}&x=0&y=0'
        ]

    def parse(self, response: Response) -> dict:

        if "Vegeu la llista de paraules" not in response.text:
            url = response.text.split("'")[1]
        else:
            print("Word not found jej")
            return {"definition": None}

        yield scrapy.Request(url, callback=self.parse_word)

    def parse_word(self, response: Response) -> dict:

        # extract type, one of: (f, m, adj, v or v*)
        l_items = response.css(r"tr>td[colspan='2'][valign='TOP'][align='left'][width='650']>font::text").extract()
        l_items = list(map(lambda item: item.strip(), l_items))
        l_items = list(filter(lambda item: item != "", l_items))
        first_def = l_items[0]

        # get the word from the title
        word = response.css(r"span[class='enc']::text").extract()[0].strip()

        data = {
            'word': word,  # it's only 1 element
            'definition': first_def,
            'url': response.url
        }

        yield data
