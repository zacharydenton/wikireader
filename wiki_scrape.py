#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import lxml.html	
import pprint
import argparse
import random
import re
from types import *

def wiki_case(title):
	'''
	converts a list of strings to a wiki-case string

	for example, ['george', 'washington'] becomes 'George_Washington'
	'''
	title = [piece.capitalize() for piece in title]
	return '_'.join(title)

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

def wiki_raw(title):
	'''
	returns an lxml document of the wikipedia page specified by title
	'''
	url = "http://en.wikipedia.org/wiki/" + title

	# change user agent; wikipedia doesn't allow the default one
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]
	article = opener.open(url)

	doc = lxml.html.parse(article).getroot()
	return doc

def wiki_parse(title):
	'''
	parses a wikipedia page specified by title

	returns a dictionary with attributes 'paragraphs' and
	'images'. 'paragraphs' is a list of strings that represents
	all of the paragraphs in the wikipedia article. 'images' contains
	a list of urls for all of the images in the article.
	'''
	if "wikipedia.org" in title:
		title = title.split('/')[-1]
	url = "http://en.wikipedia.org/wiki/" + title

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

def wiki_summary(title, mode='terse'):
	'''
	returns a summary of a wikipedia article
	'''
	article = wiki_parse(title)

	# TODO: check that this is actually an article
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

def wiki_news(mode=''):
	'''
	returns the news on the main page
	'''
	article = wiki_raw("Main_Page")
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

def wiki_didyouknow(mode=''):
	'''
	returns the 'did you know' section on the main page
	'''
	article = wiki_raw("Main_Page")
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

def wiki_today(mode=''):
	'''
	returns the interesting events that occurred on this date
	'''
	article = wiki_raw("Main_Page")
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
	parser.add_argument('-m', '--mode', default='summary', choices=['terse', 'summary', 'full', 'random'])
	action = parser.add_mutually_exclusive_group(required=True)
	action.add_argument('-n', '--news', action='store_true', help="displays the latest headlines")
	action.add_argument('-d', '--didyouknow', action='store_true', help="displays some interesting facts")
	action.add_argument('-t', '--today', action='store_true', help="displays noteworthy events that occurred on this date")
	action.add_argument('article',nargs='*',default='Special:Random',help="the name of the article you want to read")
	args = parser.parse_args()

	if args.news:
		print wiki_news(mode=args.mode)
	elif args.didyouknow:
		print wiki_didyouknow(mode=args.mode)
	elif args.today:
		print wiki_today(mode=args.mode)
	else:
		#article = wiki_search(args.article)
		article = wiki_case(args.article)
		print wiki_summary(article, mode=args.mode)

if __name__ == "__main__":
	main()