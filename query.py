#!/usr/bin/env python
# coding: utf-8
"""Usage: ./query.py [OPTION]... TITLES
Update website by querying ArXiV for papers with TITLES.
Example: ./query.py -F '%Y-%m-%d' 'Delta Scuti Variables'

Options:
    -a, --append         Add another paper to the home page
    -t, --test           Test run, no file changes are made
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
    -h, --help           This message"""

import sys
import os
import json
import getopt
import tarfile

from datetime import datetime, timedelta
import urllib.request as libreq
import feedparser

PAPERS = "papers.js"
OLD_PAPERS_JS = "old_papers.js"
OLD_PAPERS_JSON = "old_papers.json"

SCHEDULE = [2, 4]  # Wednesday and Thursday ISO time


def make_backup():

    backup_name = "papersbackup_{}.tar.gz".format(datetime.today().isoformat())
    with tarfile.open(backup_name, "w") as compressed_backup:
        for filename in (PAPERS, OLD_PAPERS_JS, OLD_PAPERS_JSON):
            if os.path.isfile(filename):
                compressed_backup.add(filename)
    print("Created backup of current papers files in {}".format(backup_name))


def cleanhtml(raw_html):

    cleaned_html = raw_html.translate(
        raw_html.maketrans(
            {"\\": None, "\n": None, "\t": " ", "'": "’", '"': "“"}
        )
    )

    return cleaned_html


def determine_similarity(string1, string2):
    """determine the cosine similarity between strings"""

    char_dicts = ({}, {})
    strings = (string1.upper().split(), string2.upper().split())
    for char_dict, string in zip(char_dicts, strings):
        for word in string:
            if word not in char_dict:
                char_dict[word] = 0
            char_dict[word] += 1

    all_words = sorted(
        list(set(list(char_dicts[0].keys()) + list(char_dicts[1].keys())))
    )
    vectors = [
        [char_dict[word] if word in char_dict else 0 for word in all_words]
        for char_dict in (char_dicts)
    ]
    mags = [sum(v**2 for v in vector) ** 0.5 for vector in vectors]
    similarity = sum(v1 * v2 / (mags[0] * mags[1]) for v1, v2 in zip(*vectors))
    return similarity


def user_select_alternatives(querytitle, feed):

    if len(feed) == 0:
        return None
    titles = [cleanhtml(data.title) for data in feed]
    similarities = [
        determine_similarity(cleanhtml(querytitle), title) for title in titles
    ]
    options = zip(titles, similarities)
    order = sorted(range(len(feed)), key=lambda i: similarities[i])[::-1]
    print(f"Found {len(feed)} Similar Articles:")
    print("{:<6s} | {:<5s} | {:<6s}".format("Index", "Score", "Title"))
    for j, i in enumerate(order):
        print(f"{j:<6d} | {similarities[i]:<1.3f} | {titles[i]:<6s}")
    answer = "."
    while answer.upper() != "Q":
        answer = input(
            "Please select an article index to you instead [0-9/q(uit)]:"
        )
        if answer in map(str, range(10)):
            print(f"You've selected: {titles[order[int(answer)]]}")
            return feed[order[int(answer)]]
    return None


def query(querytitle, share_date, method="ti"):
    """
    method: Search method, see https://arxiv.org/help/api/basics
        default is title
    """
    if method == "ti":
        num_entries = 10
    else:
        num_entries = 0

    queryfixed = querytitle.replace(" ", "+").replace("_", "+AND+ti:")
    base_url = "http://export.arxiv.org/api/query?search_query={}:".format(
        method
    )
    q = base_url + queryfixed + f"&start=0&max_results={num_entries}"
    with libreq.urlopen(q) as url:
        r = url.read()

    feed = feedparser.parse(r)
    assert (
        feed.entries
    ), f"Query failed to find '{querytitle}' using search method '{method}'"
    data = feed.entries[0]

    uncleantitle = data.title
    title = cleanhtml(uncleantitle)

    if method == "ti":  # Verify the title is what was requested
        similarity = determine_similarity(cleanhtml(querytitle), title)
        if similarity < 0.9:
            print(
                "The title returned by the query seems to differ from the title requested"
            )
            print(f" Requested Title: '{cleanhtml(querytitle)}'")
            print(f" Found Title:     '{title}'")
            print(f"Cosine similarity: {similarity:.3f}")
            print("------------------------------------")
            while True:
                response = input(
                    "Would you like to select this article? [Y/n]:"
                )
                if response.upper() == "Y":
                    break
                elif response.upper() == "N":
                    data = user_select_alternatives(
                        querytitle, feed.entries[1:]
                    )
                    if data is None:
                        print("No changes were applied... Exiting")
                        exit(1)
                    else:
                        uncleantitle = data.title
                        title = cleanhtml(uncleantitle)
                        break

    authors = ", ".join(author.name for author in data.authors).replace(
        "'", "’"
    )

    link = data.link

    for link2 in data.links:
        if link2.rel == "alternate":
            pass
        elif link2.title == "pdf":
            pdf = link2.href

    dictionary = {
        "title": title,
        "authors": authors,
        "url": link,
        "pdf": pdf,
        "date": share_date,  # Date queried, not necessarily posted
    }

    return dictionary


