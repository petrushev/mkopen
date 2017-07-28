from sys import argv
from os import environ

from mkopen.db.mappers import sessionmaker


Session = sessionmaker(
    {'url': '%s/%s' % (environ['OPENSHIFT_POSTGRESQL_DB_URL'], environ['PGDATABASE']),
     'echo': False})


def main():
    try:
        crawler_name = argv[1]
    except IndexError:
        return

    if crawler_name == 'makstat':
        from mkopen.crawlers.makstat import main as crawler
    elif crawler_name == 'dksk':
        from mkopen.crawlers.dksk import main as crawler
    elif crawler_name == 'aggregate_dksk':
        from mkopen.crawlers.aggregate_dksk import main as crawler
    elif crawler_name == 'opendata':
        from mkopen.crawlers.opendata import main as crawler
    elif crawler_name == 'opendata_ext':
        from mkopen.crawlers.opendata_ext import main as crawler
    elif crawler_name == 'nbrm':
        from mkopen.crawlers.nbrm import main as crawler
    elif crawler_name == 'skopje2014':
        from mkopen.crawlers.skopje2014 import main as crawler
    elif crawler_name == 'archive_dksk':
        from mkopen.crawlers.archive_dksk import main as crawler
    elif crawler_name == 'registry_dksk':
        from mkopen.crawlers.registry_dksk import main as crawler

    else:
        print 'Crawler unknown:', crawler_name
        return

    session = Session()
    crawler(session)


if __name__ == '__main__':
    main()
