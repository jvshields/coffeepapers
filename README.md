# coffeepapers

Just run query.py with whatever titles of papers using underscores for spaces (you only need enough of the title to uniquely identify it), with the final argument specifying the date as a string. That script will fetch those papers from arxiv and build a new papers.js, and both old_papers files. Those files are used to build the website located at jvshields.github.io/coffeepapers/

In order to correctly build the website, the workflow should be:
1. Pull the current files (making sure you have the up to date old_papers files). This should be as simple as a git pull.
2. Run query.py with the paper names and your date specified as the last argument.
3. Push your updates files back to github. (git add papers.js old_papers.js old_papers.json, git commit -m 'papers', git push)