def main(titles, share_date, method="ti", test_mode=False, append=False):

    if test_mode:
        print("Running in Test Mode: No Files will be written")

    new_papers = [query(title, share_date, method) for title in titles]

    current_papers = []
    if append:
        with open(PAPERS, "r") as f:
            current_papers = json.loads(
                f.read().strip().lstrip(r"data='").strip(r"'")
            )

    if test_mode:
        print("Sample Output:")
        print(PAPERS)
        print("---------")
        print(json.dumps(new_papers + current_papers).join([r"data='", r"'"]))
        print("---------")
        return 0

    with open(PAPERS, "w") as outfile:
        outfile.write(
            json.dumps(new_papers + current_papers).join([r"data='", r"'"])
        )

    # The following loads and updates the archive json file
    # It's annoying and messy tbh. Python's JSON reader and the html one
    # are using different formats. I keep a file "old_papers.json" that is a
    # cumulative list of all past and current papers. We load and dump to that,
    # then use the updated data to prep "old_papers.js" for the html script.
    # It works but isn't very clean.

    # Make sure to check "old_papers.json" exists.
    all_papers = (
        new_papers  # Build the list of all previous and current papers
    )
    if os.path.isfile(OLD_PAPERS_JSON):  # if old_papers.json exists, append
        with open(OLD_PAPERS_JSON, "r") as f:
            all_papers += json.load(f)

    # write out our new database of old papers
    with open(OLD_PAPERS_JSON, "w") as f_json, open(
        OLD_PAPERS_JS, "w"
    ) as f_js:
        json.dump(all_papers, f_json)
        f_js.write(json.dumps(all_papers).join([r"data='", r"'"]))


if __name__ == "__main__":

    # The last arg is the date it'll be shared.
    # Any format, just a string. "Tu Oct 12" etc is fine.
    # We have to pass the last arg as the date though, or it'll mess up.
    optlist, args = getopt.getopt(
        sys.argv[1:],
        "atbd:m:hF:",
        ["append", "test", "backup", "help", "date=", "format=", "method="],
    )

    method = "ti"
    share_date = None
    test_mode = False
    append = False
    format_string = "%a %b %d, %Y"
    for opt, value in optlist:
        if opt in ("-b", "--backup"):
            make_backup()
            if not args:
                exit(0)
        elif opt in ("-d", "--date"):
            share_date = value
        elif opt in ("-F", "--format"):
            format_string = value
        elif opt in ("-m", "--method"):
            method = value
        elif opt in ("-h", "--help"):
            print(__doc__)
            exit(0)
        elif opt in ("-t", "--test"):
            test_mode = True
        elif opt in ("-a", "--append"):
            append = True

    if share_date is None:
        today = datetime.today() + timedelta(hours=13, minutes=30)
        weekend = 7 - today.weekday()
        next_coffee = min(
            (weekend + SCHEDULE[0]) % 7, (weekend + SCHEDULE[1]) % 7
        )
        share_date = (
            today.replace(hour=10, minute=30, second=0, microsecond=0)
            + timedelta(days=next_coffee)
        ).strftime(format_string)

    titles = args
    assert titles, "Provide 1 or more paper titles"
    main(titles, share_date, method, test_mode, append)
