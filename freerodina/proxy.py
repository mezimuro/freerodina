#!/usr/bin/env python
# -*- coding: utf-8 -*-

from freerodina.core import *
import freerodina.lib


"""
    Proxy providers
"""

class BaseProxyProvider:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.proxies = []
        self.http_client = freerodina.lib.NanoHTTPClient()

    def Load(self):
        try:
            self.proxies = self.Fetch()[:PROXY_PROVIDERS_LIST_LIMIT]
        except Exception as e:
            dprint(0, self.__class__.__name__ + ": Exception occurred: " + repr(e))
            return False

        dprint(1, self.__class__.__name__ + ": " + str(len(self.proxies)) + " proxies collected")
        return True

    @abstractmethod
    def Fetch():
        pass


class SslProxiesOrgProxyProvider(BaseProxyProvider):
    def Fetch(self):
        result = []

        soup = self.http_client.GetSoup('http://sslproxies.org/')

        tbl = soup.find('table', attrs={'id': 'proxylisttable'}).find('tbody')
        for row in tbl.findAll('tr'):
            col = row.findAll('td')
            result.append(col[0].string.strip() + ':' + col[1].string.strip())

        return result


class HideMeRuProxyProvider(BaseProxyProvider):
    def Fetch(self):
        result = []

        soup = self.http_client.GetSoup('http://hideme.ru/proxy-list/?maxtime=2000&type=s&anon=34')

        tbl = soup.find('table', attrs={'class': 'proxy__t'}).find('tbody')
        for row in tbl.findAll('tr'):
            col = row.findAll('td')
            result.append(col[0].string.strip() + ':' + col[1].string.strip())

        return result


class SslProxies42BlogspotCaProxyProvider(BaseProxyProvider):
    def Fetch(self):
        result = []

        soup = self.http_client.GetSoup('http://sslproxies24.blogspot.ca/')

        link = None
        divs = soup.findAll('div', attrs={'class': 'jump-link'})
        for div in divs:
            if "SSL" in div.find('a')['title']:
                link = div.find('a')['href']
                break

        # parsing "post" page
        if link:
            soup = self.http_client.GetSoup(link)
            result = soup.find('span', attrs={'style': 'color: #00cc00;'}).text.split()

        return result


"""
    Proxy checker
"""

class ProxyChecker:
    good_proxies = []

    def __checkprocedure(self, proxy):
        try:
            if proxy.split(':')[0] in proxy_blacklist:
                return  # proxy was used

            # testing the proxy 3 times on the RodinaTV web-site
            for i in range(0, 3):
                start_time = time.time()
                r = requests.get('https://rodina.tv/register/',
                                 headers = g_data['basic_http_headers'],
                                 proxies = {'http': 'http://'+proxy, 'https': 'https://'+proxy},
                                 timeout = PROXY_CHECKER_HTTP_TIMEOUT,
                                 verify = not DISABLE_SSL_VERIFICATION
                                )
                if i == 0:
                    latency = time.time() - start_time
                else:
                    latency = (latency + time.time() - start_time) / 2 # calculating average latency

            if not 'support@rodina.tv' in r.text:
                return  # we failed to open the correct web-page

            # check for elite anonymity (L1)
            try:
                r = requests.get('http://myip.dnsdynamic.org/',
                                 headers = g_data['basic_http_headers'],
                                 proxies = {'http': 'http://'+proxy, 'https': 'https://'+proxy},
                                 timeout = PROXY_CHECKER_HTTP_TIMEOUT,
                                 verify = not DISABLE_SSL_VERIFICATION
                                )
                if len(r.text) > 15:
                    return  # myip.dnsdynamic.org responded incorrectly
                if r.text == freerodina.lib.GetExternalIP():
                    return  # L1 anonymity test failed
            except Exception as e:
                dprint(1, self.__class__.__name__ + ": Exception occurred during L1 anonymity test: " + repr(e) + "; proxy=" + proxy)

            if not any(p['ipaddr'] == proxy for p in self.good_proxies):  # filtering duplicates
                self.good_proxies.append({'ipaddr':proxy, 'latency':latency})
        except Exception as e:
            dprint(1, self.__class__.__name__ + ": Exception occurred: " + repr(e) + "; proxy=" + proxy)

    # launches the check in a pseudo-multithreaded manner
    def Run(self, proxies):
        # concurrency stuff here
        jobs = [gevent.spawn(self.__checkprocedure, proxy) for proxy in proxies]
        try:
            gevent.joinall(jobs, timeout=PROXY_CHECKER_GEVENT_TIMEOUT)
            self.good_proxies = sorted(self.good_proxies, key=itemgetter('latency'))
        except KeyboardInterrupt:
            sys.exit("Ctrl-C caught, exiting")


"""
    Main class
"""

class ProxyManager:
    proxies = []

    # fetches and packs together proxies from all BaseProxyProvider-descendants in this module
    def Collect(self):
        __moduleclasses__ = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        for __moduleclass__ in __moduleclasses__:
            if __moduleclass__[1].__bases__:
                if __moduleclass__[1].__bases__[0].__name__ == 'BaseProxyProvider':
                    next_proxy_provider = __moduleclass__[1]()
                    if next_proxy_provider.Load():
                        self.proxies += next_proxy_provider.proxies

        if len(self.proxies) > 0:
            return True
        else:
            return False

    # removes unusable proxies from the list. sorting them by latency
    def CheckAndFilter(self):
        proxy_checker = ProxyChecker()
        proxy_checker.Run(self.proxies)
        self.proxies = proxy_checker.good_proxies

        if len(self.proxies) > 0:
            return True
        else:
            return False
