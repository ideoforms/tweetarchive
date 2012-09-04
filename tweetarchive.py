#!/usr/bin/python

"""
tweetarchive:
a lightweight python twitter archiver, producing pure ASCII output in CSV format.
requires tweepy, and BeautifulSoup for ASCII/entity conversion.
"""
__version__ = '0.0.1'
__author__ = 'Daniel Jones'
__license__ = 'MIT'


import os
import re
import csv
import sys
import time
import tweepy
import pprint
import getopt
import httplib
import urlparse
import settings
try:
	from BeautifulSoup import BeautifulStoneSoup
except:
	print "couldn't import BeautifulStoneSoup (no ASCII or HTML entity conversion available)"

resolve_shorturl_regexes = map(lambda host: re.compile(r"https?://%s/[\w-]+" % host.replace('.', '\\.')), settings.resolve_shorturls)

def main(args):
	if len(args) > 0:
		settings.archive_username = args[0]
	if "%s" in settings.archive_filename:
		settings.archive_filename = settings.archive_filename % settings.archive_username

	print "archiving to file %s" % settings.archive_filename

	# if we have previous tweets, check the last ID we fetched --
	# only want to pull new ones up to this point.
	settings.archive_last_id = None
	if os.path.exists(settings.archive_filename) and "id" in settings.archive_attributes:
		try:
			fd = open(settings.archive_filename, "r")
			reader = csv.reader(fd)
			row = list(reader)[-1]
			settings.archive_last_id = row[settings.archive_attributes.index("id")]
			print " - existing archive found, seeking up to ID %s" % settings.archive_last_id
			fd.close()
		except:
			pass

	api = twitter_connect()
	statuses = twitter_statuses(api, settings.archive_username, last_id = settings.archive_last_id, wait = settings.wait)

	fd = open(settings.archive_filename, "a")
	writer = csv.writer(fd)
	for status in statuses:
		row = tuple(map(lambda attribute: getattr(status, attribute), settings.archive_attributes))
		writer.writerow(row)
	fd.close()

def twitter_connect():
	""" create our API object via tweepy """
	if settings.consumer_key is not None:
		auth = tweepy.OAuthHandler(settings.consumer_key, settings.consumer_secret)
		auth.set_access_token(settings.oauth_key, settings.oauth_secret)
		api = tweepy.API(auth)
	else:
		api = tweepy.API()

	return api

def twitter_statuses(api, user = "ideoforms", count = float('inf'), last_id = None, wait = 1):
	""" iteratively pull statuses from twitter, up to a limit of <count>.
	    wait <wait> seconds between each page to be a good citizen. """
	page = 1
	statuses = []
	user_info = api.get_user(user)
	statuses_count = user_info.statuses_count
	count = statuses_count if statuses_count < count else count
	print "fetching %d of %d statuses" % (count, statuses_count)
	try:
		while len(statuses) < count:
			try:
				results = api.user_timeline(user, page = page)
			except:
				print " - fetch failed (might have hit request limit, try using oauth settings)"
				break

			if not results:
				break

			print " - got page %d (%d/%d statuses)" % (page, len(statuses) + len(results), statuses_count)

			for status in results:
				# pprint.pprint(vars(status))
				if last_id is not None and str(status.id) == last_id:
					count = 0
					break
				try:
					unescaped = unicode(BeautifulStoneSoup(status.text, convertEntities = BeautifulStoneSoup.HTML_ENTITIES))
					ascii = unescaped.encode('ascii', 'ignore')
					ascii = resolve_urls(ascii)
					status.text_ascii = ascii
				except:
					pass

				statuses.append(status)

			page += 1
			time.sleep(wait)

	except KeyboardInterrupt:
		print "terminated (fetched %d/%d statuses)" % (len(statuses), statuses_count)
		pass

	print "finished (found %d new tweets)" % len(statuses)

	statuses.reverse()
	return statuses

def resolve_urls(string):
	"""Searches a string for URLs on a specific hostname (usually link-shorterning URLs)
	and tries to resolve them, returning a modified string."""
	for re in resolve_shorturl_regexes:
		# find all matches, add each one to the map of urls to resolve as "a":"a"
		while True:
			amatch = re.search(string)
			if not amatch: break
			urlfrm = string[amatch.start():amatch.end()]
			urltoo = urlfrm
			iterdepth = 0
			while any(re.match(urltoo) for re in resolve_shorturl_regexes):
				iterdepth += 1
				if iterdepth == 10:
					print "Warning: too many redirects, giving up resolving %s" % urlfrm
					urltoo = urlfrm
					break
				# resolve the HTTP redirect
				o = urlparse.urlparse(urltoo, allow_fragments=True)
				conn = httplib.HTTPConnection(o.netloc)
				path = o.path
				if o.query:
					path +='?'+o.query
				conn.request("HEAD", path)
				res = conn.getresponse()
				headers = dict(res.getheaders())
				urltoo = headers['location']
			#print "Resolved %s -> %s" % (urlfrm, urltoo)
			string = string.replace(urlfrm, urltoo)
	return string

if __name__ == "__main__":
	""" first, parse command-line arguments """
	args = sys.argv[1:]

	opts, args = getopt.getopt(args, "hu:f:w:")
	for key, value in opts:
		if key == "-h":
			print "Usage: %s [-h] [-u <username>] [-f <filename>] [-w <wait>]" % (sys.argv[0])
			print ""
			print "  -h  show this help"
			print "  -u  username to archive"
			print "  -f  filename to archive to"
			print "  -w  delay time between fetching each page"
			sys.exit(1)
		elif key == "-u":
			settings.archive_username = value
		elif key == "-f":
			settings.archive_filename = value
		elif key == "-w":
			settings.wait = float(value)
	
	main(args)

