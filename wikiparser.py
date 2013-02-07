#!/usr/bin/env python
# coding=utf-8
""" Wikiquote api parser, yay """
import re
from quote import Quote

__author__ = 'Wes Lanning'

import sys
from xml.dom import minidom
from urllib import request


# needed to properly fetch pages
USER_AGENT = 'User-agent', 'Mozilla/5.0'

# wiki url related constants
LANG = 'en'
URL = 'Mark Twain'
ARTICLE_URL = 'http://{}.wikiquote.org/w/api.php?format=xml&action=query&titles={}&prop=revisions&rvprop=content'
CAT_URL = 'http://{}.wikiquote.org/w/api.php?format=xml&action=query&titles={}&prop=categories&list=allcategories'

QUOTE_XML_TAG = 'rev'
CAT_XML_TAG = 'cl'
TITLE_TAG = 'page'

XML_HEAD = '<?xml version="1.0" encoding="UTF-8"?>'
XML_ROOT_TOP = '<quotes>'
XML_ROOT_BTM = '</quotes>'


def fetch_page(url: str) -> minidom.Document:
    """
    Fetches a wikiquote page from a url using the wikiquote api
    @param url: the wiki url to fetch from (e.g. U{http://en.wikiquote.org/w/api.php?format=json&action=query&titles=Mark%20Twain&prop=revisions&rvprop=content})
    @return: the xml DOM
    """
    url_opener = request.build_opener()
    url_opener.addheaders = [USER_AGENT]
    infile = url_opener.open(url)
    # gets the the body contents of the file without outer tags
    return minidom.parse(infile)


def format_quote(quote_line:str, id:int, author: str, cats:list) -> Quote:
    """
    Converts a quote string to a quote object
    @param quote_line: the quote string
    @param id: the id for the quote
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
        quote_line = re.sub('[w:]{0,2}\[\[[^|]+\|(?P<name>[^]]+)]]', '\g<name>', quote_line)

        # remove some other crap found in the quotes
    quote_line = re.sub('\[\[|\]\]|<!-- ?| ?-->', '', quote_line)
    quote_line = re.sub('\'{2,3}', '"', quote_line)
    quote_line = re.sub('<br> ?', '\n', quote_line)
    #print(quote_line)
    return Quote(id=id, quote=quote_line, author=author, cats=cats)

def parse_cats_page(xml: minidom.Document, start_tag:str) -> list:
    """
    Read through the page with categories and parse them out
    @param xml:
    @param start_tag: xml tag to start reading elements from
    @return: list of categories
    """

    elements = xml.getElementsByTagName(start_tag)
    categories = []
    filter_list = ['People cleanup', 'Pages with inadequate citations']

    for cat_elem in elements:
        category = cat_elem.getAttribute('title').split(':')[1]

        if category not in filter_list:
            categories.append(category)

    return categories

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
        line = str(line) # stupid intellij can't figure out this is a string without this

        # remove the denotation chars for a quote
        matches = re.match('\* ([\S ]+)', line)

        if matches:
            quotes.append(format_quote(quote_line=matches.group(1), id=i, author=author, cats=cats))
            i += 1


        if line.startswith("{{misattributed"):
            break

    return quotes

def dump_xml(xml_data:list, to_file=False, file_name=''):
    """
    Dumps xml data to stdout or to a file
    @param xml_data: list of xml elements
    @param to_file: if not given, contents dumped to stdout
    @param file_name: if not given, it's taken from xml_data
    """

    if to_file:
        file_name = file_name if file_name else xml_data[0]._author + '.xml'
        file = open(file_name, 'w')
        file.write(XML_HEAD + XML_ROOT_TOP)

        for data in xml_data:
            file.write(data.to_xml())

        file.write(XML_ROOT_BTM)
    else:
        print(XML_HEAD + XML_ROOT_TOP)
        for data in xml_data:
            print(data.to_xml())

        print(XML_ROOT_BTM)


if __name__ == "__main__":

    quote_page = fetch_page(ARTICLE_URL.format(LANG, request.quote(URL)))
    cats_page = fetch_page(CAT_URL.format(LANG, request.quote(URL)))
    cat_list = parse_cats_page(cats_page, CAT_XML_TAG)
    quote_list = parse_quote_page(quote_page, QUOTE_XML_TAG, cat_list)
    dump_xml(quote_list, True)