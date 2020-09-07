from utils import BRITISH_BANDS_FILE, BANDS_STATS_FILE, AMERICAN_BANDS_FILE, GENRES_STATS_FILE, BANDS_SAMPLES_FILES
from utils import ARTICLES_FILE, ARTICLES_TAGGED_FILE, ARTICLES_EXPANDED_FILE, AMERICAN_BANDS_EXPANDED_FILE, AMERICAN_BANDS_YEARS_FILE
from dbpedia_collector import AMBIGUOUS_BANDS, TOP_100
from article_entities_extractor import extract_article_text
from pprint import pprint

import utils
import re
import itertools
import random
import pandas as pd
from datetime import datetime


def check_for_duplicates(lst):
    lst_set = set(lst)

    if len(lst) > len(lst_set):
        for a in lst_set:
            lst.remove(a)

        print("duplicates!!!:")
        pprint(lst)
    else:
        print("no duplicates, all good")

    print("")


class Bands(object):
    SEP_WORDS = [", ", " & ", " and "]

    def __init__(self, bf, af):
        self.bf = bf
        self.af = af
        # check_for_duplicates(list(self.bf["band"]))

        self.bands = self.bf[["band", "start_year", "genres"]]
        self.bands_years = {}

        self.bands_stats = {}
        self.bands_w_sep = {}

        self.bands_genres = {}
        self.bands_dups = {}

        self.genres_stats = {}

        self.create_years_dict()

    def export_stats(self):
        self.bf["hits"] = [self.bands_stats[b] for b in self.bands["band"]]
        self.bf.to_csv(BANDS_STATS_FILE, index=False)

        gsf = pd.DataFrame(self.genres_stats.items(), columns=["genre", "hits"])
        gsf.to_csv(GENRES_STATS_FILE, index=False)

    def add_band_year_dict_entry(self, band, year):
        # for duplicates
        if band in self.bands_years:
            self.bands_years[band] = min(self.bands_years[band], year)
        else:
            self.bands_years[band] = year

    def add_band_year(self, band, year):
        self.add_band_year_dict_entry(band, year)
        if band.startswith("the "):
            self.add_band_year_dict_entry(band[4:], year)

    def create_years_dict(self):
        self.bands_years = {}

        for band, year, genres in self.bands.itertuples(index=False):
            # skip ambiguous bands
            if band in AMBIGUOUS_BANDS:
                continue

            self.add_band_year(band, year)
            if any([sw in band for sw in self.SEP_WORDS]):
                for sub_band in re.split("|".join(self.SEP_WORDS), band):
                    self.add_band_year(sub_band.strip(), year)

    def __contains__(self, item):
        band, year = item
        return band in self.bands_years and self.bands_years[band] <= year

    def create_bands_stats_dict(self):
        self.bands_stats = {}
        self.bands_w_sep = {}

        for band, year, genres in self.bands.itertuples(index=False):
            self.bands_stats[band] = 0

            if any([sw in band for sw in self.SEP_WORDS]):
                self.bands_w_sep[band] = re.split("|".join(self.SEP_WORDS), band)

    def create_band_genres_dict(self):
        self.bands_genres = {}
        self.bands_dups = {}

        for band, year, genres in self.bands.itertuples(index=False):
            genres = genres.split("|")

            # handle duplicates
            if band in self.bands_genres:
                self.bands_dups[band].append({"year": year, "genres": genres})
                self.bands_genres[band] = self.bands_dups[band]
            else:
                self.bands_genres[band] = genres
                self.bands_dups[band] = [{"year": year, "genres": genres}]

        self.bands_dups = {b: y for b, y in self.bands_dups.items() if len(y) > 1}

    def create_genres_stats_dict(self):
        self.genres_stats = {}

        genres = set(itertools.chain(*[g.split("|") for g in self.bands["genres"]]))
        self.genres_stats = {g: 0 for g in genres}

    def get_tagged_bands(self, tags):
        bands = []
        pending_bands = {}
        for tag in tags:
            if tag in self.bands_stats:
                bands.append(tag)
            elif "the " + tag in self.bands_stats:
                bands.append("the " + tag)
            else:
                for band, parts in self.bands_w_sep.items():
                    if tag in parts or "the " + tag in parts:
                        if band not in pending_bands:
                            pending_bands[band] = list(parts)
                        try:
                            pending_bands[band].remove(tag)
                        except ValueError:
                            pass
                        try:
                            pending_bands[band].remove("the " + tag)
                        except ValueError:
                            pass

        bands.extend([b for b, p in pending_bands.items() if len(p) == 0])
        return list(set(bands))

    def make_tags_col(self):
        tags_col = []
        for entities, year in self.af[["entities", "date"]].itertuples(index=False):
            year = int(year[:4])
            tags_col.append("|".join([
                # tidy entities a bit
                e for e in entities.strip('"').replace("\\'s", "").replace(" , ", ", ").split("|")
                if (e, year) in self
            ]))

        self.af["tags"] = tags_col

    def make_bands_col(self, with_stats=False):
        self.create_bands_stats_dict()
        bands_col = []
        for tags in self.af["tags"]:
            bands_col.append("|".join(self.get_tagged_bands(tags.split("|"))))

        if with_stats:
            self.create_bands_stats_dict()
            for band in itertools.chain(*(b.split("|") for b in bands_col if b)):
                self.bands_stats[band] += 1

            self.export_stats()

        self.af["bands"] = bands_col

    def make_genres_col(self, with_stats=False):
        self.create_band_genres_dict()

        genres_col = []
        for bands, year in self.af[["bands", "date"]].itertuples(index=False):
            year = int(year[:4])
            if bands:
                bands = bands.split("|")
                genres = list(itertools.chain(*[self.bands_genres[b] for b in bands]))
                genres_of_dups = [g for g in genres if isinstance(g, dict)]

                if genres_of_dups:
                    genres = [g for g in genres if isinstance(g, str)]
                    genres.extend(itertools.chain(*[g["genres"] for g in genres_of_dups if g["year"] <= year]))

                genres_col.append("|".join(set(genres)))
            else:
                genres_col.append("")

        if with_stats:
            self.create_genres_stats_dict()
            for genre in itertools.chain(*(g.split("|") for g in genres_col if g)):
                self.genres_stats[genre] += 1

            self.export_stats()

        self.af["genres"] = genres_col


