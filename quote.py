#!/usr/bin/env python
# coding=utf-8
""" Wikiquote api parser, yay """

__author__ = 'Wes Lanning'

import json
from xml.sax.saxutils import escape

from util import xml_escape


class Quote:
    """ Holds info related to a quote object
    """

    ref = ''

    _id = 0
    _author = ''
    _quote = ''
    _cats = []

    XML = '<quote id="{}" author="{}" cats="{}" ref="{}">{}</quote>'

    def __init__(self, ident: int, quote: str, author: str, cats: list, ref=''):
        """
        Initialize a new quote object to hold the data that is parsed from a source

        @param ident: the server side id of the quote
        @param quote: the quote snippet parsed from source
        @param author: author of the quote
        @param cats: categories the quote belongs in
        @param ref: reference/summary snippet about the quote
        @return: self
        """
        self._id = ident
        self._quote = quote
        self._author = author
        self._cats = cats
        self.ref = ref

    def to_xml(self, xml_skeleton=XML) -> str:
        """
        Converts the quote to xml

        @param xml_skeleton: template to how the xml should map to the data.
         Example: <quote id="{}" author="{}" cats="{}" ref="{}">{}</quote>
        @return: xml string with data formatted in it
        """
        return xml_skeleton.format(self._id, xml_escape(self._author),
                                   escape('|'.join(self._cats)), xml_escape(self.ref), xml_escape(self._quote))

    def to_json(self) -> str:
        return json.dumps({'id': self._id, 'author': self._author, 'cats': '|'.join(self._cats), 'ref': self.ref,
                           'quote': self._quote})
