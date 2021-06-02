
"""
Twitter Data Extraction Bot 

for user @ozkndev .

Access Token:

1390297114064916483-VJFnVXWrrbuwbfotMxDoUjcVEQWKTs

Access Token Secret:

qK6g1oeiz0yLybY0IV5MwVwgUsH0BHqkmlVHQn7dHkgX3

API Key:

LqYfTFQm4xNYdTapk8nbLU8S2

API Secret Key:

UstRhrp7wvnYATcXEEQODFV8g0rKvixCNZ4ifilnVNH5OOBhkR

"""

import tweepy
import os
import sys
import time
import pandas as pd
from pandas import DataFrame
from tweepy.models import Status
import openpyxl
import json
import re
from datetime import datetime,timedelta,timezone, tzinfo
import dateutil, pytz
from dateutil.tz import tzlocal
import schedule

for timeZone in pytz.all_timezones:
    if 'Europe/Istanbul' in timeZone:
        dateTimeObj = datetime.now(pytz.timezone(timeZone))
        realtz = timeZone
        realtime = dateTimeObj.strftime('%Y:%m:%d %H:%M:%S')
        break


CONSUMER_KEY = "LqYfTFQm4xNYdTapk8nbLU8S2"
CONSUMER_SECRET = "UstRhrp7wvnYATcXEEQODFV8g0rKvixCNZ4ifilnVNH5OOBhkR"
ACCESS_TOKEN = "1390297114064916483-VJFnVXWrrbuwbfotMxDoUjcVEQWKTs"
ACCESS_TOKEN_SECRET = "qK6g1oeiz0yLybY0IV5MwVwgUsH0BHqkmlVHQn7dHkgX3"

try:
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    auth.get_authorization_url()
    api = tweepy.API(auth)
    api.verify_credentials()
    print("Authentication OK")

except tweepy.TweepError:
    print ('Error during authentication')

def get_tweets(user):

    #user_id = user
    all_tweets = []
    for status in tweepy.Cursor(api.user_timeline, screen_name=user, tweet_mode="extended").items(30):
        all_tweets.append(status)
    # tweets = api.user_timeline(screen_name = user_id, tweet_mode = 'extended')
    
    # all_tweets.extend(tweets)

    return all_tweets

def to_csv(user_list):
    
    data_dict = dict()

    for user in user_list:
         
        all_tweets = get_tweets(user)
        user_object = api.get_user(user)
        #stat = api.get_status(u)
        like = 0
        retweet = 0 
        mentions = 0
        #print(all_tweets)
        replies = 0

        count = 0
        

        for tweets in all_tweets:
            like = tweets.favorite_count
            retweet = tweets.retweet_count
            
            data_dict[tweets.id] =[user,
                            user_object.followers_count,
                            like,
                            retweet,
                            tweets.full_text]
        
    df = DataFrame.from_dict(data_dict,orient='index',columns=["kullanıcı adı","takipçi","beğeni sayısı","retweet sayısı","tweet"])
    df.to_csv('users_tweet_info.csv',index=False)
    df.head(3)
    df.to_excel("users_tweet_info.xlsx")
    f = pd.read_csv("users_tweet_info.csv")
    return json.dumps(f)

def search_keyword_inrange(keyword):
    
    if " " in keyword:
        keyword = f"\"{keyword}\""   # iki veya daha fazla kelimelik tam aramalar için
        
    date = get_range_date()

    date_since = date[0]
    date_until = date[1]

    data_dict = dict()
            
    tweets = []
    tmp_twts = tweepy.Cursor(api.search, q=keyword).items(1000)
    
    for tweet in tmp_twts:  # tweetin son bir saat içinde atılıp atılmadığını kontrol eder.

        date_str = edit_date(tweet.created_at.replace(tzinfo = None))
        date_tweet= datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

        if date_tweet < date_until and date_tweet > date_since :
            print(date_tweet)
            tweets.append(tweet)
    
    for tweet in tweets: # şarta uyan tweet objeleri içinden gerekli bilgiler çekilir.

        tweet_date = edit_date(tweet.created_at.replace(tzinfo = None)) # zaman dilimi ayarı yapılır.
        tweet_date = datetime.strptime(tweet_date, '%Y-%m-%d %H:%M:%S')

        data_dict[tweet.id] ={"username" : tweet.user.screen_name,
                              "fav_count" : tweet.favorite_count,
                              "retweet_count" : tweet.retweet_count,
                              "text" : tweet.text,
                              "created_at" : str(tweet_date)}

    keyword = keyword.replace("\"","")

    return json.dumps(data_dict, indent = 6)  

