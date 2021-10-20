#!/usr/bin/env python
# coding: utf-8


import urllib.request as libreq
import feedparser
import sys
import json
import re
from datetime import date
import os


def cleanhtml(raw_html):
    cleantext = re.sub('\\n', '', raw_html)
    cleaned = re.sub('\\t', ' ', cleantext)
    cleanedmore = re.sub('\"', '“', cleaned)
    cleanedmore = re.sub('\'', '’', cleanedmore)
    return(cleanedmore)

def query(querytitle, share_date):
    queryfixed = querytitle.replace(' ', '+')
    queryfixed = queryfixed.replace('_', '+AND+ti:')
    
    base_url = 'http://export.arxiv.org/api/query?search_query=ti:'
    q = base_url + queryfixed + '&start=0&max_results=1'
    with libreq.urlopen(q) as url:
      r = url.read()
    
    feed = feedparser.parse(r)

    data = feed.entries[0]
    
    uncleantitle = data.title
    title = cleanhtml(uncleantitle)
    
    authorsunclean = (', '.join(author.name for author in data.authors))
    authors = re.sub('\'', '’', authorsunclean)
    
    link = data.link
 
    for link2 in data.links:
        if link2.rel == 'alternate':
            pass
        elif link2.title == 'pdf':
            pdf = link2.href
            
    dictionary = {
    'title'   : title,
    'authors' : authors,
    'url'  : link,
    'pdf'  : pdf,
    'date' : share_date # Date queried, not necessarily posted
    }
    
    
    return(dictionary)




full_list = []

# The last arg is the date it'll be shared.
# Any format, just a string. "Tu Oct 12" etc is fine.
# We have to pass the last arg as the date though, or it'll mess up.
share_date = sys.argv[-1]

for arg in sys.argv[1:-1]:

    title = arg
    query_result = query(title, share_date)
    full_list.append(query_result)

with open('papers.js', 'w') as outfile:
    outfile.write('data=\'')
    json.dump(full_list, outfile)
    outfile.write('\'')
    
# The following loads and updates the archive json file
# It's annoying and messy tbh. Python's JSON reader and the html one
# are using different formats. I keep a file "old_papers.json" that is a 
# cumulative list of all past and current papers. We load and dump to that, 
# then use the updated data to prep "old_papers.js" for the html script. 
# It works but isn't very clean.

# Make sure to check "old_papers.json" exists. 
# If not, dump full_list to it and move on
if not os.path.isfile("old_papers.json"):
    data = full_list
    with open('old_papers.json', 'w') as f:
        json.dump(full_list, f)

# If "old_papers.json" exists, load it, update its data will full_list
# and dump.
else:
    with open('old_papers.json') as f:
        data = json.load(f)

        assert len(full_list)
        for i in range(len(full_list)):
            data.insert(0, full_list[i])
        
    with open('old_papers.json', 'w') as f:
        json.dump(data, f)

# Finally, use "data" to create the ".js" file for the html script.
with open('old_papers.js') as outfile:
    outfile.write('data=\'')
    json.dump(data, outfile)
    outfile.write('\'')
