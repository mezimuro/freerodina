#!/usr/bin/env python
# -*- coding: utf-8 -*-

from freerodina.core import *


""" Classes """

# really simple HTTP client which can save and maintain client state
class NanoHTTPClient:
    def __init__(self):
        self.http_session = requests.Session()
        self.http_session.headers.update(g_data['basic_http_headers'])
        self.Reset()

    def Get(self, url):
        r = self.http_session.get(url, timeout=REQUESTS_DEFAULT_TIMEOUT, verify=not DISABLE_SSL_VERIFICATION)
        r.raise_for_status()
        return r

    def GetSoup(self, url):
        r = self.http_session.get(url, timeout=REQUESTS_DEFAULT_TIMEOUT, verify=not DISABLE_SSL_VERIFICATION)
        r.raise_for_status()
        return BeautifulSoup(r.text, 'html.parser')

    def FaultTolerantGet(self, url, retrylimit, delay=0):
        success = False
        for i in range(0, retrylimit):
            try:
                r = self.http_session.get(url, timeout=REQUESTS_DEFAULT_TIMEOUT, verify=not DISABLE_SSL_VERIFICATION)
                r.raise_for_status()
                success = True
            except Exception as e:
                dprint(1, self.__class__.__name__ + ".FaultTolerantGet(): url " + repr(url) + " failed. (" + repr(e) + " )")
                time.sleep(delay)
                continue

            if success:
                break

        return success

    def InstallProxy(self, proxy):
        proxies = {'http': 'http://'+proxy, 'https': 'https://'+proxy}
        self.http_session.proxies.update(proxies)

    def Post(self, url, data):
        r = self.http_session.post(url, data=data, verify=not DISABLE_SSL_VERIFICATION)
        r.raise_for_status()
        return r

    def Reset(self):
        self.http_session.proxies.clear()


""" Procedures """

def GetExternalIP():
    try:
        return requests.get('http://myip.dnsdynamic.org/', headers=g_data['basic_http_headers'], timeout=REQUESTS_DEFAULT_TIMEOUT, verify=not DISABLE_SSL_VERIFICATION).text
    except Exception as e:
        dprint(0, "GetExternalIP(): Exception occurred: " + repr(e))

# Returns a difference between two timezones in hours
def get_tz_diff(tz1, tz2):
    now = datetime.now()

    tz1_offset = pytz.timezone(tz1).utcoffset(now).total_seconds() / 60 / 60
    tz2_offset = pytz.timezone(tz2).utcoffset(now).total_seconds() / 60 / 60

    lesser = min(tz1_offset, tz2_offset)
    greater = max(tz1_offset, tz2_offset)
    diff = greater - lesser

    return int(diff)
