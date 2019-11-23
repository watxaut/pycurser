import argparse
import json
import logging
import os
import time
from pathlib import Path

from scrapy.crawler import CrawlerProcess

import src.twitter.twitter as twitter
from src.diccionari.diccionari.spiders.diccionari_spider import DiccionariSpider
from src.diccionari.diccionari.spiders.diccionari_word_spider import DiccionariWordSpider

debug = True


def read_json(path):
    json_file = open(path, "r")
    json_items = json.load(json_file)
    json_file.close()
    return json_items


def crawl_word(crawled_word):
    json_path = "{}/{}".format(str(Path(__file__).parent.absolute()), "word.json")
    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        'FEED_URI': json_path
    })
    d_params = {"word": crawled_word}
    process.crawl(DiccionariWordSpider, kwargs=d_params)
    process.start()  # the script will block here until the crawling is finished

    logger.info("Finished crawling word")
    # for race conditions on writing files and so, better to sleep 1
    time.sleep(1)
    logger.info("JSON File created")

    word_item = read_json(json_path)
    return word_item


def run_spider(dictionary_start_id, json_path_tweet) -> bool:
    # path where scrapy will output the results. Will get erased each time it runs
    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        'FEED_URI': json_path_tweet
    })
    d_params = {"start_id": dictionary_start_id}
    process.crawl(DiccionariSpider, kwargs=d_params)
    process.start()  # the script will block here until the crawling is finished
    logger.info("Finished crawling")
    # for race conditions on writing files and so, better to sleep 1
    time.sleep(1)

    logger.info("JSON File created")
    return True


def main():
    json_path_tweet = "src/items.json"
    config_path = "config.txt"

    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--action",
        type=str,
        choices=["follow_back", "reply_mentions"],
        help="Type of action to run. Leave empty to run the scraper",
    )

    args = parser.parse_args()

    # change working directory because when executed with cron might fail
    main_abs_path = str(Path(__file__).parent.absolute())
    os.chdir(main_abs_path)

    if args.action is None:  # run scraper and tweet
        # check for items.json. If there is no file, then we need to start another page of the dictionary,
        # else, get the next not used word
        if os.path.isfile(json_path_tweet):
            l_words = read_json(json_path_tweet)
        else:  # we need to scrap
            # get start id
            f = open(config_path, "r")
            start_id = int(f.read())
            f.close()

            is_run = run_spider(start_id, json_path_tweet)
            if not is_run:
                raise Exception("Error while scrapping")
            else:
                l_words = read_json(json_path_tweet)

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
        logger.info("Not used words: ", len(not_used_words))
        if not_used_words:  # there is still words, save the file again
            items_json = open(json_path_tweet, "w")
            json.dump(l_words, items_json)
            items_json.close()
        else:  # no more words, erase file items.json
            logger.info("Erasing file items.json as there is no more words not used")
            os.remove(json_path_tweet)

        # now that we have the data, tweet the data
        if not debug:
            api = twitter.init_twitter_handler()
            response = twitter.send_tweet(api, msg)
        else:
            logger.info("would tweet\n", msg)
    elif args.action == "follow_back":
        api = twitter.init_twitter_handler()
        is_done = twitter.follow_back(api)
        logger.info(f"Every follower followed: {is_done}")
    elif args.action == "reply_mentions":

        logger.info("Starting reply bot twitter")
        since_id = twitter.read_since_id()
        logger.info(f"Since_id: {since_id}")

        api = twitter.init_twitter_handler()

        d_tweets, new_since_id = twitter.check_mentions(api, since_id)
        twitter.update_since_id(new_since_id)
        logger.info(f"Updated since_id: '{new_since_id}'")

        # process tweets and crawl
        for tweet_id in d_tweets.keys():
            word = d_tweets[tweet_id]["word"]
            screen_name = d_tweets[tweet_id]["screen_name"]
            if word is not None:
                items = crawl_word(word)
                definition = items[0]["definition"]
                url = items[0]["url"]
                word_scraped = items[0]["word"]
                reply_msg = f"@{screen_name} {definition}\nEstudia."
                twitter.reply_tweet(api, tweet_id, reply_msg)

                # remove file json
                logger.info("Erasing file items.json")
                json_path = "{}/{}".format(str(Path(__file__).parent.absolute()), "word.json")
                os.remove(json_path)
                time.sleep(1)
            else:
                logger.info("NO WORD FOUND")
                reply_msg = f"@{screen_name} Envolta la paraula a buscar en cometes dobles (\").\n\n Estudia."
                twitter.reply_tweet(api, tweet_id, reply_msg)

            logger.info("Done replying")


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger('pycurser')

    main()
