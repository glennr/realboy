== Project RealBoy ==
by Greg Marra and Zack Coburn

= Setup =

1. Create and fill in db.txt, realboys.txt, and logins.txt. See db.txt.tmlp, realboys.txt.tmpl, and logins.txt.tmpl for examples.

2. Run the following commands:

python run_once.py
python friend_finder.py -s gregmarra
python twitter_friend_graph.py
python realboy.py

3. You may want to set up realboy.py to run with cron. crontab.txt.tmpl is an example crontab file.
