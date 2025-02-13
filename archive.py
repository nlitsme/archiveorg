######## WIP ###########
"""
http://www.mementoweb.org/guide/howto/

web.archive.org/web/<data>if_/<url>
  other suffixes:
     id_  ... original
     if_  for iframe document
     fr_  for frame
     cs_  for .css   style
     im_  for images
     js_  for .js    script, worker
     oe_  for video, track, embed, object, audio, font
     mp_  for fetch, "", null, undefined

web.archive.org/web/*/<url>/*
web.archive.org/web/timemap/link/<url>
   '<link>; rel="original";'
   '<link>; rel="timegate";'
   '<link>; rel="self"; type="application/link-format"; from="<date-time>",'
   '<link>; rel="(?:first )?memento";'datetime="<date-time>",'

web.archive.org/web/timemap/json?url=...&....
	url = web.whatsapp.com/
	matchType = prefix
	collapse = urlkey
	output = json
	fl = original,mimetype,timestamp,endtimestamp,groupcount,uniqcount
	filter = !statuscode:[45]..
	from = 2020120410
	to = 2020120410

  [ [...fieldnames...], [...record...], ... ]
  for base url -> all urls for domain

available fields:
   urlkey       nl,eneco)/duurzame-energie/modelcontract
   timestamp    yyyymmddhhmmss
   original     https://www.eneco....
   mimetype     text/html
   statuscode   200
   digest       base32 encoded sha1 hash
   redirect     -
   robotflags   -
   length       numbe
   offset       numbe
   filename     internal-filename

"""
import time
import re
import os
import errno
import urllib.request
import urllib.parse
import http.cookiejar
import json
from datetime import datetime, timezone, timedelta
import binascii


class Archive:
    def __init__(self, args):
        self.args = args
        self.baseurl = "https://web.archive.org"

        handlers = []
        if args.debug:
            handlers.append(urllib.request.HTTPSHandler(debuglevel=1))
        self.opener = urllib.request.build_opener(*handlers)

    def logprint(self, *args):
        if self.args.debug:
            print(*args)

    def httpreq(self, url, data=None):
        """
        Does GET or POST request to 4chan.
        """
        self.logprint(">", url)
        req = urllib.request.Request(url)

        kwargs = {}
        for _ in range(2):
            try:
                response = self.opener.open(req, **kwargs)
                break
            except ConnectionRefusedError:
                time.sleep(5)
                continue
            except urllib.error.HTTPError as e:
                self.logprint("!", str(e))
                response = e
                break

        data = response.read()
        #   links = {}
        #   if link := response.headers.get("link"):
        #       links = self.decode_link_header(link)
        if response.headers.get("content-type", '').find("application/json")>=0:
            js = json.loads(data)
            self.logprint(js)
            self.logprint()
            return js
        self.logprint(data)
        self.logprint()
        return data

    def timemap(self, url):
        m = self.httpreq(f"{self.baseurl}/web/timemap/link/{url}")
        for line in m.decode().split("\n"):
            if m := re.match(r'<(.*?)>; rel="(.*?)"(?:; datetime="(.*?)")?', line):
                yield (m[2], m[1], m[3])

    def jsonmap(self, url, frm=None, unt=None):
        params = {
            "url":url,
            "matchType": "prefix",
            "collapse": "urlkey",
            "output": "json",
            #"fl": "original,mimetype,timestamp,endtimestamp,groupcount,uniqcount",
            "filter": "!statuscode:[345]..",
        }
        if frm: params["from"] = frm
        if unt: params["to"] = unt

        result = self.httpreq(f"{self.baseurl}/web/timemap/json?"+urllib.parse.urlencode(params))
        fieldnames = None
        for rec in result:
            if fieldnames is None:
                fieldnames = rec
            else:
                yield dict(zip(fieldnames, rec))

    def get(self, url):
        url = re.sub(r'web/\d+', lambda m:f"{m[0]}id_", url)
        return self.httpreq(url)

