#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Main settings
"""

DEBUG_LEVEL                     = 0                         # -1 (off) / 0 (normal) / 1 (high)
LOG_FILE                        = 'freerodina.log'          # case-sensitive
LOG_REWRITE                     = False                     # True (create fresh log) / False (append)

PMS_IP                          = '127.0.0.1:32400'         # our Plex Media Server (where RodinaTV channel installed)

USER_AGENT                      = 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1866.237 Safari/537.36'

TIMEZONE_TV_SERVICE             = 'Europe/Moscow'           # timezone of TV channels
TIMEZONE_LOCAL                  = 'America/Vancouver'       # timezone of the viewer
RODINATV_SERVER                 = 'USA West'


"""
    Minor settings
"""

DEFAULT_RETRY_LIMIT             = 10                        # retry limit for fault-tolerant procedures
PROXY_PROVIDERS_LIST_LIMIT      = 300                       # for truncating too long ones

REQUESTS_DEFAULT_TIMEOUT        = 30.1                      # seconds
PROXY_CHECKER_HTTP_TIMEOUT      = 15.1                      # seconds
PROXY_CHECKER_GEVENT_TIMEOUT    = 90                        # seconds

ACTIVATION_MAIL_WAIT_TIME       = 600                       # seconds

DISABLE_SSL_VERIFICATION        = True                    
