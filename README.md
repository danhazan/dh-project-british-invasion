# dh-project-british-invasion

This is the source code and data file for the project described in:

https://danhaza.wixsite.com/britishinvasion


What each script does:

dbpedia_collector.py - Collects all the american and british bands from dbpedia.

nytimes_collector.py - Collects all the nytimes articles with subject 'Music', and stores them with their extracted named entities.

data_analyzer.py - Needs the data collected by the two other scripts. Tags and filters the articles and various statistics about the data.


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
