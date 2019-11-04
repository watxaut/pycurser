import logging
import time
import os
import json

from pathlib import Path
from scrapy.crawler import CrawlerProcess

from src.diccionari.diccionari.spiders.diccionari_spider import DiccionariSpider
import src.twitter.twitter as twitter

debug = False
json_path = "src/items.json"
config_path = "config.txt"


def read_json(path):
    json_file = open(path, "r")
    items = json.load(json_file)
    json_file.close()
    return items


def run_spider(dictionary_start_id) -> bool:

    # path where scrapy will output the results. Will get erased each time it runs

    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        'FEED_URI': json_path
    })

    d_params = {"start_id": dictionary_start_id}

    process.crawl(DiccionariSpider, kwargs=d_params)
    process.start()  # the script will block here until the crawling is finished

    logger.info("Finished crawling")

    # for race conditions on writing files and so, better to sleep 1
    time.sleep(1)

    logger.info("JSON File created")

    return True


if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger('pycurser')

    # change working directory because when executed with cron might fail
    main_abs_path = str(Path(__file__).parent.absolute())
    os.chdir(main_abs_path)

    # check for items.json. If there is no file, then we need to start another page of the dictionary,
    # else, get the next not used word
    if os.path.isfile(json_path):
        l_words = read_json(json_path)
    else:  # we need to scrap
        # get start id
        f = open(config_path, "r")
        start_id = int(f.read())
        f.close()

        is_run = run_spider(start_id)
        if not is_run:
            raise Exception("Error while scrapping")
        else:
            l_words = read_json(json_path)

            # save next start id
            f_config = open(config_path, "w")
            f_config.write(l_words[0]["next_dict_id"])
            f_config.close()

    for d_word in l_words:
        if not d_word["used"]:  # if the word is not used
            d_word['used'] = True
            msg = d_word["msg"]
            break
    else:
        raise Exception("Every word used. Should never enter here")

    not_used_words = list(filter(lambda x: not x['used'], l_words))
    print("Not used words: ", len(not_used_words))
    if not_used_words:  # there is still words, save the file again
        items_json = open(json_path, "w")
        json.dump(l_words, items_json)
        items_json.close()
    else:  # no more words, erase file items.json
        logger.info("Erasing file items.json as there is no more words not used")
        os.remove(json_path)

    # now that we have the data, tweet the data
    if not debug:
        api = twitter.init_twitter_handler()
        response = twitter.send_tweet(api, msg)
    else:
        print("would tweet\n", msg)
