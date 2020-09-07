from article import Article
from utils import GENRES_FILE, ARTICLES_FILE, BRITISH_BANDS_FILE, BANDS_STATS_FILE, MONTHS_STATS_KW_FILE, MONTHS_STATS_SUBJ_FILE
from pynytimes2 import NYTAPI
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from urllib.error import URLError

import pandas as pd
import utils
import csv
import sys
import os

nyt = NYTAPI("4GmxDfL35e4uyWVqfIAi2SDBYsc3zv8t")


def main():
    if utils.DEBUG:
        utils.stddbg = sys.stderr
    else:
        utils.stddbg = open(os.devnull, "w")

    with open(utils.BROKEN_LINKS_FILE, "r") as f:
        utils.BROKEN_URLS = [l.strip("\n") for l in f.readlines()]

    print("start: " + str(datetime.now().time()), file=utils.stddbg)

    last_error = None
    while True:
        try:
            # collect(start_date="1980-01-01", end_date="1981-01-02", continuous=False, cleanup=False)
            collect(continuous=True, cleanup=True)
        except URLError as e:
            last_error = e
            print("got: URLError for url {}. Restarting... \n\n".format(e.url), file=utils.stddbg)
        except UnicodeDecodeError as e:
            last_error = e
            print("got: UnidoceDecodeError for url {}. Restarting... \n\n".format(e.url), file=utils.stddbg)
        except FileExistsError as e:
            if (isinstance(last_error, URLError) and (last_error.code == 500 or last_error.reason == "Bad Request" or last_error.code == 404)) or (isinstance(last_error, UnicodeDecodeError)):
                print("got: FileExistsError, due to broken link. blacklisting...", file=utils.stddbg)
                os.remove(e.filename2)
                utils.BROKEN_URLS.append(last_error.url)
                with open(utils.BROKEN_LINKS_FILE, "a") as f:
                    f.write(last_error.url + "\n")
            last_error = e
        except Exception as e:
            print("Got unknown exception", file=utils.stddbg)
            print("end: " + str(datetime.now().time()), file=utils.stddbg)
            raise e


def split_to_months(dates):
    start, end = [datetime.strptime(_, utils.FULL_DATE_FORMAT) for _ in dates]
    months_strf = OrderedDict(((start + timedelta(_)).strftime(utils.MONTH_FORMAT), None) for _ in range((end - start).days)).keys()
    return [datetime.strptime(m, utils.MONTH_FORMAT) for m in months_strf]


def gen_months_pairs(*dates):
    return zip(split_to_months(dates)[:-1], split_to_months(dates)[1:])


def sum_articles(csv_in):
    with open(csv_in) as f:
        keys = f.read().split("\n")

    count = 0
    for key in keys:
        a, hits = fetch([key], 1955, 2020)
        print(key, ": ", hits)
        count += hits

    return count


def sum_articles_by_key(csv_in, key_in, csv_out, key_out):
    keys = list(pd.read_csv(csv_in)[key_in])

    count = 0
    with open(csv_out, "w", encoding="utf-8") as f:
        f.write("{},{}\n".format(key_in, key_out))
        for key in keys:
            a, hits = fetch([key, "music"], 1955, 2020)
            print(key, ": ", hits)
            f.write('"{}",{}\n'.format(key, hits))
            count += hits
            print(count)


