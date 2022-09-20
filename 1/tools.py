import json
import os

import requests

CACHE_DIR = "./cache/"
CSV_DIR = "./csv/"
USE_CACHE = True

REGION = ""

VACANCY = "Data Engineering"

API_URL = "https://api.hh.ru"

PER_PAGE = 100

VACANCIES_LIMIT = 2000

EXPERIENCES = ["noExperience", "between1And3", "between3And6", "moreThan6", ""]
USE_EXPERIENCES = True

HEADERS = {"Content-Type": "application/json", "User-Agent": "curl/7.38.0"}

EXCLUDE_WORDS = [
    "highlighttext",
    "опыт",
    "работы",
    "data",
    "experience",
]


def die(*msg):
    print(*msg)
    exit(1)


def get_cache_json(name: str, url, method="GET", data={}):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, 0o777, True)

    if os.path.exists(CACHE_DIR + name) and USE_CACHE:
        f = open(CACHE_DIR + name, "r")
        j = json.load(f)
        f.close()
    else:
        res = requests.request(method, url, data=data)
        if res.status_code != 200:
            die(f"Can not fetch page {url} with data {data} - status code not 200", res.status_code)

        f = open(CACHE_DIR + name, "w")
        j = res.json()
        json.dump(j, f)
        f.close()

    return j



def convert_salary_to(x):
    return convert_salary_short(x, True)


def convert_salary_from(x):
    return convert_salary_short(x, False)

currencies = get_cache_json(f"currencies.json", "https://www.cbr-xml-daily.ru/daily_json.js")

def convert_salary_short(x, to=True):
    res_int = -1
    if x is not None:
        curr = x["currency"]
        if curr != "RUR":
            if curr not in currencies["Valute"]:
                return None
            rate = currencies["Valute"][curr]["Value"]/currencies["Valute"][curr]["Nominal"]
            # print(curr, rate)
        else:
            rate = 1

        if to:
            if x["to"] is not None:
                res_int = x["to"]
        else:
            if x["from"] is not None:
                res_int = x["from"]

        if res_int != -1:
            return res_int * rate
    return None