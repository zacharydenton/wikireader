#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import lxml.html	
import ConfigParser
import pprint
import argparse
import random
import re
import os
from types import *

def wiki_case(title):
	'''
	converts a list of strings to a wiki-case string

	for example, ['george', 'washington'] becomes 'George_Washington'
	'''
	if isinstance(title, list):
		title = [piece.capitalize() for piece in title]
		return '_'.join(title)
	else:
		return title

def wiki_search(query):
	'''
	use the wikipedia search function to find an article
	'''
	query = '+'.join(query)
	url = 'http://en.wikipedia.org/w/index.php?title=Special:Search&search=' + query

	# change user agent; wikipedia doesn't allow the default one
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]
	result = opener.open(url)

	return result.geturl()

def split_paragraph(paragraph):
	'''
	splits a paragraph into sentences
	'''
	sentenceEnders = re.compile('[.!?]')
	sentenceList = sentenceEnders.split(paragraph)
	# add punctuation
	sentenceList = [sentence + '.' for sentence in sentenceList]
	return sentenceList

def wiki_raw(url, title):
	'''
	returns an lxml document of the wikipedia page specified by title
	'''
	url = url + title

	# change user agent; wikipedia doesn't allow the default one
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]
	article = opener.open(url)

	doc = lxml.html.parse(article).getroot()
	return doc

def wiki_parse(url, title):
	'''
	parses a wiki page specified by title

	returns a dictionary with attributes 'paragraphs' and
	'images'. 'paragraphs' is a list of strings that represents
	all of the paragraphs in the wikipedia article. 'images' contains
	a list of urls for all of the images in the article.
	'''
	if "wikipedia.org" in title:
		title = title.split('/')[-1]
	url = url + title

	# change user agent; wikipedia doesn't allow the default one
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]
	article = opener.open(url)

	doc = lxml.html.parse(article).getroot()
	result = {}

	result['paragraphs'] = []
	for paragraph in doc.cssselect('p'):
		result['paragraphs'].append(paragraph.text_content())

	result['images'] = []
	for image in doc.cssselect('img'):
		result['images'].append(image.get('src'))

	# remove citations [1]
	result['paragraphs'] = [re.sub(r'\[[0-9]+\]', '', paragraph) for paragraph in result['paragraphs']]

	return result

def wiki_read(url, title, mode='terse'):
	'''
	returns a summary of a wikipedia article
	'''
	article = wiki_parse(url, title)

	if "may refer to" in article['paragraphs'][0]:
		if len(article['paragraphs']) > 1:
			mode = 'full'
		else:
			article = wiki_raw(title)
			paragraphs = [p.text_content() for p in article.cssselect('p')]
			headings = [h.text_content() for h in article.cssselect('.mw-headline')]
			return "\n\n".join(paragraphs + headings)

	if mode == 'terse':
		first_paragraph = article['paragraphs'][0]
		first_sentence = split_paragraph(first_paragraph)[0]
		return first_sentence 
	elif mode == 'random':
		return random.choice(article['paragraphs'])
	elif mode == 'summary':
		first_paragraph = article['paragraphs'][0]
		return first_paragraph
	else:
		# display the whole thing
		return '\n\n'.join(article['paragraphs'])

def wiki_news(url, mode=''):
	'''
	returns the news on the main page
	'''
	article = wiki_raw(url, "Main_Page")
	news = article.cssselect('div#mp-itn li')
	
	result = []
	for new in news:
		text = new.text_content()
		# this text is extraneous, so it should be removed
		text = text.replace(u'Wikinews – Recent deaths – More current events...', '')
		text = text.strip()
		result.append(text)

	if mode == 'random':
		return random.choice(result)
	else:
		return '\n\n'.join(result)

def wiki_didyouknow(url, mode=''):
	'''
	returns the 'did you know' section on the main page
	'''
	article = wiki_raw(url, "Main_Page")
	didyouknow = article.cssselect('div#mp-dyk li')
	
	result = []
	for fact in didyouknow:
		text = fact.text_content()
		# this text is extraneous, so it should be removed
		text = text.replace(u'Archive – Start a new article – Nominate an article', '')
		text = text.strip()
		result.append(text)

	if mode == 'random':
		return random.choice(result)
	else:
		return '\n\n'.join(result)

def wiki_today(url, mode=''):
	'''
	returns the interesting events that occurred on this date
	'''
	article = wiki_raw(url, "Main_Page")
	today = article.cssselect('div#mp-otd li')
	
	result = []
	for event in today:
		text = event.text_content()
		text = text.strip()
		result.append(text)

	if mode == 'random':
		return random.choice(result)
	else:
		return '\n\n'.join(result)

def main():
	'''
	main entry point for the program. parses arguments and uses them.
	'''
	
	parser = argparse.ArgumentParser()
	parser.add_argument('-m', '--mode', choices=['terse', 'summary', 'full', 'random'])
	parser.add_argument('-u', '--url', help="change the wiki url to read from (e.g. http://en.wikipedia.org/wiki/)")
	parser.add_argument('-l', '--language', help="change the wikipedia language (e.g. sv)")
	action = parser.add_mutually_exclusive_group(required=False)
	action.add_argument('-n', '--news', action='store_true', help="displays the latest headlines")
	action.add_argument('-d', '--didyouknow', action='store_true', help="displays some interesting facts")
	action.add_argument('-t', '--today', action='store_true', help="displays noteworthy events that occurred on this date")
	action.add_argument('article',nargs='*',default='Special:Random',help="the name of the article you want to read")
	args = parser.parse_args()

	config = ConfigParser.SafeConfigParser()
	configfile = os.path.expanduser("~/.wikireader")
	try:
		open(configfile, 'r') # make sure the configuration file exists
		config.read(configfile)
		if args.mode:
			config.set('Output', 'mode', args.mode)
		if args.url:
			config.set('Source', 'url', args.url)
		if args.language:
			config.set('Source', 'language', args.language)
			config.set('Source', 'url', 'http://%(language)s.wikipedia.org/wiki/')
	except:
		config.add_section('Source')
		config.set('Source', 'language', 'en')
		config.set('Source', 'url', 'http://%(language)s.wikipedia.org/wiki/')
		config.add_section('Output')
		config.set('Output', 'mode', 'summary')
	finally:
		url = config.get('Source', 'url')
		mode = config.get('Output', 'mode')
		with open(configfile, 'wb') as cfile:
			config.write(cfile)
			cfile.close()

	if args.news:
		print wiki_news(url, mode=mode).encode('utf-8')
	elif args.didyouknow:
		print wiki_didyouknow(url, mode=mode).encode('utf-8')
	elif args.today:
		print wiki_today(url, mode=mode).encode('utf-8')
	else:
		#article = wiki_search(args.article)
		article = wiki_case(args.article)
		print wiki_read(url, article, mode=mode).encode('utf-8')

if __name__ == "__main__":
	main()