def ensure_dirs(path):
    if path.endswith('/'):
        path += 'index.html'
    base, tail = os.path.split(path)

    cur = '/' if path[0]=='/' else ''
    for p in base.split('/'):
        if len(p) > 250:
            p = md5hex(p)
        cur += p
        if not os.path.exists(cur):
            # path is not yet there -> create subdirectory
            os.mkdir(cur)
        elif not os.path.isdir(cur):
            # when path is there, but not a directory:
            #   rename, create dir, move original to the new subdirectory.
            os.rename(cur, cur+".tempfile")
            os.mkdir(cur)
            os.rename(cur+".tempfile", os.path.join(cur, "index.html"))
        cur += '/'

    return os.path.join(cur, tail)

def get_unique_name(path, checkexists=False):
    # first check if path length is ok, and change to "<md5hex>.md5" style pathname when the max name length is exceeded.
    try:
        os.stat(path+"-xxxxxxxx.http")
    except OSError as e:
        if e.errno == errno.ENAMETOOLONG:
            base, tail = os.path.split(path)
            path = os.path.join(base, md5hex(tail) + ".md5")

    if not os.path.exists(path):
        return path

    if checkexists:
        return

    base, ext = os.path.splitext(path)
    i = 1
    while True:
        path = "%s-%d%s" % (base, i, ext)
        if not os.path.exists(path):
            return path
        i += 1

def is_subdir(basedir, path):
    """
    Make sure path is within basedir
    """
    absbase = os.path.abspath(basedir)
    abspath = os.path.abspath(path)
    return absbase == os.path.commonpath([absbase, abspath])



def main():
    import argparse
    parser = argparse.ArgumentParser(description='archive.org tool')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--timemap', action='store_true', help='print timemap for url')
    parser.add_argument('--jsonmap', action='store_true', help='print jsonmap for url')
    parser.add_argument('--from', dest='frm', type=str)
    parser.add_argument('--until', type=str)
    parser.add_argument('--printtime', action='store_true', help='print all items from timemap')
    parser.add_argument('--saveto', '-s', type=str, help='save all items from jsonmap to this dir', metavar='DIR')
    parser.add_argument('--withtime', action='store_true', help='save with time in the path')
    parser.add_argument('--interval', type=int, help='seconds to wait between requests', default=5)
    parser.add_argument('--noclobber', '-n', action='store_true', help='don''t overwrite existing files')
    parser.add_argument('url', type=str)
    args = parser.parse_args()

    a = Archive(args)

    if args.timemap:
        for m, url, dt in a.timemap(args.url):
            print(f"{m:<20} {dt or '-':<30} {url}")

    if args.jsonmap:
        for ent in a.jsonmap(args.url, args.frm, args.until):
            print(ent)

    if args.printtime:
        for m, url, dt in a.timemap(args.url):
            if m.find('memento')>=0:
                print("==>", url, "<==")
                data = a.get(url)
                print(data.decode())
                print()
                time.sleep(5)

    if args.saveto:
        baseurl = "https://web.archive.org/web"
        for ent in a.jsonmap(args.url, args.frm, args.until):
            url = f"{baseurl}/{ent.get('timestamp')}id_/{ent.get('original')}"
            if args.withtime:
                path = f"{args.saveto}/{ent.get('timestamp')}/{ent.get('original')}"
            else:
                path = f"{args.saveto}/{ent.get('original')}"
            path = ensure_dirs(path)

            path = get_unique_name(path, checkexists=args.noclobber)
            if not path:
                print(f"{ent.get('original')} already there")
                continue

            if not is_subdir(args.saveto, path):
                raise Exception("path tries to escape savedir")

            print(f"saving {ent.get('timestamp')}: {ent.get('original')}")

            with open(path, "wb") as fh:
                data = a.httpreq(url)
                # todo: save x-archive-orig-...  headers to '.http'
                fh.write(data)

                # interval to make sure we don't get ip-blocked
                time.sleep(args.interval)


if __name__ == '__main__':
    main()