def expand_articles(af):
    col_names = ["id", "date", "genres"]
    new_rows = []
    for i, date, genres in af[col_names].itertuples(index=False):
        new_rows.extend([(i, date, g) for g in genres.split("|") if g])

    axf = pd.DataFrame(new_rows, columns=col_names)
    axf.to_csv(ARTICLES_EXPANDED_FILE, index=False)
    return new_rows


EXPANDED_COLUMNS = ["genre", "date", "count"]


def expand_genres_year_count(df, genres, cols, date_format=False, with_years=False):
    years_total = {y: 0 for y in range(1954, 2021)}
    genres_by_year = {g: {y: 0 for y in range(1954, 2021)} for g in genres}

    for genres, year in df[cols].itertuples(index=False):
        if date_format:
            year = int(year[:4])

        for genre in genres.split("|"):
            years_total[year] += 1
            if genre:
                genres_by_year[genre][year] += 1

    new_rows = [
        (g, y, round(c / years_total[y] * 100, 2) if years_total[y] else 0)
        for g, yr in genres_by_year.items()
        for y, c in yr.items()
    ]

    dfx = pd.DataFrame(new_rows, columns=EXPANDED_COLUMNS)
    dfx.sort_values(by=[EXPANDED_COLUMNS[0], EXPANDED_COLUMNS[1]], inplace=True)

    if with_years:
        yfx = pd.DataFrame(years_total.items(), columns=["year", "count"])
        return dfx, yfx
    else:
        return dfx


def expand_articles_genres_year_count(af, genres):
    col_names = ["genres", "date"]
    afx = expand_genres_year_count(af, genres, col_names, date_format=True)
    afx.to_csv(ARTICLES_EXPANDED_FILE, index=False)


def expand_bands_genres_year_count(bands):
    col_names = ["genres", "start_year"]
    bfx, yfx = expand_genres_year_count(bands.bf, bands.genres_stats.keys(), col_names, date_format=False, with_years=True)
    bfx.drop(bfx[bfx[EXPANDED_COLUMNS[0]] == "Heartland rock"].index, inplace=True)
    bfx.to_csv(AMERICAN_BANDS_EXPANDED_FILE, index=False)
    yfx.to_csv(AMERICAN_BANDS_YEARS_FILE, index=False)


def sample_ambiguous_bands(aft, sample=5):
    article_samples = {b: [] for b in AMBIGUOUS_BANDS}
    for bands, url in aft[["bands", "url"]].itertuples(index=False):
        for band in bands.split("|"):
            if band in article_samples:
                article_samples[band].append(url)

    article_samples = {b: random.sample(arts, sample) for b, arts in article_samples.items()}
    article_samples = {b: [extract_article_text(a) for a in arts] for b, arts in article_samples.items()}

    # article_samples = [(b, a) for b, arts in article_samples.items() for a in arts]
    # gsf = pd.DataFrame(article_samples, columns=["band", "articles"])
    # gsf.to_csv(BANDS_SAMPLES_FILES, index=False)
    return article_samples


def check_top_100(bands):
    for b in TOP_100:
        if (b, 2020) not in bands:
            print(b)


def main():
    print("start: " + str(datetime.now().time()), file=utils.stddbg)
    bands_british = Bands(pd.read_csv(BRITISH_BANDS_FILE), pd.read_csv(ARTICLES_FILE))
    bands_american = Bands(pd.read_csv(AMERICAN_BANDS_FILE), None)
    check_for_duplicates(list(bands_british.af["id"]))

    print("british: " + str(datetime.now().time()), file=utils.stddbg)
    bands_british.make_tags_col()
    # drop articles without tags
    bands_british.af.drop(bands_british.af[(bands_british.af["tags"] == "")].index, inplace=True)
    print("tagged: " + str(datetime.now().time()), file=utils.stddbg)

    bands_british.make_bands_col(with_stats=True)
    # drop articles without bands
    bands_british.af.drop(bands_british.af[(bands_british.af["bands"] == "")].index, inplace=True)
    print("banded: " + str(datetime.now().time()), file=utils.stddbg)

    bands_british.make_genres_col(with_stats=True)
    print("genred: " + str(datetime.now().time()), file=utils.stddbg)

    expand_articles_genres_year_count(bands_british.af, bands_british.genres_stats.keys())
    print("expanded: " + str(datetime.now().time()), file=utils.stddbg)

    print("american: " + str(datetime.now().time()), file=utils.stddbg)
    bands_american.create_genres_stats_dict()
    expand_bands_genres_year_count(bands_american)

    bands_british.af.to_csv(ARTICLES_TAGGED_FILE, index=False)
    print("end: " + str(datetime.now().time()), file=utils.stddbg)

if __name__ == '__main__':
    main()
