# coding=utf-8
""" Wikiquote api parser utility functions, yay """
import os
import pickle

__author__ = 'Wes Lanning'

# for dumping the xml to a file or stdout
XML_HEAD = '<?xml version="1.0" encoding="UTF-8"?>'
XML_ROOT_TOP = '<quotes languages="{}">'
XML_ROOT_BTM = '</quotes>'



def sanitize_filename(filename:str) -> str:
    """

    @param filename:
    @return:
    """
    filename = filename.replace('/', '_').replace(' ', '_')
    return filename


def dump_xml(xml_data:list, to_file=False, langs=dict, filename='') -> None:
    """
    Dumps xml data to stdout or to a file
    @param xml_data: list of xml elements
    @param to_file: if not given, contents dumped to stdout
    @param langs: all possible languages for current page
    @param filename: if not given, it's taken from xml_data
    """
    # add all the languages a page can be viewed in to the root xml element
    xml_root_elem = XML_ROOT_TOP.format('|'.join('%s' % k for k, v in langs.items()))

    if to_file:
        filename = filename if filename else xml_data[0] + '.xml'

        # create xml file to dump quotes to
        file = open(filename, 'w')
        file.write(XML_HEAD + xml_root_elem)

        for data in xml_data:
            file.write(data.to_xml())

        file.write(XML_ROOT_BTM)
        file.close()
    else: # dump to stdout/console
        print(XML_HEAD + xml_root_elem)

        for data in xml_data:
            print(data.to_xml())

        print(XML_ROOT_BTM)


def save_foreign_title_ref(new_titles:dict, filename:str):
    """
    Map xx/author-name-in-foreign-language.xml to en/author-name.xml
    Does this by creating a file of key:value pairs in each language dir

    @param new_titles: dictionary with iso language -> name pairs
    @param filename: where the references for this language are stored (e.g. quotes/languages/english_page_tile.pkl)
    """

    language_ref = {}

    if os.path.exists(filename):
        language_ref = pickle.load(open(filename, 'rb'))

    for lang, title in new_titles.items():
        language_ref[lang] = title

    with open(filename, 'wb') as output_file:
        pickle.dump(language_ref, output_file)
