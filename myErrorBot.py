# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request
import urllib.parse
import requests
import pprint

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template


app = Flask(__name__)

# s_bot
slack_token = "xoxb-508464543335-507908961873-67eU39lFVIosFLo24PTswKUG"
slack_client_id = "508464543335.508405959987"
slack_client_secret = "ca12e381b910b9d07d311173350c4153"
slack_verification = "RgZaLQysOr2TB4i6TEg9sGW7"
sc = SlackClient(slack_token)

# 1_bot
# slack_token = "xoxb-501387243681-508898407686-E0QRDsCcpYGK9Nsc2dcw833k"
# slack_client_id = "501387243681.508548422871"
# slack_client_secret = "c5a074bfa4fd4ab9495568578c249372"
# slack_verification = "WQUTCWXEaCGYkdwPeo1iHzBN"
# sc = SlackClient(slack_token)

# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    
    #여기에 함수를 구현해봅시다.
    url = "https://docs.python.org/ko/3/library/exceptions.html"
    req = urllib.request.Request(url)

    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")
    
    keywords = []
    search = text[12:]
    search_ = "".join(search.split()).lower()
    search_res = ""
    search_res_null = "검색결과가 없습니다.\n"
    
    try:
        if "errorlist" in search_:
            print('if 들어옴')
            # for row in soup.find_all("div", id="exception-hierarchy"):
            #     print(row)

    except IndexError:
        keywords.append(search_res_null)
    
    keywords.append("검색결과 더보기\n")

    for res in search_stackoverflow(search).items():
        keywords.append(res[0] + ":::: " + res[1])
        print(res)

    
    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'\n'.join(keywords)


def search_stackoverflow(search):
    # //////////////////////////////////////////////////////////////
    # stackoverflow 추가검색 결과
    # //////////////////////////////////////////////////////////////

    url = "https://stackoverflow.com"
    search_url = (url + "/search?q=python+" + urllib.parse.quote_plus(search.lstrip()))
    print(search_url)
    req = requests.get(search_url)
    sourcecode = req.text
    soup = BeautifulSoup(sourcecode, "html.parser")

    res = {}
    for div in soup.select("div.search-result"):
        # print(div.select("div.answered-accepted"))
        if div.select("div.answered-accepted"):
            link = div.find("a", class_="question-hyperlink").get("href")
            title = div.find("a", class_="question-hyperlink").get("title")
            # print(title + ":::: " + link)
            # cites.append(url+link)
            res[title] = url+link

    return res

# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_naver_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                            })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run('localhost', port=5000)
