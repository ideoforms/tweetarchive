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

# short-URLs using the following hostnames will be resolved
# (note that this may make your archived tweets longer than 140 characters).
# to disable, set this to an empty list, i.e. []
resolve_shorturls = ["t.co", "bit.ly", "bbc.in", "wp.me", "is.gd"]

# oauth settings
# needed for protected accounts, and to avoid load throttling
consumer_key = None
consumer_secret = None
oauth_key = None
oauth_secret = None
