#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" "Core" stuff module. Inits/environment/includes/constants/structs/etc... """


"""
    Imports
"""

from abc import ABCMeta, abstractmethod, abstractproperty
from operator import itemgetter

import locale
import sys
import io
import time
import inspect
import getopt
import os.path
import re

from gevent import monkey
monkey.patch_all()
import gevent

from datetime import datetime
import pytz

import requests
import json
from bs4 import BeautifulSoup
import ssl

from freerodina.settings import *


"""
    Pre-initialized data/constants/etc
"""

g_data = {}

g_data['proxy_blacklist_file']        =       'blacklist'
g_data['last_account_file']           =       'lastaccount'
g_data['log_file']                    =       LOG_FILE

g_data['basic_http_headers']          =       {
                                                'User-Agent' : USER_AGENT
                                              }


g_data['registration_form_data']      =       {
                                                'fos_user_registration_form[name]' : '',
                                                'fos_user_registration_form[email]' : '',
                                                'fos_user_registration_form[plainPassword][first]' : '11223344',
                                                'fos_user_registration_form[plainPassword][second]' : '11223344',
                                                'id' : '',
                                                'hash' : '',
                                                'aid' : '',
                                                'fos_user_registration_form[_token]' : ''
                                              }

g_data['registration_errors']         =       [
                                                u'Пожалуйста, введите ваш постоянный e-mail адрес',
                                                u'Email уже используется',
                                                u'Это значение уже используется',
                                                u'Email в неправильном формате'
                                              ]

g_data['registration_results']        =       {
                                                'success' : u'Вы подтвердили регистрацию и получаете 1 день бесплатно для тестирования перед покупкой.',
                                                'used_ip' : u'уже был использован бесплатный абонемент на 1 день.'
                                              }


"""
    Global variables/storage
"""

proxy_blacklist     =        []


"""
    Initialization
"""
#reload(sys)
#sys.setdefaultencoding('utf-8')


"""
    Core functions and procedures
"""

def halt(msg):
    dprint(0, u"Ошибка: " + msg)
    dprint(0, u"Завершение работы...")
    sys.exit(1)

def print_usage():
    dprint(0, u"Доступны следующие опции:                      ")
    dprint(0,  "")
    dprint(0, u"    -n        получить новый аккаунт           ")
    dprint(0, u"    -l        показать последний аккаунт       ")
    dprint(0, u"    -d        форсировать режим отладки        ")
    dprint(0,  "")
    dprint(0,  "")
    dprint(0,  "")
    dprint(0, u"                    Успехов!                   ")
    dprint(0,  "")
    dprint(0,  "###############################################")

def print_header():
    dprint(0,  "###############################################")
    dprint(0,  "..../..........................................")
    dprint(0,  ".../..R O D I N A  T V ........................")
    dprint(0,  "../...E X P L O I T ...........................")
    dprint(0,  "./....v 2.0....................................")
    dprint(0,  "/_ _                _ _ _ _ _ _ _ _ _ _ _ _ _ _")
    dprint(0,  "#### by mezimuro ################### 2016 #####")
    dprint(0,  "")
    dprint(0, u"         Наслаждаемся бесплатным ТВ :D         ")
    dprint(0,  "")
    dprint(0,  "***********************************************")

def get_full_path(filename):
    return os.getcwd()+os.path.sep+filename

def proxy_blacklist_load():
    global proxy_blacklist

    filename = g_data['proxy_blacklist_file']
    if os.path.isfile(filename):
        f = open(filename, 'r')
        proxy_blacklist = [line.strip() for line in f]

def proxy_blacklist_append(proxy):
    with open(g_data['proxy_blacklist_file'], 'a') as f:
        f.write(proxy.split(':')[0] + "\n")

def write_last_account(account):
    if account:
        f = open(g_data['last_account_file'], 'w')
        f.write(account['login'] + "\n")
        f.write(account['password'] + "\n")
        f.write(account['expiration_time'] + "\n")

def fault_tolerant_run(function, retrylimit, delay=0):
    for i in range(0, DEFAULT_RETRY_LIMIT):
        function()


"""
    Finalization
"""
g_data['proxy_blacklist_file'] = get_full_path(g_data['proxy_blacklist_file'])
g_data['last_account_file'] = get_full_path(g_data['last_account_file']);
g_data['log_file'] = get_full_path(g_data['log_file']);

proxy_blacklist_load()

from freerodina.debug import dinit, dprint, dfree
import freerodina.lib

if DISABLE_SSL_VERIFICATION:
    requests.packages.urllib3.disable_warnings()
