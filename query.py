#!/usr/bin/env python
# coding: utf-8

import sys
import os
import json
import feedparser
import urllib.request as libreq

def cleanhtml(raw_html):

    cleaned_html = raw_html.translate(
            raw_html.maketrans({
                    '\n': None, 
                    '\t': ' ', 
                    '\'': '’',
                    '\"': '“'
                    })
            )

    return cleaned_html

def query(querytitle, share_date):

    queryfixed = querytitle.replace(' ', '+').replace('_', '+AND+ti:')
    
    base_url = 'http://export.arxiv.org/api/query?search_query=ti:'
    q = base_url + queryfixed + '&start=0&max_results=1'
    with libreq.urlopen(q) as url:
      r = url.read()
    
    feed = feedparser.parse(r)

    data = feed.entries[0]
    
    uncleantitle = data.title
    title = cleanhtml(uncleantitle)
    
    authors = ', '.join(
            author.name for author in data.authors
            ).replace('\'', '’')
    
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
    
    
    return dictionary



if __name__ == '__main__':

    # The last arg is the date it'll be shared.
    # Any format, just a string. "Tu Oct 12" etc is fine.
    # We have to pass the last arg as the date though, or it'll mess up.
    *titles, share_date = sys.argv[1:]
    assert titles, "Provide 1 or more paper titles followed by a time string"
    new_papers = [query(title, share_date) for title in titles]


    with open('papers.js', 'w') as outfile:
        outfile.write(json.dumps(new_papers).join([r"data='", r"'"]))
        
    # The following loads and updates the archive json file
    # It's annoying and messy tbh. Python's JSON reader and the html one
    # are using different formats. I keep a file "old_papers.json" that is a 
    # cumulative list of all past and current papers. We load and dump to that, 
    # then use the updated data to prep "old_papers.js" for the html script. 
    # It works but isn't very clean.

    # Make sure to check "old_papers.json" exists. 
    all_papers = new_papers # Build the list of all previous and current papers
    if os.path.isfile("old_papers.json"): # if old_papers.json exists, append 
         with open('old_papers.json', 'r') as f:
            all_papers += json.load(f)
        
    # write out our new database of old papers
    with open('old_papers.json', 'w') as f_json, open('old_papers.js', 'w') as f_js:
        json.dump(all_papers, f_json)
        f_js.write(json.dumps(all_papers).join([r"data='", r"'"]))

