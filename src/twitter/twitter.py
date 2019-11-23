import logging
import traceback
import os

import tweepy

from src.twitter.secret import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_SECRET

logger = logging.getLogger("pycurser")


def init_twitter_handler() -> tweepy.API:

    api = None
    try:

        # create OAuthHandler object and set access
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

        # create tweepy API object to fetch tweets
        api = tweepy.API(auth)

    except:
        logger.error("Error: Authentication Failed\n{}".format(traceback.format_exc()))

    return api


def send_tweet(api: tweepy.API, msg: str):
    response = api.update_status(msg)
    return response


def follow_back(api: tweepy.API):
    logger.info("Retrieving and following followers")
    for follower in tweepy.Cursor(api.followers).items():
        if not follower.following:
            logger.info(f"Following {follower.name}")
            follower.follow()
    return True


def check_mentions(api, since_id):
    logger.info("Retrieving mentions")
    new_since_id = since_id
    d_tweets = {}
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=since_id).items():
        new_since_id = max(tweet.id, new_since_id)
        if tweet.in_reply_to_status_id is not None:
            continue

        tweet_msg = tweet.text.lower()
        logger.info(f"Tweet from: {tweet.user.name}")
        logger.info(f"Text in tweet: '{tweet_msg}'")
        if '"' in tweet_msg:
            try:
                word_to_search = tweet_msg.split('"')[1]
                d_tweets[tweet.id] = {"word": word_to_search, "screen_name": tweet.user.screen_name}
            except IndexError:
                d_tweets[tweet.id] = {"word": None, "screen_name": tweet.user.screen_name}
        else:
            d_tweets[tweet.id] = {"word": None, "screen_name": tweet.user.screen_name}
    return d_tweets, new_since_id


def reply_tweet(api, tweet_id, reply_msg):
    api.update_status(
        status=reply_msg,
        in_reply_to_status_id=tweet_id,
    )
    return True


def read_since_id():
    abspath = os.path.abspath(__file__)
    dir_path = os.path.dirname(abspath)
    f = open(f"{dir_path}/since_id.txt", "r")
    since_id = int(f.read())
    f.close()
    return since_id


def update_since_id(new_since_id):
    abspath = os.path.abspath(__file__)
    dir_path = os.path.dirname(abspath)
    f = open(f"{dir_path}/since_id.txt", "w")
    f.write(f"{new_since_id}")
    f.close()

