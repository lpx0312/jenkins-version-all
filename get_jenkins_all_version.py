#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import json
import argparse
import datetime

try:
    # Python3
    from urllib.request import Request, urlopen, ProxyHandler, build_opener
except ImportError:
    # Python2
    from urllib2 import Request, urlopen, ProxyHandler, build_opener


API = "https://api.github.com/repos/jenkinsci/jenkins/releases"
OUTPUT_FILE = "jenkins-all-version.json"


def build_opener_with_proxy(proxy):
    if not proxy:
        return None
    proxy_handler = ProxyHandler({
        "http": proxy,
        "https": proxy
    })
    return build_opener(proxy_handler)


def fetch_page(url, token=None, opener=None):
    req = Request(url)
    req.add_header("User-Agent", "jenkins-version-fetcher")

    if token:
        req.add_header("Authorization", "token %s" % token)

    if opener:
        resp = opener.open(req)
    else:
        resp = urlopen(req)

    data = resp.read()
    if not isinstance(data, str):
        data = data.decode("utf-8")

    return json.loads(data)


def format_date(iso_time):
    dt = datetime.datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="Fetch all Jenkins versions with release date")
    parser.add_argument("-p", "--proxy", help="Proxy (e.g. http://127.0.0.1:7890)")
    parser.add_argument("-t", "--token", help="GitHub Token")

    args = parser.parse_args()

    opener = build_opener_with_proxy(args.proxy)

    page = 1
    result = {}

    print("[INFO] Fetching Jenkins releases...")

    while True:
        url = "%s?per_page=100&page=%d" % (API, page)

        try:
            data = fetch_page(url, token=args.token, opener=opener)
        except Exception as e:
            print("[ERROR]", e)
            sys.exit(1)

        if not data:
            break

        for r in data:
            tag = r.get("tag_name", "")
            pub = r.get("published_at", "")

            if tag.startswith("jenkins-") and pub:
                version = tag.replace("jenkins-", "")
                result[version] = format_date(pub)

        page += 1

    # 写入文件
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)

    print("[SUCCESS] Saved to %s" % OUTPUT_FILE)
    print("[INFO] Total versions:", len(result))


if __name__ == "__main__":
    main()