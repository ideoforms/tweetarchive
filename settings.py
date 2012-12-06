# username to archive
archive_username = "ideoforms"

# use %s in filename to insert twitter username
archive_filename = "%s.csv"

# attributes to archive. the 0th item must always be the tweet ID.
# "text" is the normal UTF-8 text;
# "text_ascii" is an ASCII conversion (requires BeautifulStoneSoup)
archive_attributes = [ "id", "created_at", "retweet_count", "text_ascii" ]

# delay between fetching individual pages of tweets
wait = 2.0
per_page = 50

# include RTs by other people in the archive?
include_rts = True

# short-URLs using the following hostnames will be resolved
# (note that this may make your archived tweets longer than 140 characters).
# to disable, set this to an empty list, i.e. []
resolve_shorturls = [ "t.co", "bit.ly", "bbc.in", "wp.me", "is.gd", "fb.me", "zite.to", "ow.ly", "goo.gl", "deck.ly" ]

# by default, refuse to save partial archive results (after exiting the
# process early) to prevent gaps in archives. 
save_partial = True

# oauth settings
# needed for protected accounts, and to avoid load throttling
# obtain these by creating an application at https://dev.twitter.com/apps
consumer_key = None
consumer_secret = None
oauth_key = None
oauth_secret = None
