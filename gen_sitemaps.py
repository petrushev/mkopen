from os import environ
from os.path import join as path_join
from os.path import dirname

from sqlalchemy.sql.expression import func
from lxml.etree import Element, SubElement
from lxml.etree import tostring as xml_to_string

from mkopen.db.mappers import sessionmaker
from mkopen.db.models import Data
from werkzeug.urls import url_quote


SITEMAP_PATH = path_join(dirname(__file__), 'wsgi', 'static')

Session = sessionmaker(
    {'url': '%s/%s' % (environ['OPENSHIFT_POSTGRESQL_DB_URL'], environ['PGDATABASE']),
     'echo': False})


def main():
    session = Session()

    doc = Element("urlset", {"xmlns":"http://www.sitemaps.org/schemas/sitemap/0.9"})

    len_ = func.array_length(Data.catalog_id, 1)
    q = session.query((Data.catalog_id[ 1 : len_ - 1 ]).distinct()).all()

    for row in q:
        catalog_param = '/'.join(row[0])
        url_xml = SubElement(doc, "url")
        SubElement(url_xml, 'loc').text = \
           'https://%s/search?catalog=%s' % (environ['OPENSHIFT_APP_DNS'],
                                             url_quote(catalog_param))
        SubElement(url_xml, 'changefreq').text = 'weekly'
        SubElement(url_xml, 'priority').text = '0.9'

    with open(path_join(SITEMAP_PATH, 'catalog.xml'), 'wb') as f:
        f.write(xml_to_string(doc, encoding='utf-8', pretty_print=True))


if __name__ == '__main__':
    main()