def search_keyword(keyword):

    if " " in keyword:
        keyword = f"\"{keyword}\""   # iki veya daha fazla kelimelik tam aramalar için

    data_dict = dict()
    
    tweets = tweepy.Cursor(api.search,
                            q=keyword,
                            ).items(1000)
    
    for tweet in tweets:

        date = edit_date(tweet.created_at.replace(tzinfo = None))

        data_dict[tweet.id] ={"username" : tweet.user.screen_name,
                              "fav_count" : tweet.favorite_count,
                              "retweet_count" : tweet.retweet_count,
                              "text" : tweet.text,
                              "created_at" : str(date)}



    keyword = keyword.replace("\"","")
    # df = DataFrame.from_dict(data_dict,orient='index',columns=["kullanıcı adı","beğeni sayısı","retweet sayısı","tweet","tarih"])
    # df.to_csv(f'{keyword}.csv',index=False)
    # df.head(3)
    # df.to_excel(f"{keyword}.xlsx")
    
    return json.dumps(data_dict)

def get_info_one_user(username):
    user = api.get_user(username)
    output = {  "username" : user.screen_name, 
                "id": user.id, 
                "friends": user.friends_count, 
                "follower" : user.followers_count,
                "location": user.location}

    return json.dumps(output)

def edit_date(date):

    datee = date.strftime("%Y-%m-%d")
    hour = date.strftime("%H:%M:%S")

    list_date = datee.split("-")
    list_hour = hour.split(":")

    date_dict = dict()
    hour_dict = dict()

    last_date = ""

    for i in range(len(list_hour)):
        if i == 0:
            hour_dict["hour"] = int(list_hour[i])+3
            date_dict["year"] = int(list_date[i])
            if hour_dict["hour"] >= 24:  # zaman dilimi Türkiye'ye göre ayarlandı.
                date_dict["day"] = date_dict["day"]+1
                hour_dict["hour"] = (int(list_hour[i])+3) % 24
            
        elif i == 1:
            hour_dict["minute"] = int(list_hour[i])
            date_dict["month"] = int(list_date[i])
        else:
            hour_dict["second"] = int(list_hour[i])
            date_dict["day"] = int(list_date[i])

    for k in date_dict:
        
        if not k == "day":
            last_date += f"{date_dict[k]}-"
        else:
            last_date += f"{date_dict[k]} "

    for k in hour_dict:
    
        if not k == "second":
            last_date += f"{hour_dict[k]}:"
        else:
            last_date += f"{hour_dict[k]}"

    return last_date

def get_range_date():
    last_hour_date_time = datetime.now() 
    today = last_hour_date_time.strftime("%Y-%m-%d")
    today_hour = last_hour_date_time.strftime('%H:%M:%S')

    list_date = today.split("-")
    list_hour = today_hour.split(":")

    date_dict = dict()
    hour_dict = dict()

    for i in range(len(list_date)):
        if i == 0:
            date_dict["year"] = int(list_date[i])
        elif i == 1:
            date_dict["month"] = int(list_date[i])
        else:
            date_dict["day"] = int(list_date[i])

    for i in range(len(list_hour)):
        if i == 0:
            hour_dict["hour"] = int(list_hour[i])
        elif i == 1:
            hour_dict["minute"] = int(list_hour[i])
        else:
            hour_dict["second"] = int(list_hour[i])

    #print(date_dict)
    ind = pd.date_range(today, periods = 24, freq ='60T')

    range_date1 = ind[hour_dict["hour"]]
    range_date2 = ind[hour_dict["hour"]-1]

    return range_date2,range_date1

if __name__ == "__main__" :
    
    #keyword_tweets = search_keyword_inrange("elon musk")

    # if 
    #     schedule.every(1).to(2).hours.do(search_keyword_inrange(""))
    

    #schedule.every(interval).hours.do(job)

    keyword = str(sys.argv[1])
    print(search_keyword_inrange(keyword))
    # schedule.every(60).minutes.do(search_keyword_inrange,keyword)

    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
    
