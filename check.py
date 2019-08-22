import os
from sqlite3 import dbapi2 as Database

dbname = 'db.sqlite3'

try:
    Database.connect(dbname, uri=True)
    print('URIs supported')
except Database.NotSupportedError:
    print('URIs not supported')
except TypeError:
    print('uri is an invalid kwarg')
finally:
    if os.path.isfile(dbname):
        os.unlink(dbname)
