#!/usr/bin/env python
# coding=utf-8
""" Wikiquote api parser, yay """
__author__ = 'Wes Lanning'

import os
import re
from quote import Quote
import argparse
from xml.dom import minidom
from urllib import request
from urllib import parse


# needed to properly fetch pages
USER_AGENT = 'User-agent', 'Mozilla/5.0'

QUOTE_DIR = 'quotes'

# wiki url related constants
DEFAULT_LANG = 'en' # language to fetch from
DEFAULT_PAGE = 'Mark Twain' # title of the page to fetch from. Wiki Titles are capitalized
ARTICLE_URL = 'http://{}.wikiquote.org/w/api.php?format=xml&action=query&titles={}&prop=revisions&rvprop=content'
CAT_URL = 'http://{}.wikiquote.org/w/api.php?format=xml&action=query&titles={}&prop=categories&list=allcategories'
LANG_URL = 'http://{}.wikiquote.org/w/api.php?format=xml&action=query&titles={}&prop=langlinks&lllimit=500'

# each tells the parser where to start looking for data in the xml tags
QUOTE_TAG = 'rev' # where to start looking for quotes
CAT_TAG = 'cl' # where to grab the categories for the quotes
LANG_TAG = 'll' # where to grab the possible languages for the quotes
TITLE_TAG = 'page' # where to fetch the author/title of the page

# for dumping the xml to a file or stdout
XML_HEAD = '<?xml version="1.0" encoding="UTF-8"?>'
XML_ROOT_TOP = '<quotes>'
XML_ROOT_BTM = '</quotes>'

def cmd_line_parse() -> argparse.Namespace:
    """
    Parses the command line args
    @return: the parsed args namespace
    """

    parser = argparse.ArgumentParser(description='Parse a wikiquote URL')
    parser.add_argument('--file', dest='filename', metavar='FILE', help='Dump to file instead of stdout. usage [optional]: filename.xml')
    parser.add_argument('--url', metavar='URL', dest='url_title', help='usage [optional]: "Mark Twain"')
    parser.add_argument('--language', metavar='LANG', dest='language', help='usage [optional]: en')
    return parser.parse_args()

def fetch_page(url: str) -> minidom.Document:
    """
    Fetches a wikiquote page from a url using the wikiquote api
    @param url: the wiki url to fetch from
    @return: the xml DOM
    """
    url_opener = request.build_opener()
    url_opener.addheaders = [USER_AGENT]
    infile = url_opener.open(url)
    # gets the the body contents of the file without outer tags
    return minidom.parse(infile)

def format_quote(quote_line:str, quote_id:int, author:str, cats:list) -> Quote:
    """
    Converts a quote string to a quote object
    @param quote_line: the quote string
    @param quote_id: the id for the quote
    @param author: the quote author
    @param cats: list of categories the quotes fall under
    @return: a Quote object
    """
    # TODO: group the regexs below into one with backreferences (maybe)
    # also, this should work, but doesn't because of the white space, so workaround is to remove white space
    # and use the uncommented blob >:(
    # quote_line = re.sub(r"""[w:]{0,2}           # optionally look for w:
    #                        \[\[[^|]+            # ditch all chars from \[\[ up to \|
    #                        \|(?P<name>[^\]]+)]] # stop at \| and capture this part""", '\g<name>', matches.group(1))

    if quote_line.find('[['): # expensive to do regex below so avoid if possible
        # convert crap like [Ulysses S. Grant|Grant] to Grant or [w:Philip Sheridan|Sheridan] to Sheridan
        quote_line = re.sub('[w:]{0,2}\[\[[^|]+\|(?P<name>[^]]+)]]', '\g<name>', quote_line)

    # remove some other crap found in the quotes
    quote_line = re.sub('\[\[|\]\]|<!-- ?| ?-->', '', quote_line)
    quote_line = re.sub('"{2,}|\'{2,3}', '"', quote_line)
    quote_line = re.sub('<br> ?', '\n', quote_line)

    return Quote(id=quote_id, quote=quote_line, author=author, cats=cats)

