from utils import BRITISH_BANDS_FILE, AMERICAN_BANDS_FILE
from SPARQLWrapper import SPARQLWrapper, JSON

import pandas as pd

BANDS_QUERY_PRE = """
SELECT distinct
(lcase(str(?band_name)) as ?band) 
?link
(GROUP_CONCAT(DISTINCT ?genre_name; SEPARATOR="|") as ?genres) 
(MIN(?_origin) as ?origin) 
(MIN(year(xsd:dateTime(?start_date))) as ?start_year) 
(MIN(?end_year) as ?end_year)
WHERE {
       VALUES ?rock_genre { dbr:Rock_music }

       ?band a dbo:Band ;
       foaf:name ?band_name;
       dbo:genre ?_genre;
       dbo:activeYearsStartYear ?start_date.
       
       ?rock_genre dbo:musicSubgenre ?rock_subgenre.
       ?rock_genre dbo:musicFusionGenre ?rock_fusion.
       
       ?_genre foaf:name ?_genre_name.
       BIND (str(?_genre_name) as ?genre_name).
       BIND (?band as ?link).
       
       OPTIONAL {?band dbo:activeYearsEndYear ?end_date}.
       BIND (if(BOUND(?end_date), year(xsd:dateTime(?end_date)), 0) as ?end_year).
"""

BANDS_QUERY_POST = """
      }
ORDER BY ?band
"""


HOMETOWN_NORMAL_QUERY = """
       ?band dbo:hometown ?_origin.
       ?_origin dbo:country ?country.
       FILTER (?_genre = ?rock_genre || ?_genre = ?rock_subgenre || ?_genre = ?rock_fusion).
"""

HOMETOWN_SUBDIV_QUERY = """
       ?band dbo:hometown ?_origin1.
       ?_origin1 dbp:subdivisionName ?_origin.
       FILTER (?_genre = ?rock_genre || ?_genre = ?rock_subgenre || ?_genre = ?rock_fusion).
"""


ORIGIN_NORMAL_QUERY = """
       ?band dbp:origin ?_origin.
       OPTIONAL {?band dbo:hometown ?hometown}.
       FILTER (?_genre = ?rock_genre || ?_genre = ?rock_subgenre || ?_genre = ?rock_fusion).
       FILTER (!BOUND(?hometown)).
"""

HOMETOWN_PETTY_QUERY = """
       ?band dbo:hometown ?_origin.
       FILTER (?_genre = ?rock_genre || ?_genre = ?rock_subgenre || ?_genre = ?rock_fusion).
"""


BRITISH_HOMETOWN_NORMAL_QUERY = BANDS_QUERY_PRE + HOMETOWN_NORMAL_QUERY + """
       FILTER (?country = dbr:United_Kingdom || ?country = dbr:England).
""" + BANDS_QUERY_POST

BRITISH_HOMETOWN_SUBDIV_QUERY = BANDS_QUERY_PRE + HOMETOWN_SUBDIV_QUERY + """
       FILTER (STRSTARTS(str(?_origin),"United Kingdom") || STRSTARTS(str(?_origin),"England")).
""" + BANDS_QUERY_POST

BRITISH_ORIGIN_NORMAL_QUERY = BANDS_QUERY_PRE + ORIGIN_NORMAL_QUERY + """
       FILTER (CONTAINS(str(?_origin), "United Kingdom") || CONTAINS(str(?_origin), "England")).
""" + BANDS_QUERY_POST

BRITISH_HOMETOWN_PETTY_QUERY = BANDS_QUERY_PRE + HOMETOWN_PETTY_QUERY + """
       FILTER (?_origin = dbr:England || ?_origin = dbr:United_Kingdom || str(?band_name) = "Queen")
""" + BANDS_QUERY_POST


AMERICAN_HOMETOWN_NORMAL_QUERY = BANDS_QUERY_PRE + HOMETOWN_NORMAL_QUERY + """
       FILTER (?country = dbr:United_States || ?country = dbr:United_States_of_America).
""" + BANDS_QUERY_POST

AMERICAN_HOMETOWN_SUBDIV_QUERY = BANDS_QUERY_PRE + HOMETOWN_SUBDIV_QUERY + """
       FILTER (STRSTARTS(str(?_origin),"United States") || STRSTARTS(str(?_origin),"USA")).
""" + BANDS_QUERY_POST

