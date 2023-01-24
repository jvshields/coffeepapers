#!/usr/bin/env python
# coding: utf-8
'''Usage: ./query.py [OPTION]... TITLES
Update website by querying ArXiV for papers with TITLES.
Example: ./query.py -F '%Y-%m-%d' 'Delta Scuti Variables'

Options:
    -b, --backup         Create backup of current data files
    -d, --date=DATE      Set the date as the string DATE
                         default is next Tuesday or Thursday
    -F, --format=FORMAT  Use FORMAT as the datetime format       
    -m, --method=METHOD  Search ArXiV by METHOD
                         Options include the following:
                           ti: Title (default)
                           au: Author
                           abs: Abstract
                           co: Comment
                           jr: Journal Reference
                           cat: Subject Category
                           rn: Report Number
                           id: Id
                           all: All of the above
    -h, --help           This message'''

import sys
import os
import json
import getopt
import tarfile

from datetime import datetime, timedelta
import urllib.request as libreq
import feedparser

PAPERS = 'papers.js'
OLD_PAPERS_JS = 'old_papers.js'
OLD_PAPERS_JSON = 'old_papers.json'

def make_backup():

    backup_name = 'papersbackup_{}.tar.gz'.format(datetime.today().isoformat())
    with tarfile.open(backup_name, 'w') as compressed_backup:
        for filename in (PAPERS, OLD_PAPERS_JS, OLD_PAPERS_JSON):
            if os.path.isfile(filename):
                compressed_backup.add(filename)
    print('Created backup of current papers files in {}'.format(backup_name))

def cleanhtml(raw_html):

    cleaned_html = raw_html.translate(
            raw_html.maketrans({
                    '\\': None,
                    '\n': None, 
                    '\t': ' ', 
                    '\'': '’',
                    '\"': '“'
                    })
            )

    return cleaned_html

def query(querytitle, share_date, method='ti'):
    '''
        method: Search method, see https://arxiv.org/help/api/basics
            default is title
    '''

    queryfixed = querytitle.replace(' ', '+').replace('_', '+AND+ti:')
    base_url = 'http://export.arxiv.org/api/query?search_query={}:'.format(
            method)
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


def main(titles, share_date, method='ti'):

    new_papers = [query(title, share_date, method) for title in titles]


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




if __name__ == '__main__':

    # The last arg is the date it'll be shared.
    # Any format, just a string. "Tu Oct 12" etc is fine.
    # We have to pass the last arg as the date though, or it'll mess up.
    optlist, args = getopt.getopt(
            sys.argv[1:], 
            'bdm:hF:', 
            ['backup', 'help', 'date=', 'format=', 'method=']
            )

    method = 'ti'
    share_date = None
    format_string = '%a %b %d'
    for opt, value in optlist:
        if opt in ('-b', '--backup'):
            make_backup()
            if not args: exit(0)
        elif opt in ('-d', '--date'):
            share_date = value 
        elif opt in ('-F', '--format'):
            format_string = value
        elif opt in ('-m', '--method'):
            method = value
        elif opt in ('-h', '--help'):
            print(__doc__)
            exit(0)
    
    if share_date is None:
        today = datetime.today() + timedelta(hours=13, minutes=0)
        weekend = 7 - today.weekday()
        next_coffee = min((weekend + 2) % 7, (weekend + 4) % 7)
        share_date = (today.replace(
            hour=11, 
            minute=0, 
            second=0,
            microsecond=0
            ) + timedelta(days=next_coffee)).strftime(format_string)


    titles = args
    assert titles, "Provide 1 or more paper titles"
    main(titles, share_date, method)