def parse_cats_page(xml: minidom.Document, start_tag:str) -> list:
    """
    Read through the page with categories and parse them out
    @param xml: the xml dom object
    @param start_tag: xml tag to start reading elements from
    @return: list of categories
    """

    elements = xml.getElementsByTagName(start_tag)
    categories = []
    # categories only useful to wikipedia. Filter them out.
    filter_list = ['People cleanup', 'Pages with inadequate citations', 'Pages with broken file links', 'Articles with unsourced statements']

    for cat_elem in elements:
        category = cat_elem.getAttribute('title').split(':')[1]

        if category not in filter_list:
            categories.append(category)

    return categories


def parse_lang_page(xml: minidom.Document, start_tag:str) -> dict:

    """
    Grabs all the various languages a page is translated to.
    @param xml:
    @param start_tag:
    @return: dict of language keys and author name as value in iso formatting (e.g. af, ar, da, etc)
    """
    elements = xml.getElementsByTagName(start_tag)
    languages = {}

    for lang_elem in elements:
        languages[lang_elem.getAttribute('lang')] = lang_elem.firstChild.nodeValue

    return languages

def parse_quote_page(xml: minidom.Document, start_tag:str, cats: list, title_tag=TITLE_TAG) -> list:
    """
    Reads through the page with quotes and parses them out
    @param xml: the xml node list to parse
    @param start_tag: xml tag to start reading elements from
    @param cats: category list for the quotes on this page
    @param title_tag: tag to parse the page title from
    @return: list of quote objects
    """

    quote_area = xml.getElementsByTagName(start_tag)
    title_elem = minidom.NodeList(xml.getElementsByTagName(title_tag))
    author = title_elem.item(0).getAttribute('title')
    page_data = quote_area[0].firstChild.data.split('\n')

    i = 0
    quotes = []

    for line in page_data:
        # remove the denotation chars for a quote
        matches = re.match('\* ([\S ]+)', line)

        if matches:
            quotes.append(format_quote(quote_line=matches.group(1), quote_id=i, author=author, cats=cats))
            i += 1

        if re.match('\{\{misattributed|\{\{disputed', line, re.IGNORECASE):
            break # don't care about getting anything in misattributed and below

    return quotes

def dump_xml(xml_data:list, to_file=False, file_name='') -> None:
    """
    Dumps xml data to stdout or to a file
    @param xml_data: list of xml elements
    @param to_file: if not given, contents dumped to stdout
    @param file_name: if not given, it's taken from xml_data
    """

    if to_file:
        file_name = file_name if file_name else xml_data[0]._author.replace(' ', '_') + '.xml'
        file = open(file_name, 'w')
        file.write(XML_HEAD + XML_ROOT_TOP)

        for data in xml_data:
            file.write(data.to_xml())

        file.write(XML_ROOT_BTM)
    else: # dump to stdout/console
        print(XML_HEAD + XML_ROOT_TOP)

        for data in xml_data:
            print(data.to_xml())

        print(XML_ROOT_BTM)

if __name__ == "__main__":

    args = cmd_line_parse()
    filename = ''
    to_file = True

    if args.filename:
        filename = args.filename
        to_file = True
    if args.language:
        DEFAULT_LANG = args.language
    if args.url_title:
        DEFAULT_PAGE = args.url_title
    # default dir for quotes to go to
    if not os.path.exists(QUOTE_DIR):
        os.makedirs(QUOTE_DIR)

    # fetch all possible languages first
    lang_page = fetch_page(LANG_URL.format(DEFAULT_LANG, request.quote(DEFAULT_PAGE)))
    lang_dict = parse_lang_page(lang_page, LANG_TAG)
    lang_dict['en'] = DEFAULT_PAGE

    for lang, page_title in lang_dict.items():
        default_dir = '{}/{}'.format(QUOTE_DIR, lang)
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)

        quote_page = fetch_page(ARTICLE_URL.format(lang, request.quote(page_title)))
        cats_page = fetch_page(CAT_URL.format(lang, request.quote(page_title)))

        cat_list = parse_cats_page(cats_page, CAT_TAG)
        quote_list = parse_quote_page(quote_page, QUOTE_TAG, cat_list)

        if quote_list:
            dump_xml(quote_list, to_file, '{}/{}.xml'.format(default_dir, page_title))

    #print(lang_list)


