from sys import argv
from os import environ

from mkopen.db.mappers import sessionmaker


Session = sessionmaker(
    {'url': 'postgres://%s/%s' % (environ['OPENSHIFT_POSTGRESQL_DB_URL'], environ['PGDATABASE']),
     'echo': False})


def main():
    try:
        crawler_name = argv[1]
    except IndexError:
        return

    if crawler_name == 'makstat':
        from mkopen.crawlers.makstat import main as crawler

    else:
        print 'Crawler unknown:', crawler_name
        return

    session = Session()
    crawler(session)


if __name__ == '__main__':
    main()