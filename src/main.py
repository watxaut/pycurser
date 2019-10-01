import logging
import time
import os
import json

from scrapy.crawler import CrawlerProcess

from src.diccionari.diccionari.spiders.diccionari_spider import DiccionariSpider
import src.twitter.twitter as twitter

debug = True

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger('pycurser')

    # path where scrapy will output the results. Will get erased each time it runs
    json_path = "items.json"

    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        'FEED_URI': json_path
    })

    process.crawl(DiccionariSpider)
    process.start()  # the script will block here until the crawling is finished

    logger.info("finished crawling")

    # for race conditions on writing files and so, better to sleep 1
    time.sleep(1)

    logger.info("JSON File created")

    # try to open file
    try:
        json_file = open(json_path, "r")
    except IOError:
        raise

    d_word = json.load(json_file)[0]

    json_file.close()

    # retrieve the message to send
    msg = d_word["msg"]

    # now that we have the data, tweet the data
    if not debug:
        api = twitter.init_twitter_handler()
        response = twitter.send_tweet(api, msg)

    # erase json file
    os.remove(json_path)
    logger.debug("Removed JSON file")


