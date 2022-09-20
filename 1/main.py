import os
import urllib


import numpy as np
import tensorflow as tf
import nltk
from nltk.corpus import stopwords

from tensorflow.keras.preprocessing.text import Tokenizer

import requests
import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt

from tools import API_URL, get_cache_json, REGION, die, VACANCY, PER_PAGE, VACANCIES_LIMIT, CSV_DIR, USE_EXPERIENCES, \
    EXPERIENCES, convert_salary_from, convert_salary_to, EXCLUDE_WORDS

if REGION != "":
    # Get region
    areas = get_cache_json("areas.json", API_URL + "/areas")
    region = [k["id"] for v in areas for k in v["areas"] if k["name"] == REGION]
    if len(region) != 1:
        die("Can not find region", REGION)

dictionaries = get_cache_json(f"dictionaries.json", f"{API_URL}/dictionaries")

orig_max_colwidth_pd = pd.get_option('display.max_colwidth')
orig_max_col_pd = pd.get_option('display.max_columns')



items = []

df = DataFrame()

filter_expirienses = [""]
if USE_EXPERIENCES:
    filter_expirienses = EXPERIENCES

# Get vacancies
for experience in filter_expirienses:
    # Current page
    page = 0
    # Initial page count
    page_count = 1
    # Search limit is 2000 - count of processed items
    processed = 0

    while page < page_count:
        # print(f"Processing page {page} of {page_count}")
        data = {
            "text": VACANCY,
            "per_page": PER_PAGE,
            "page": page
        }

        exp_str = ""

        if REGION != "":
            data["area"] = region[0]

        if experience != "":
            data["experience"] = experience
            exp_str = "_" + experience

        url = f"{API_URL}/vacancies?{urllib.parse.urlencode(data)}"

        # print(url)
        vacancies = get_cache_json(f"vacancy{page}{exp_str}.json",
                                   url)
        page_count = vacancies["pages"]
        res_items = vacancies["items"]
        processed += len(res_items)
        # print(f"Vacancies found: {len(res_items)}, processed {processed}")

        res_items = [{**res_item, "experience": experience} for res_item in res_items]

        if processed >= VACANCIES_LIMIT:
            # reaches the limit
            break

        if not USE_EXPERIENCES or experience != "":
            items.extend(res_items)
            df = df.append(res_items, ignore_index=True)
            page += 1

if not os.path.exists(CSV_DIR):
    os.makedirs(CSV_DIR, 0o777, True)
df.to_csv(CSV_DIR + "/orig_res.csv")

# drop unused fields
df.index = df["id"]
for i in ["id", "premium", "created_at", "published_at", "adv_response_url", "working_days", "apply_alternate_url",
          "insider_interview", "response_url", "url", "alternate_url", "relations", "sort_point_distance", "has_test",
          "response_letter_required", "contacts", "department", "type", "address", "working_time_intervals",
          "working_time_modes"]:
    df = df.drop(i, axis=1)

# filter out archived vacancies
df = df[df["archived"] == False]
df = df.drop(["archived"], axis=1)

df["employer_short"] = df["employer"].map(lambda x: x["name"])
df["area_short"] = df["area"].map(lambda x: x["name"])
df["schedule_short"] = df["schedule"].map(lambda x: x["name"])





df["salary_from"] = df["salary"].map(convert_salary_from, na_action=None)
df["salary_to"] = df["salary"].map(convert_salary_to, na_action=None)



print(f"Количество вакансий по запросу {VACANCY}: {len(df.index)}")

for field in ["area_short", "experience", "employer_short"]:
    print("COLUMN %s" % field)
    vc = df[field].value_counts(normalize=True) * 100
    vc = vc[vc > 1]

    print(vc)

    y_pos = np.arange(len(vc))
    plt.figure(figsize=(20,10))
    plt.barh(y_pos, vc.values)
    plt.yticks(y_pos, vc.index)
    for i, v in enumerate(vc.values):
        plt.text(v, i, f'{v:6.3}', color='blue', fontweight='bold')
    plt.title(field)
    plt.show()


df_w_salary_from=df.dropna(subset=['salary_from'])
print("Resume with salary from:",len(df_w_salary_from))

df_w_salary_to=df.dropna(subset=['salary_to'])
print("Resume with salary to:",len(df_w_salary_to))

pd.set_option('display.max_columns', None)
print(df.sort_values(["salary_from"])[0:10])
# print(df_w_salary_from.sort_values(["salary_from"]).tail())
pd.set_option('display.max_columns', orig_max_col_pd)

print(df.info())
print(df.describe())

# pd.set_option('display.max_colwidth', None)
# pd.set_option('display.max_columns', None)
# print(df[0:10])
# pd.set_option('display.max_colwidth', orig_max_colwidth_pd)
# pd.set_option('display.max_columns', orig_max_col_pd)





df=df[~df["schedule_short"].isin(["Вахтовый метод","Гибкий график","Сменный график"])]

print("График:",df["schedule_short"].value_counts(normalize=True))

snippets=df["snippet"].values.tolist()

requirements=[s["requirement"] for s in snippets if s["requirement"] is not None]
responsibility=[s["responsibility"] for s in snippets if s["responsibility"] is not None]

print(snippets[0])

stop_syms='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n'

tknzr_req=Tokenizer(num_words=None,
    filters=stop_syms,
    lower=True,
    split=' ',
    char_level=False,)

tknzr_req.fit_on_texts(requirements)
items_req=sorted(tknzr_req.word_counts.items(),key=lambda x:x[1], reverse=True)

nltk.download("stopwords")

russian_stopwords=stopwords.words("russian")
english_stopwords=stopwords.words("english")

for item_req in items_req:
    if item_req[0] not in EXCLUDE_WORDS and item_req[0] not in russian_stopwords and item_req[0 ] not in english_stopwords:
        #print(item_req)
        ()

#Вытащили слова из списка
words=["python", "sql", "hadoop", "spark", "postgresql", "linux", "kafka", "clickhouse", "oracle", "docker", "scala", "ars", "kubernetes", "git", "devops"]

counts={}
for word in words:
    counts[word]=0

    for req in requirements:
        req=req.lower()
        req=req.translate(req.maketrans(stop_syms, ' '*len(stop_syms)))
        #print(req)

        if word in req.split(" "):
            counts[word]+=1
            continue

for item in counts.items():
    print(item[0],":",item[1])




if not os.path.exists(CSV_DIR):
    os.makedirs(CSV_DIR, 0o777, True)
df.to_csv(CSV_DIR + "/filtered_res.csv")
