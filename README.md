# dh-project-british-invasion

This repo contains the source code and data files for the project that is presented [here](
https://danhaza.wixsite.com/britishinvasion) (in hebrew).

This project includes the usage of NLP tools for deep analysis of news articles, collected using the NYT api and boilerpipe, as well as the collection of data from DBPedia using SPARQL queries. 



<br/><br/>


About the code:

dbpedia_collector.py - Collects all the american and british bands from dbpedia.

nytimes_collector.py - Collects all the nytimes articles with subject 'Music' between 1955-2020, and stores them with their extracted named entities.

data_analyzer.py - Needs the data collected by the two other scripts. Tags and filters the articles and produces various statistics about the data.

pynytimes2 - A modification of the pynytimes library, that uses python generators to allow a more dynamic collection of the articles metadata.

<br/><br/>


About the data files:

articles.csv - All the 100,000+ articles collected on the subject "Music", along with their named entities.

articles_tagged.csv - The filtered and tagged articles, with the bands and genres mentioned.

articles_expanded.csv - Articles statistics, apears on the lower graph.


bands_american.csv - All of the the american rock bands.

bands_american_expanded.csv - American rock bands statistics, appears on the upper graph.

bands_american_years.csv - American bands founded by year.

bands_british.csv - All of the the british rock bands.

bands_stats.csv - British rock bands with the number of articles mentioning them.


genres.csv - All of the rock subgenres and fusion genres.