def collect(start_date="1955-01-01", end_date="2020-09-02", continuous=False, cleanup=True):
    mode = "w"
    if continuous:
        mode = "a"
        af = pd.read_csv(ARTICLES_FILE)
        last_date = datetime.strptime(max(af["date"]), utils.FULL_DATE_FORMAT)

        print("continuing. last date: {}".format(last_date), file=utils.stddbg)

        start_date = last_date.replace(day=1)
        if cleanup:
            print("cleaning up to date: {}".format(start_date), file=utils.stddbg)
            last_date_str = datetime.strftime(last_date, utils.FULL_DATE_FORMAT)
            start_date_str = datetime.strftime(start_date, utils.FULL_DATE_FORMAT)

            os.rename(ARTICLES_FILE, ARTICLES_FILE[:-4] + last_date_str + ".csv")
            af.drop(af[af["date"] >= start_date_str].index, inplace=True)
            af.to_csv(ARTICLES_FILE, index=False)
        else:
            start_date += relativedelta(months=1)

        print("continuing from {}".format(start_date), file=utils.stddbg)
        start_date = datetime.strftime(start_date, utils.FULL_DATE_FORMAT)

    print("collecting from date {} to {}".format(start_date, end_date), file=utils.stddbg)
    af = None  # cleanup

    # # buffering 1MB to fit a whole month (each article ~1K, max hits for a month = 363, so it should fit)
    # with open(ARTICLES_FILE, mode, newline="\n", encoding="utf-8", buffering=1024*1024) as f:
    with open(ARTICLES_FILE, mode, newline="\n", encoding="utf-8") as f:
        cf = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        if not continuous:
            cf.writerow(["id", "headline", "date", "source", "url", "entities"])

        # for month in fetch_all(['rock music'], start_date, end_date, fq=False):
        # for month in fetch_all(['music'], start_date, end_date, fq=False):
        for month in fetch_all('subject:"Music"', start_date, end_date, fq=True):
            for page in month:
                articles = [Article(a) for a in page]
                for a in articles:
                    cf.writerow(a.get_row())
            f.flush()  # after each month
    print("success!: " + str(datetime.now().time()), file=utils.stddbg)
    exit()


def count_months_hits(phrases, begin_date, end_date, csv_out, fq=False):
    with open(csv_out, "w", newline="\n", encoding="utf-8") as fl:
        cf = csv.writer(fl, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        cf.writerow(["month", "hits"])
        for f, t in gen_months_pairs(begin_date, end_date):
            gen, hits = fetch(phrases, f, t, count=True, fq=fq)
            print("month: {}, hits: {}".format(f.strftime(r"%b-%Y"), hits), file=utils.stddbg)
            cf.writerow([f.strftime(r"%b-%Y"), hits])


def fetch_all(phrases, begin_date, end_date, fq=False):
    # yield articles generator for a certain month
    # return [fetch(phrases, f, t) for f, t in gen_months_pairs(begin_date, end_date)]
    for f, t in gen_months_pairs(begin_date, end_date):
        gen, hits = fetch(phrases, f, t - timedelta(days=1), fq, count=True)
        print("month: {}, hits: {}".format(f.strftime(r"%b-%Y"), hits), file=utils.stddbg)
        yield gen


def count_hits(phrases, begin_date, end_date):
    return fetch(phrases, begin_date, end_date, count=True).__next__()


def fetch(phrases, begin_date, end_date, fq=False, count=False):
    if fq:
        gen = nyt.article_search(
            dates={
                "begin": begin_date,
                "end": end_date
            },
            options={
                "sort": "oldest",
                "fq": phrases
            },
            count=count
        )
    else:
        gen = nyt.article_search(
            query=" AND ".join(['"{}"'.format(p) for p in phrases]),
            dates={
                "begin": begin_date,
                "end": end_date
            },
            options={
                "sort": "oldest",
            },
            count=count
        )

    if count:
        return gen, gen.__next__()

    return gen


def query_nyt(phrase):
    return nyt.article_search(
        query='"{}"'.format(phrase),
        # results = 30,
        dates = {
            "begin": datetime(1955, 1, 31),
            "end": datetime(2020, 2, 28)
        },
        options = {
            "sort": "oldest",
        }
        #     "sources": [
        #         "New York Times",
        #         "AP",
        #         "Reuters",
        #         "International Herald Tribune"
        #     ],
        #     "news_desk": [
        #         "Politics"
        #     ],
        #     "type_of_material": [
        #         "News Analysis"
        #     ]
        # }
    )

if __name__ == '__main__':
    main()