AMERICAN_ORIGIN_NORMAL_QUERY = BANDS_QUERY_PRE + ORIGIN_NORMAL_QUERY + """
       FILTER (CONTAINS(str(?_origin), "United States") || CONTAINS(str(?_origin), "USA")).
""" + BANDS_QUERY_POST

AMERICAN_HOMETOWN_PETTY_QUERY = BANDS_QUERY_PRE + HOMETOWN_PETTY_QUERY + """
       FILTER (?_origin = dbr:United_States || ?country = dbr:United_States_of_America)
""" + BANDS_QUERY_POST

AMBIGUOUS_BANDS = [
    "the times", "apple", "birdland", "james", "free", "abc", "the eagles",
    "king", "chelsea", "fox", "jack", "mass", "europeans", "the europeans",
    "holocaust", "the music", "the verve", "blue", "morgan", "ph.d.", "stars",
    "hanson", "firebird", "christie", "the creation", "keith", "the cross",
    "caravan", "samson", "the bolshoi", "kenny", "home", "the sweet",
    "the wall", "travis", "neo", "lucas", "lucas", "keats", "the news", "arnold",
    "the mirage", "esquire", "family", "rain", "gomez", "the movies", "nova",
    "slade", "london", "keane", "babe ruth", "revolver", "the fuse", "twist",
    "mccoy", "flash", "ash", "gene", "lomax", "the doll", "blackstar", "forest",
    "harrisons", "jet", "lone star", "rococo", "palladium", "ricky", "the blood",
    "satan", "darling", "the view", "raven", "dare", "elviss", "fink", "hell",
    "magnum", "buster", "complex", "bonham", "the high fidelity", "cressida", "hood",
    "marion", "the saints", "the truth", "trucks", "jesu", "the attack", "the fall",
    "halo", "the farm", "sawyer", "spice", "the moment", "kingdom come", "godot",
    "the firm", "the monks", "the story", "angelica", "alfie", "cannon", "spector",
    "the birds", "the koreans", "the records", "latin quarter", "crew", "tank",
    "the guns", "camel", "man", "the beat", "thunder", "bandit", "blitz", "design",
    "superstar", "peach", "the work", "logan", "midas", "tiger", "breathless",
    "ace", "loop", "the ukrainians", "iona", "blitzkrieg bop", "quintessence",
    "the innocents", "the crescent", "the wheels", "vega", "space", "asap",
    "plainsong", "the union", "the dylans"
]


TOP_100 = [b.lower() for b in [
    "The Beatles", "Rolling Stones", "Led Zeppelin", "The Who", "The Jimi Hendrix Experience",
    "Pink Floyd", "The Clash", "Cream", "Elton John", "Queen", "Black Sabbath", "David Bowie",
    "The Kinks", "Emerson, Lake and Palmer", "Fleetwood Mac", "Deep Purple", "Joe Cocker",
    "Iron Maiden", "The Yardbirds", "Dire Straits", "Jethro Tull", "The Police", "King Crimson",
    "Moody Blues", "Rod Stewart", "Sex Pistols", "The Animals", "The Cure", "Status Quo",
    "Paul McCartney", "Cat Stevens", "Eric Clapton", "Sting", "John Lennon", "The Faces",
    "Genesis", "Electric Light Orchestra", "Peter Gabriel", "The Smiths", "Yes", "Jeff Beck",
    "Radiohead", "The Hollies", "Peter Frampton", "The Pretty Things", "Judas Priest",
    "Small Faces", "John Mayall's Bluesbreakers", "Uriah Heep", "Motorhead", "Oasis",
    "Ozzy Osbourne", "Phil Collins", "Whitesnake", "George Harrison", "The Nice", "Eurythmics",
    "Manfred Mann's Earth Band", "Def Leppard", "PIL", "Osibisa", "Procol Harum", "Blind Faith",
    "The Stone Roses", "The Dave Clark Five", "UltraVox", "Coldplay", "Robbie Williams", "Blur",
    "Herman's Hermits", "Massive Attack", "Placebo", "Prodigy", "Mandala", "Free", "Traffic",
    "Gravy Train", "Joy Division", "Ten Years After", "Depeche Mode", "Porcupine Tree",
    "Robert Plant", "The Zombies", "The Jam", "Henry Cow", "T-Rex", "Wishbone Ash", "Gomez",
    "Morrissey", "Muse", "The Verve", "Humble Pie", "Van der graaf Generator", "Rick Wakeman",
    "The Groundhogs", "The Darkness", "Jesus and Mary Chain", "The Herd", "Richard Ashcroft",
    "Marillion"
]]

