#!/usr/bin/env python
# -*- coding: utf-8 -*-

# original code by baa (PlexConnect)

from freerodina.core import *


g_logfile = g_data['log_file']
g_loglevel = 0
g_preffered_encoding = locale.getpreferredencoding()
g_sys_stdout_encoding = sys.stdout.encoding
g_new_start_str = ''
g_new_date_printed = False

def dinit(dlevel, newlog=False):
    global f, g_loglevel, g_new_start_str, g_new_date_printed
    g_loglevel = dlevel

    if not g_loglevel==-1 and not g_logfile=='':
        openmode = 'w' if newlog else 'a'

        if openmode == 'a':
            g_new_start_str = u"*\n************************************************ NEW START AT: " + time.strftime("%d/%m/%Y %H:%M:%S") + u" ************************************************\n*"

        f = io.open(g_logfile, openmode, encoding='utf-8')

        try:
            if os.stat(g_logfile).st_size == 0:
               g_new_date_printed = True
        except OSError:
            pass


# debugging output
def dprint(dlevel, *args):
    global g_new_date_printed

    logToTerminal = not g_loglevel==-1 and not g_logfile=='' and dlevel <= g_loglevel
    logToFile = logToTerminal

    if logToTerminal or logToFile:
        asc_args = list(args)

        for i,arg in enumerate(asc_args):
            if isinstance(asc_args[i], str):
                asc_args[i] = unicode(asc_args[i].decode(g_preffered_encoding))

        # print to file (if filename defined)
        if logToFile:
            if not g_new_date_printed:
                f.write(g_new_start_str + u"\n")
                g_new_date_printed = True

            f.write(unicode(time.strftime("%H:%M:%S "), 'utf-8'))
            if len(asc_args)==0:
                f.write(u"|")
            elif len(asc_args)==1:
                f.write(u"| "+asc_args[0]+u"\n")
            else:
                f.write(u"| "+asc_args[0].format(*asc_args[1:])+u"\n")

        # print to terminal window
        if logToTerminal:
            print(time.strftime("%H:%M:%S")),
            if len(asc_args)==0:
                print "|"
            elif len(asc_args)==1:
                print "| "+asc_args[0].encode(encoding=g_sys_stdout_encoding, errors='replace')
            else:
                print "| "+asc_args[0].format(*asc_args[1:]).encode(encoding=sys.stdout.encoding, errors='replace')

        if not g_new_date_printed:
            g_new_date_printed = True

def dfree():
    f.close()
