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

    else:
        print 'Crawler unknown:', crawler_name
        return

    session = Session()
    crawler(session)


if __name__ == '__main__':
    main()
