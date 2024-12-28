# archive.py

Tool for listing the timemap and jsonmap index files from archive.org.

```
usage: archive.py [-h] [--debug] [--timemap] [--jsonmap] [--from FRM]
                  [--until UNTIL] [--printtime] [--saveto DIR] [--withtime]
                  [--interval INTERVAL] [--noclobber]
                  url

archive.org tool

positional arguments:
  url

options:
  -h, --help            show this help message and exit
  --debug
  --timemap             print timemap for url
  --jsonmap             print jsonmap for url
  --from FRM
  --until UNTIL
  --printtime           print all items from timemap
  --saveto DIR, -s DIR  save all items from jsonmap to this dir
  --withtime            save with time in the path
  --interval INTERVAL   seconds to wait between requests
  --noclobber, -n       dont overwrite existing files
```

example:

    python3 archive.py -s . -n people.ouc.bc.ca/woodcock


# Author

Willem Hengeveld - itsme@xs4all.nl
