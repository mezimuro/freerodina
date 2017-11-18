#!/usr/bin/env python
# -*- coding: utf-8 -*-

from freerodina.core import *


"""
    Classes for providing temporary e-mail
"""

class BaseTempInbox:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.address = ''
        self.http_session = requests.Session()
        self.http_session.headers.update(g_data['basic_http_headers'])

    @abstractmethod
    def Create():
        pass

    @abstractmethod
    def Delete():
        pass

    @abstractmethod
    def FetchIndex():
        pass

    @abstractmethod
    def FetchMail():
        pass

    @abstractmethod
    def FetchLastMail():
        pass

    def Renew(self):
        if self.address:
            self.Delete()
        if self.Create():
            dprint(1, self.__class__.__name__ + ".Renew() call: new address=" + self.address)
            return True
        else:
            return False


class MytempEmailTempInbox(BaseTempInbox):
    # creates new inbox
    def Create(self):
        r = self.MakeAPIRequest('https://api.mytemp.email/1/inbox/create?sid=0&task=0&tt=0')
        if not r:
            return False

        self.address = r.get('inbox') or '';
        self.hash = r.get('inbox_hash') or '';
        self.destroy_hash = r.get('inbox_destroy_hash') or '';

        if not self.address or not self.hash or not self.destroy_hash:
            return False

        return True

    # deletes the inbox
    def Delete(self):
        if not self.MakeAPIRequest('https://api.mytemp.email/1/inbox/destroy?inbox=' + self.address + '&inbox_destroy_hash=' + self.destroy_hash):
            return False
        self.address, self.hash, self.destroy_hash = '', '', ''
        return True

    # fetches mail headers
    def FetchIndex(self):
        r = self.MakeAPIRequest('https://api.mytemp.email/1/inbox/check?inbox=' + self.address + '&inbox_hash=' + self.hash)
        if not r:
            return None
        if not 'emls' in r:
            return None
        return r['emls']

    # fetches single mail
    def FetchMail(self, mail):
        r = self.MakeAPIRequest('https://api.mytemp.email/1/eml/get?eml=' + mail['eml'] + '&eml_hash=' + mail['eml_hash'])
        if not r:
            return None
        if not 'body_text' in r:
            return None
        return r

    # fetches the last mail
    def FetchLastMail(self):
        mailindex = self.FetchIndex()
        if mailindex is not None:
            return self.FetchMail(mailindex[0])

    # API gateway for all functions
    def MakeAPIRequest(self, url):
        try:
            r = self.http_session.get(url, timeout=REQUESTS_DEFAULT_TIMEOUT, verify=not DISABLE_SSL_VERIFICATION)
            jsondata = json.loads(r.text)

            if r.status_code == 500: # check for API errors
                if 'msg' in jsondata:
                    dprint(0, self.__class__.__name__ + ": mytemp.email API Error: " + jsondata['msg'])
                    return False

            r.raise_for_status()
            return jsondata
        except Exception as e:
            dprint(0, self.__class__.__name__ + ".MakeAPIRequest(): Exception occured: " + repr(e) + '; url=' + url)
            return False
