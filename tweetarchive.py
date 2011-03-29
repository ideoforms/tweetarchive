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
import csv
import sys
import time
import tweepy
import pprint
import settings
try:
	from BeautifulSoup import BeautifulStoneSoup
except:
	print "couldn't import BeautifulStoneSoup (no ASCII or HTML entity conversion available)"

def main():
	if len(sys.argv) > 1:
		settings.archive_username = sys.argv[1]
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

if __name__ == "__main__":
	main()

