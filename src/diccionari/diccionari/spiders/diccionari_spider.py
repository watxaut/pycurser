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


class DiccionariSpider(scrapy.Spider):
    """
    This Spider will crawl a random page of the dictionary and return the information of one of the words in it in
    the form of a dictionary with word, genre, url and the whole message to send (to twitter in this case)
    """

    def __init__(self, kwargs):
        self.name = "diccionari"
        scrapy.Spider.__init__(self)

        self.allowed_domains = ["diccionari.cat"]
        self.start_id = kwargs["start_id"]

        self.start_urls = [
            'http://www.diccionari.cat/cgi-bin/AppDLC3.exe?APP=SEGUENTS&P={n_id}'.format(n_id=self.start_id)
        ]

    def parse(self, response: Response) -> dict:
        """
        Parses the search page from the dictionary and gets the URL's of the words and follows the first one
        :param response: response from the scrapy request
        :type response: scrapy.http.response.Response
        :return: yields a dictionary with word, type, url and msg for the dictionary word
        """

        # get <a> elements and retrieve the first one
        tag_urls = response.css(r"a[href*='GECART']::attr(href)")

        # get the next page GECART ID and save it
        js_next = response.css("a[class='SEGUENTS']::attr(href)")[0].get()
        start_id_next = js_next.split("(")[-1].split(")")[0]
        self.start_id = start_id_next

        for tag in tag_urls:
            url = tag.get()
            yield scrapy.Request(url, callback=self.parse_word)

            time.sleep(1)

        # # follow the link of the first word in the page and stop
        # yield response.follow(url_word, self.parse_word)

    def parse_word(self, response: Response) -> dict:
        """
        Parses the word and subtracts the type(f, m, adj, v or v*), the url and the message to send
        :param response: scrapy.http.response.Response
        :return: dict
        """

        # extract type, one of: (f, m, adj, v or v*)
        l_items = response.css(r"tr>td[colspan='2'][valign='TOP'][width='650']>font>i::text").extract()
        l_items = list(map(lambda item: item.strip(), l_items))

        type_possibilities = ["m", "f", "adj", "adv", "v", "v*", "pl", 'símb']

        l_type = list(filter(lambda item: item in type_possibilities, l_items))

        # should at least have 1 type, if not raise because there is a case that we do not control
        l_type = [item.strip() for item in l_type]
        try:
            s_type = l_type[0]
        except IndexError:
            str_err = "Something wrong with this l_items: '{}' in url: '{}'".format(l_items, response.url)
            logger.error(str_err)
            raise IndexError(str_err)

        # if the type is plural, then add and s to the type
        if len(l_type) > 1:
            if "pl" == l_type[1]:
                s_type += "s"

        # get the word from the title
        word = response.css(r"span[class='enc']::text").extract()[0].strip()

        data = {
            'word': word,  # it's only 1 element
            'type': s_type,
            'url': response.url,
            'used': False,
            'next_dict_id': self.start_id
        }

        # creates the message to send to twitter depending on the type of the word
        data["msg"] = return_twitter_msg(data)
        print(data)

        yield data
