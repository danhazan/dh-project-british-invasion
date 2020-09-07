from article_entities_extractor import extract_article_entities
import utils

class Article(object):
    """
    @type article: dict
    """
    def __init__(self, article):
        self.article = article
        # self.reduce()

    def __repr__(self):
        return self["headline"]["main"]

    def __getitem__(self, item):
        return self.article.get(item)

    @property
    def url(self):
        return self["web_url"]

    def reduce(self):
        # del self.article["keywords"]
        del self.article["multimedia"]

    def getText(self):
        return ".\n".join([
            self["abstract"],
            self["snippet"],
            self["headline"]["main"],
            self["headline"]["print_headline"] if self["headline"]["print_headline"] else ""
        ])

    def extract_entities(self):
        utils.i += 1
        ents = "|".join(extract_article_entities(self))
        return '"' + ents.replace('"', '') + '"'

    def get_row(self):
        return [
            self["_id"],
            self["headline"]["main"].replace(",", " "),
            self["pub_date"][:10],
            self["source"],
            self["web_url"],
            self.extract_entities()
        ]