COLUMN_KEYS = ['band.value', 'link.value', 'genres.value', 'start_year.value', 'end_year.value']


def main():
    # British
    query_dbpedia(BRITISH_HOMETOWN_NORMAL_QUERY, COLUMN_KEYS).to_csv(BRITISH_BANDS_FILE, index=False)
    query_dbpedia(BRITISH_HOMETOWN_SUBDIV_QUERY, COLUMN_KEYS).to_csv(BRITISH_BANDS_FILE, mode='a', index=False, header=False)
    query_dbpedia(BRITISH_ORIGIN_NORMAL_QUERY, COLUMN_KEYS).to_csv(BRITISH_BANDS_FILE, mode='a', index=False, header=False)
    query_dbpedia(BRITISH_HOMETOWN_PETTY_QUERY, COLUMN_KEYS).to_csv(BRITISH_BANDS_FILE, mode='a', index=False, header=False)

    bands = pd.read_csv(BRITISH_BANDS_FILE)
    bands.drop_duplicates(inplace=True)

    # drop bad dates
    bands.drop(bands[bands["start_year.value"] < 1900].index, inplace=True)

    # manually remove duplicates
    bands.drop(bands[(bands["band.value"] == "the kinks") & (bands["start_year.value"] == 1963)].index, inplace=True)
    bands.drop(bands[(bands["band.value"] == "the clash") & (bands["genres.value"] == "Alternative rock|Punk rock")].index, inplace=True)
    bands.drop(bands[(bands["band.value"] == "genesis") & (bands["genres.value"] == "Art rock|Pop rock|Progressive rock|Rock music|Soft rock")].index, inplace=True)
    bands.drop(bands[(bands["band.value"] == "iron maiden") & (bands["link.value"] != "http://dbpedia.org/resource/Iron_Maiden")].index, inplace=True)
    bands.drop(bands[(bands["band.value"] == "girlschool") & (bands["genres.value"] == "Heavy metal")].index, inplace=True)
    bands.drop(bands[(bands["band.value"] == "wishbone ash") & (bands["end_year.value"] == 0)].index, inplace=True)
    # all other duplicates are just bands named the same

    # manually add bands that are corrupted on dbpedia
    bands.loc[len(bands)] = ["king crimson", "", "Progressive rock|Art rock", 1968, 0]
    bands.loc[len(bands)] = ["eurythmics", "", "New wave|Dance-rock", 1980, 2005]
    bands.loc[len(bands)] = ["coldplay", "", "Alternative rock|Pop rock", 1996, 0]
    bands.loc[len(bands)] = ["placebo", "", "Alternative rock", 1994, 0]

    # get rid of .value in column names
    bands.rename(columns={k: k[:-6] for k in COLUMN_KEYS}, inplace=True)
    bands.to_csv(BRITISH_BANDS_FILE, index=False)


    # American
    query_dbpedia(AMERICAN_HOMETOWN_NORMAL_QUERY, COLUMN_KEYS).to_csv(AMERICAN_BANDS_FILE, index=False)
    query_dbpedia(AMERICAN_HOMETOWN_SUBDIV_QUERY, COLUMN_KEYS).to_csv(AMERICAN_BANDS_FILE, mode='a', index=False, header=False)
    query_dbpedia(AMERICAN_ORIGIN_NORMAL_QUERY, COLUMN_KEYS).to_csv(AMERICAN_BANDS_FILE, mode='a', index=False, header=False)
    query_dbpedia(AMERICAN_HOMETOWN_PETTY_QUERY, COLUMN_KEYS).to_csv(AMERICAN_BANDS_FILE, mode='a', index=False, header=False)

    bands = pd.read_csv(AMERICAN_BANDS_FILE)
    bands.drop_duplicates(inplace=True)

    # drop bad dates
    bands.drop(bands[bands["start_year.value"] < 1900].index, inplace=True)

    # get rid of .value in column names
    bands.rename(columns={k: k[:-6] for k in COLUMN_KEYS}, inplace=True)
    bands.to_csv(AMERICAN_BANDS_FILE, index=False)


def query_dbpedia(query, columns):
    # Specify the DBPedia endpoint
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")



    sparql.setQuery(query)

    # Convert results to JSON format
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    results_df = pd.io.json.json_normalize(results['results']['bindings'])
    # results_df[['band.value', 'city.value', 'start_year.value']]


    print(len(results_df))
    return results_df[columns]

# def remove_duplicates()

if __name__ == '__main__':
    main()