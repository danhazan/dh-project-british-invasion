from utils import JUNK_TEXTS
from boilerpipe.extract import Extractor
from nltk import sent_tokenize, word_tokenize, pos_tag, ne_chunk
from nltk import Tree

import spacy
import utils
import unicodedata
import socket
from urllib.error import URLError


# nltk extractor
def extract_entities_nltk(text):
    entities = []
    for sentence in sent_tokenize(text):
        chunks = ne_chunk(pos_tag(word_tokenize(sentence)))
        entities.extend([chunk for chunk in chunks if hasattr(chunk, 'label')])
    return entities


def get_continuous_chunks(text, labels=None):
    if labels is None:
        labels = ["ORGANIZATION", "PERSON", "LOCATION", "DATE", "TIME", "MONEY", "PERCENT", "FACILITY", "GPE"]

    chunked = ne_chunk(pos_tag(word_tokenize(text)))
    continuous_chunk = []
    current_chunk = []

    for subtree in chunked:
        # if type(subtree) == Tree and subtree.label() in labels:
        #     current_chunk.append(" ".join([token for token, pos in subtree.leaves()]))
        if type(subtree) == Tree and subtree.label() in labels:
            current_chunk.append(" ".join([token+"/"+subtree.label() for token, pos in subtree.leaves()]))
        if current_chunk:
            named_entity = " ".join(current_chunk)
            if named_entity not in continuous_chunk:
                continuous_chunk.append(named_entity)
                current_chunk = []
        else:
            continue

    return continuous_chunk


# load spacy nlp library
nlp = spacy.load('en_core_web_lg')
# nlp = spacy.load('en_core_web_sm')


# spacy extractor
def extract_entities_spacy(text):
    """
    Performs named entity recognition from text
    :param text: Text to extract
    """

    # parse text into spacy document
    doc = nlp(text.strip())

    # create sets to hold words
    named_entities = set()
    money_entities = set()
    organization_entities = set()
    location_entities = set()
    product_entities = set()
    time_indicator_entities = set()

    for i in doc.ents:
        entry = str(i.lemma_).lower()
        text = text.replace(str(i).lower(), "")
        # Time indicator entities detection
        if i.label_ in ["TIM", "DATE"]:
            time_indicator_entities.add(entry)
        # money value entities detection
        elif i.label_ in ["MONEY"]:
            money_entities.add(entry)
        # organization entities detection
        elif i.label_ in ["ORG"]:
            organization_entities.add(entry)
        # Geographical and Geographical entities detection
        elif i.label_ in ["GPE", "GEO"]:
            location_entities.add(entry)
        # product entities detection
        elif i.label_ in ["PRODUCT"]:
            product_entities.add(entry)
        # extract artifacts, events and natural phenomenon from text
        elif i.label_ in ["WORK_OF_ART", "EVENT", "NORP", "PERSON"]:
            named_entities.add(entry.title().lower())

    # print("named entities - {}".format(named_entities))
    # print("money entities - {}".format(money_entities))
    # print("location entities - {}".format(location_entities))
    # print("time indicator entities - {}".format(time_indicator_entities))
    # print("organization entities - {}".format(organization_entities))
    # print("\n")

    return named_entities.union(organization_entities).union(product_entities)


BAD_SUBDOMAINS = ["blogs.nytimes", "dealbook.nytimes", "json8.nytimes"]


def extract_article_text(url):
    if url in utils.BROKEN_URLS or any([True for sd in BAD_SUBDOMAINS if sd in url]):
        return ""

    while True:
        try:
            extractor = Extractor(extractor='ArticleExtractor', url=url)
            break
        except socket.timeout:
            print("got socket.timeout on url: {}. retrying...".format(url), file=utils.stddbg)
        except URLError as e:
            if e.reason == "timed out":
                print("got urllib 'timed out' on url {}. retrying...".format(url), file=utils.stddbg)
            elif hasattr(e.reason, "strerror") and e.reason.strerror == 'getaddrinfo failed':
                print("got urllib 'getaddrinfo failed' on url {}. retrying...".format(url), file=utils.stddbg)
            elif e.code == 503:
                print("got urllib 503 error on url {}. retrying...".format(url), file=utils.stddbg)
            else:
                if not hasattr(e, "url"):
                    e.url = url
                raise
        except Exception as e:
            e.url = url
            raise e

    text = str(unicodedata.normalize('NFKD', (str(extractor.getText()))).encode('ascii', 'ignore'))
    return filter_junk(text)
    # return text


def filter_junk(text):
    # pre
    text = text.lstrip("b'").lstrip('b"')
    #suff
    text = text.rstrip("\\nAdvertisement\\n'").rstrip('\\nAdvertisement\\n"')
    # notices
    for j in JUNK_TEXTS:
        text = text.replace(j, "")
    # spacing
    text = text.replace("\\n", "\n")

    return text




def extract_article_entities(article):
    """
    type article: article.Article
    """
    return extract_entities_spacy(extract_article_text(article.url) + ".\n " + article.getText())
    # return get_continuous_chunks(extract_article_text(article.url) + ".\n " + article.getText())


if __name__ == '__main__':
    # url = "https://www.nytimes.com/1970/05/17/archives/john-cages-words-were-prophetic-john-cages-words-were-prophetic.html"
    url = "https://www.nytimes.com/1968/12/15/archives/the-producer-of-the-new-rock-the-producer-of-the-new-rock.html"
    url = "https://www.nytimes.com/1993/06/20/magazine/the-power-of-love.html"


    # import pandas as pd
    # from utils import ARTICLES_TAGGED_FILE
    #
    # urls = list(pd.read_csv(ARTICLES_TAGGED_FILE[:-4] + "_.csv")["url"])
    #
    # texts = [extract_article_text(u) for i, u in enumerate(urls)]


    text = extract_article_text(url)
    ents = extract_entities_spacy(text)
    ents2 = get_continuous_chunks(text)
    print(ents)
