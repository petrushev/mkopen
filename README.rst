
Open Data Macedonia
===================

This is a web application serving as a central hub for mirroring any open data published in Macedonia. The main purpose of such hub is permanence, given that in many instances the sources are withdrawn or edited in-place; in such cases the data here is re-published as a copy with a new timestamp. Currently one deployment can be found at:

`data-mkopen.rhcloud.com <https://data-mkopen.rhcloud.com>`_

Requirements
------------

The application is a python flask application running on a postgresql database. See `requirements.txt <https://github.com/petrushev/mkopen/blob/master/requirements.txt>`_ for more information. 

Deployment
----------

The application is configured via system environment variables:

* MKOPEN_STATIC_URL_PATH - root url for static files, defaults to ``'/static'``
* OPENSHIFT_POSTGRESQL_DB_URL - url for database connection, without database name
* PGDATABASE - database name
* GOOGLE_WEBMASTER - code for google webmaster console verifiation

To run locally, use ``run.py``.

To crawl external sources, use ``crawl.py <crawler>``, where ``crawler`` is a name of any script in ``mkopen/crawlers``.
