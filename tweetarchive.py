#!/usr/bin/python

"""
tweetarchive:
a lightweight python twitter archiver, producing pure ASCII output in CSV format.
requires python-twitter-tools, and BeautifulSoup for ASCII/entity conversion.
"""
__version__ = '0.0.1'
__author__ = 'Daniel Jones'
__license__ = 'MIT'


import os
import re
import csv
import sys
import time
import pprint
import getopt
import httplib
import twitter
import urlparse
import settings
import email.utils 

try:
	from BeautifulSoup import BeautifulStoneSoup
except:
	print "couldn't import BeautifulStoneSoup (no ASCII or HTML entity conversion available)"
	sys.exit(1)

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
	settings.archive_count = 0
	if os.path.exists(settings.archive_filename) and "id" in settings.archive_attributes:
		try:
			fd = open(settings.archive_filename, "r")
			reader = csv.reader(fd)
			lines = list(reader)
			row = lines[-1]
			settings.archive_count = len(lines)
			settings.archive_last_id = row[settings.archive_attributes.index("id")]
			print "existing archive found, seeking up to ID %s" % settings.archive_last_id
			fd.close()
		except:
			pass

	api = twitter_connect()
	statuses = twitter_statuses(api, settings.archive_username, min_id = settings.archive_last_id, wait = settings.wait, histsize = settings.archive_count)

	fd = open(settings.archive_filename, "a")
	writer = csv.writer(fd)
	for status in statuses:
		row = tuple(map(lambda attribute: status[attribute], settings.archive_attributes))
		writer.writerow(row)

	fd.close()

def twitter_connect():
	""" create our API object via python-twitter-tools,
	    authenticating with oAuth if necessary. """
	if settings.consumer_key is not None:
		auth = twitter.OAuth(settings.oauth_key, settings.oauth_secret, settings.consumer_key, settings.consumer_secret)
		api = twitter.Twitter(auth = auth)
	else:
		api = twitter.Twitter()

	return api

def twitter_statuses(api, username = "ideoforms", histsize = 0, min_id = None, wait = 1):
	""" Iteratively pull statuses from twitter, up to a limit of <count>.
	    Wait <wait> seconds between each page to be a good citizen. """

	page = 1
	last_id = None
	statuses = []
	user_info = api.users.show(screen_name = username)
	total_count = user_info["statuses_count"]
	fetch_count = total_count - histsize
	print "fetching %d of %d statuses" % (fetch_count, total_count)

	try:
		found_last = False
		while len(statuses) < fetch_count:
			try:
				if last_id:
					results = api.statuses.user_timeline(screen_name = username, count = settings.per_page, include_rts = settings.include_rts, max_id = last_id - 1)
				else:
					results = api.statuses.user_timeline(screen_name = username, count = settings.per_page, include_rts = settings.include_rts)
			except:
				print " - fetch failed (might have hit request limit, try using oauth settings)"
				break

			if not results:
				print " - no results (not sure why)"
				time.sleep(2)

			cumulative_count = len(statuses) + len(results)
			if cumulative_count > fetch_count:
				cumulative_count = fetch_count
			print " - got page %d (%d/%d statuses)" % (page, cumulative_count, fetch_count)
			page += 1

			for status in results:
				if min_id is not None and str(status["id"]) == min_id:
					found_last = True
					break

				try:
					unescaped = unicode(BeautifulStoneSoup(status["text"], convertEntities = BeautifulStoneSoup.HTML_ENTITIES))
					ascii = unescaped.encode('ascii', 'ignore')
					ascii = ascii.replace("\n", " ")
					ascii = resolve_urls(ascii)
					status["text_ascii"] = ascii
				except Exception, e:
					print "couldn't parse tweet: %s (%s)" % (status["text"], e)
					pass

				# parse ISO-8601 date
				timestamp = email.utils.parsedate(status["created_at"])
				status["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S", timestamp)

				if settings.verbose:
					print "%d (%s) %s" % (status["id"], status["created_at"], status["text_ascii"])

				last_id = status["id"]
				statuses.append(status)

			if found_last:
				break

			time.sleep(wait)

	except KeyboardInterrupt:
		print "terminated (fetched %d/%d statuses)" % (len(statuses), fetch_count)
		if not settings.save_partial:
			print "(not saving to disk to avoid gaps in archive)"
			sys.exit(1)

	print "finished (found %d new tweets)" % len(statuses)

	statuses.reverse()
	return statuses

def resolve_urls(string):
	""" Searches a string for URLs on a specific hostname (usually link-shorterning URLs)
	    and tries to resolve them, returning a modified string. """
	for re in resolve_shorturl_regexes:
		try:
			while True:
				amatch = re.search(string)
				if not amatch:
					break

				urlfrm = string[amatch.start():amatch.end()]
				urltoo = urlfrm
				iterdepth = 0
				while any(re.match(urltoo) for re in resolve_shorturl_regexes):
					iterdepth += 1
					if iterdepth == 10:
						print "Warning: too many redirects, giving up resolving %s" % urlfrm
						return string

					# resolve the HTTP redirect
					o = urlparse.urlparse(urltoo, allow_fragments = True)
					conn = httplib.HTTPConnection(o.netloc)
					path = o.path
					if o.query:
						path += '?' + o.query
					conn.request("HEAD", path)
					res = conn.getresponse()
					headers = dict(res.getheaders())
					urltoo = headers['location']

				# print "Resolved %s -> %s" % (urlfrm, urltoo)
				string = string.replace(urlfrm, urltoo)
		except:
			# possible error resolving URL; leave it as is
			pass

	return string

if __name__ == "__main__":
	""" first, parse command-line arguments """
	args = sys.argv[1:]

	opts, args = getopt.getopt(args, "hvu:f:w:")
	for key, value in opts:
		if key == "-h":
			print "Usage: %s [-hv] [-u <username>] [-f <filename>] [-w <wait>]" % (sys.argv[0])
			print ""
			print "  -v  verbose output"
			print "  -h  show this help"
			print "  -u  username to archive"
			print "  -f  filename to archive to"
			print "  -w  delay time between fetching each page"
			sys.exit(1)
		elif key == "-v":
			settings.verbose = True
		elif key == "-u":
			settings.archive_username = value
		elif key == "-f":
			settings.archive_filename = value
		elif key == "-w":
			settings.wait = float(value)

	if not hasattr(settings, "wait_time"):
		settings.wait = 2.0
	if not hasattr(settings, "per_page"):
		settings.per_page = 50
	if not hasattr(settings, "include_rts"):
		settings.include_rts = True
	if not hasattr(settings, "verbose"):
		settings.verbose = False
	if not hasattr(settings, "save_partial"):
		settings.save_partial = False
	
	main(args)

