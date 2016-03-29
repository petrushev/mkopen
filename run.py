# run application localy
from os import environ

environ.update({
    'MKOPEN_STATIC_URL_PATH': '//localhost:8000',
    'PGDATABASE': 'opendata',
    'OPENSHIFT_POSTGRESQL_DB_URL': 'postgresql://'
})


from mkopen.app import create_app

if __name__ == '__main__':

    application = create_app()
    application.run('localhost', 8090, True)
