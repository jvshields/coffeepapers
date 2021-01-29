#!/usr/bin/env python
# coding: utf-8


import urllib.request as libreq
import feedparser
import sys
import json
import re


def cleanhtml(raw_html):
    cleantext = re.sub('\\n', '', raw_html)
    cleaned = re.sub('\\t', ' ', cleantext)
    return(cleaned)

def query(querytitle):
    queryfixed = querytitle.replace(' ', '+')
    queryfixed = queryfixed.replace('_', '+')
    
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
    'title' : title,
    'authors' : authors,
    'url' : link,
    'pdf' : pdf
    }
    
    
    return(dictionary)




full_list = []

for arg in sys.argv[1:]:

    title = arg
    query_result = query(title)
    full_list.append(query_result)
    
with open('papers.js', 'w') as outfile:
    outfile.write('data=\'')
    json.dump(full_list, outfile)
    outfile.write('\'')
    






