# Relationships among python, sqlite3 and django versions

I'd developed an website project using django framework. Everything is OK until I migrate it to an old CentOS 6 server. When running unit tests with sqlite3 database (mysql in production), all tests failed with DB operations, which is caused by the following exceptions:

```bash
...
sqlite3.NotSupportedError: URIs not supported

The above exception was the direct cause of the following exception:
...
django.db.utils.NotSupportedError: URIs not supported
```



I searched the web for solutions. 

[Stackoverflow](https://stackoverflow.com/questions/49500117/how-to-fix-error-django-db-utils-notsupportederror-uris-not-supported) said I should modify `/usr/local/lib/python3.7/site-packages/django/db/backends/sqlite3/base.py` and change the `uri` in `kwargs.update({'check_same_thread': False, 'uri': False})` to `False`.  It's indeed a solution, but not elegant enough. It's to disable the `uri` features, what if I want to use an file uri for my database files?

An [django ticket](https://code.djangoproject.com/ticket/28376) said it's not like a a bug in Django, please check the following info:

```bash
>>> import sqlite3
>>> sqlite3.version_info
(2, 6, 0)
>>> sqlite3.sqlite_version_info
(3, 11, 0)
```

I did and got this result:

```bash
>>> import sqlite3
>>> sqlite3.version_info
(2, 6, 0)
>>> sqlite3.sqlite_version_info
(3, 6, 20)
```

According to this result, I shouldn't got this problem, right?

Then I tried many ways to solve this problem, by changing the base python versions and finally I made it, but I still don't know why exactly.



After several months I've got enough spare time to dive into this problem. Here I'll try my best to illustrate this problem for you.



## python vs sqlite3

### What is `sqlite3.version`?

`sqlite3` is an python built in module, which means you can import and use it as long as you've installed  python. It depends on an python extension `_sqlite` written in C. The `sqlite3.version` actually reference to an version macro `PYSQLITE_VERSION` in `_sqlite`.

I've check the commit history, find that it's never been changed since [being committed on 5 Mar 2010](https://github.com/python/cpython/commit/f9cee224461273307ca9f8a0e690a527496534ab), when python was still `v2.6.5rc1` or `v2.7a3`, there's many changes added after the version has been bumped. Therefore, this version value is totally non sense, no much need to check it at all.



### What is `sqlite3.sqlite_version_info`?



The `uri` parameter of `sqlite3.connect()` was added in the `_sqlite` module which was an `cpython` module implemented in `C` by the  [commit on on 10 Feb 2013](https://github.com/python/cpython/commit/902fc8b5a0035cc95f6d849f759577f9d315caaf#diff-affe43c743133796bb0a7eec464483b9).Together an control flag `SQLITE_OPEN_URI` was referenced (see [git blame](https://github.com/python/cpython/blame/13a19139b5e76175bc95294d54afc9425e4f36c9/Modules/_sqlite/connection.c#L110)). Python versions released before 10 Feb 2013 don't have this parameter, and versions after have. These versions can be checked in [python's releases in github repository](https://github.com/python/cpython/releases?after=v2.7.5). Theoretically speaking, for python3, `v3.3.0` and before don't have this parameters, for python2, `v2.6.8` and before don't. Actually, python2 do not have this parameters, for the [latest documentation (currently 2.7.16)](https://docs.python.org/2/library/sqlite3.html#sqlite3.connect) shows no `uri` parameter, indicating that commit may never merge back into python2.

If you call `sqlite3.connect(..., uri=True)` you'd get an `TypeError` in the previous version and you won't got any `sqlite3.NotSupportedError` at all no matter what `sqlite3` version you have installed. 

If you call `sqlite3.connect(..., uri=True)` in the later version, depending on your `libsqlite3` version, you'd either got an `sqlite3.NotSupportedError` or no error.



The control flag `SQLITE_OPEN_URI` was defined in `libsqlite3`, which was used for `sqlite3_open_v2()` only. According to the [release note](https://www.sqlite.org/34to35.html), it was released on sqlite `3.5.0`, indicating that this option is only supported for `sqlite >= 3.5.0`. Therefore, if your `sqlite` version was greater than `3.5.0` and you have an python version support `uri` parameter, you won't get `sqlite3.NotSupportedError`.

However, in my experiments I still got this error. My test environment is:

- CentOS release 6.10 (Final)
- Python 3.4 from EPEL repo
- sqlite 3.6.20 from CentOS repo (system default)

This is my test command:

```bash
python3 -c "
import sqlite3;
print(sqlite3.sqlite_version_info)
sqlite3.connect('db.sqlite3', uri=True)
"
```

And this is my output:

```bash
(3, 6, 20)
Traceback (most recent call last):
  File "<string>", line 4, in <module>
sqlite3.NotSupportedError: URIs not supported
```



That's really weird. But when I dived into the [source code of Python `_sqlite` module](https://github.com/python/cpython/blob/902fc8b5a0035cc95f6d849f759577f9d315caaf/Modules/_sqlite/connection.c#L101) I found that the `SQLITE_OPEN_URI` is not only an control flag, it's also a precompiled macro, which means it took effect when compiling. That's say, if the python was compiled with an older `libsqlite` (before `3.5.0`), it won't support `uri` no matter what the version of sqlite you have installed in your environment.



In summary, the problem was caused by compiling python with sqlite `< 3.5.0`. Most of the python versions released after 5 Mar 2010 with [that commit](https://github.com/python/cpython/commit/f9cee224461273307ca9f8a0e690a527496534ab) and compiled with sqlite `>= 3.5.0` shouldn't got this problem. Some old linux distributions like CentOS 6 mentioned above may had its python compiled with an old sqlite.



To solve this problem, just use another python binary distribution compiled with an newer sqlite.



## django vs sqlite3

There's an django ticket [#28584](https://code.djangoproject.com/ticket/28584) which drop support for sqltie < 3.7.15. According to the disscussion above, we know that's not the fault of the sqlite installed. Therefore, the ticket does not really solve the problem. It just prevents django using sqlite on system like CentOS 6, because the python34 in the EPEL and rh-python36 in the SCL don't support sqlite uri.

Sqlite3 >= 3.5.0 is enough for django, all you need to do is to switch to another python binary distribution compiled with an newer sqlite.

For CentOS 6 users, my recommendation is to use `miniconda3` to manage your python environment.



## TODO

- list unsupported python packages
- find python compiling environment of centos 6




