from datetime import date
from mkopen.crawlers.dksk import crawl_details, save, CATALOG_PREFIX


ARCHIVE = (
  (date(2014, 1, 17), 4988, 'https://web.archive.org/web/20140117212756/http://www.dksk.org.mk/imoti_2/detail.php?detail=4988&search=&ime=%D0%BD%D0%B8%D0%BA%D0%BE%D0%BB%D0%B0&prezime=%D0%B3%D1%80%D1%83%D0%B5%D0%B2%D1%81%D0%BA%D0%B8&funkcija=&institucija=%20http://www.dksk.org.mk/imoti_2/detail.php?detail=4988&search=&ime=%D0%BD%D0%B8%D0%BA%D0%BE%D0%BB%D0%B0&prezime=%D0%B3%D1%80%D1%83%D0%B5%D0%B2%D1%81%D0%BA%D0%B8&funkcija=&institucija='),
  (date(2015, 5, 2), 9230, 'https://web.archive.org/web/20150502151635/http://www.dksk.org.mk/imoti_2/detail.php?detail=9230&search=&ime=&prezime=%D0%B3%D1%80%D1%83%D0%B5%D0%B2%D1%81%D0%BA%D0%B8&funkcija=&institucija='),
  (date(2013, 9, 23), 4969, 'https://web.archive.org/web/20130923225111/http://www.dksk.org.mk/imoti_2/detail.php?detail=4969&search=&ime=%D0%B3%D0%BE%D1%80%D0%B4%D0%B0%D0%BD%D0%B0&prezime=%D1%98%D0%B0%D0%BD%D0%BA%D1%83%D0%BB%D0%BE%D1%81%D0%BA%D0%B0&funkcija=&institucija='),
  (date(2013, 10, 25), 4969, 'https://web.archive.org/web/20131025230555/http://www.dksk.org.mk/imoti_2/detail.php?detail=4969&search=&ime=%D0%B3%D0%BE%D1%80%D0%B4%D0%B0%D0%BD%D0%B0&prezime=%D1%98%D0%B0%D0%BD%D0%BA%D1%83%D0%BB%D0%BE%D1%81%D0%BA%D0%B0&funkcija=&institucija='),
  (date(2013, 11, 26), 4969, 'https://web.archive.org/web/20131126174750/http://www.dksk.org.mk/imoti_2/detail.php?detail=4969&search=&ime=%D0%B3%D0%BE%D1%80%D0%B4%D0%B0%D0%BD%D0%B0&prezime=%D1%98%D0%B0%D0%BD%D0%BA%D1%83%D0%BB%D0%BE%D1%81%D0%BA%D0%B0&funkcija=&institucija='),
  (date(2014, 2, 22), 4969, 'https://web.archive.org/web/20140222112949/http://www.dksk.org.mk/imoti_2/detail.php?detail=4969&search=&ime=%D0%B3%D0%BE%D1%80%D0%B4%D0%B0%D0%BD%D0%B0&prezime=%D1%98%D0%B0%D0%BD%D0%BA%D1%83%D0%BB%D0%BE%D1%81%D0%BA%D0%B0&funkcija=&institucija='),
)

def main(session):
    for date_, detail_id, url in ARCHIVE:
        catalog, csv_content = crawl_details(url)
        catalog = (CATALOG_PREFIX, ) + catalog

        metadata = {'url': "http://www.dksk.org.mk/imoti_2/detail.php?detail=%d" % detail_id,
                    'file_type': 'csv'}

        version = save(session, catalog, csv_content, metadata)

        # reset version date
        version.ref.last_checked = date_
        version.updated = date_
        session.commit()
