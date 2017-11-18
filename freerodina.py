#!/usr/bin/env python
# -*- coding: utf-8 -*-

from freerodina.core import *
import freerodina.proxy
import freerodina.tempmail


"""
    The thing
"""
class RodinaTVAccountProvider:

    # constructor
    def __init__(self):
        self.http_client = freerodina.lib.NanoHTTPClient()
        self.proxy_stack = []
        self.tmpemail = None
        self.last_account = {}

    # populates the working proxy stack (with good and fast proxies only)
    def __PopulateProxyStack(self):
        proxy_manager = freerodina.proxy.ProxyManager()

        dprint(0, u"Получение свежих прокси-листов...")
        if not proxy_manager.Collect():
            halt(u"Не удалось собрать прокси.")

        dprint(0, u"Проверка и фильтрация прокси-листов...")
        if not proxy_manager.CheckAndFilter():
            halt(u"Не удалось найти работающих прокси.")

        self.proxy_stack = [d['ipaddr'] for d in proxy_manager.proxies]
        self.proxy_stack.reverse()

        dprint(0, u"Рабочих серверов найдено: " + unicode(len(self.proxy_stack)))
        dprint(1, "proxy_stack=" + repr(self.proxy_stack))

    # sets up a temporary email box
    def __SetupTempInbox(self):
        dprint(0, u"Создание временной электронной почты...")
        self.tmpemail = freerodina.tempmail.MytempEmailTempInbox()
        if not self.tmpemail.Renew():
            halt(u"Не удалось создать временный почтовый ящик.")

    # registers an account at www.rodina.tv, using obtained proxies and temp email
    def __RegisterAccount(self):
        registration_errors = g_data['registration_errors']
        registration_results = g_data['registration_results']

        # step 1. submitting registration form
        ############################################################################
        dprint(0, u"Регистрация нового аккаунта...")

        while self.proxy_stack:
            next_proxy = self.proxy_stack.pop()
            dprint(1, "next_proxy=" + next_proxy)

            self.http_client.Reset()
            self.http_client.InstallProxy(next_proxy)

            try:
                # requesting the form
                soup = self.http_client.GetSoup('https://rodina.tv/register/')
                token_input = soup.find('input', attrs={'name': 'fos_user_registration_form[_token]'})
                if token_input == None:
                    halt(u"Получена некорректная форма регистрации.")

                # submitting the form
                success = False
                ####################################################################
                formdata = g_data['registration_form_data']
                formdata['fos_user_registration_form[_token]'] = token_input['value']

                for i in range(0, DEFAULT_RETRY_LIMIT):
                    formdata['fos_user_registration_form[name]'] = self.tmpemail.address
                    formdata['fos_user_registration_form[email]'] = self.tmpemail.address

                    r = self.http_client.Post('https://rodina.tv/register/', formdata)

                    if not r.history:
                        if any(v in r.text for v in registration_errors):
                            if self.tmpemail.Renew(): # last temp email was rejected
                                continue # iterates "for"
                            else:
                                halt(u"Непредвиденные проблемы при пересоздании временной почты.")
                        else:
                            halt(u"Регистрация прошла некорректно.")

                    if not r.history[0].headers['Location'] == '/register/check-email':
                        halt(u"Регистрация прошла некорректно.")

                    success = True
                    break # exits "for"
                ####################################################################

                if not success:
                    halt(u"Не удалось зарегистрировать аккаунт после " + unicode(DEFAULT_RETRY_LIMIT) + " попыток.")

                break # exits "while". submit succeeded
            except Exception as e:
                dprint(1, "__RegisterAccount() (step 1): Exception occurred: " + repr(e))
                continue # iterates "while" with next proxy

        if not self.proxy_stack:
            halt(u"После перебора всех доступных прокси, аккаунт так и не удалось зарегистрировать.")
        ############################################################################


        # step 2. getting the activation mail
        ############################################################################
        timer = 0
        success = False

        dprint(0, u"Регистрация успешна. Ожидание письма активации...")

        while True:
            time.sleep(5)
            timer += 5

            mailindex = self.tmpemail.FetchIndex()
            dprint(1, "mailindex=" + repr(mailindex))

            if 'rodina.tv' in mailindex[0]['from_address']:
                last_mail = self.tmpemail.FetchLastMail()
                dprint(1, "last_mail=" + repr(last_mail))

                soup = BeautifulSoup(last_mail['body_html'], 'html.parser')
                ps = soup.findAll('p')
                activation_link = ps[1].string.strip().split(' ')[-1]

                dprint(1, "activation_link=" + repr(activation_link))

                if activation_link:
                    self.tmpemail.Delete()
                    success = True
                    break
                else:
                    halt(u"Письмо получено, но его разбор закончился неудачей.")

            if timer >= ACTIVATION_MAIL_WAIT_TIME:
                break

        if not success:
            halt(u"Превышен лимит ожидания письма активации (" + unicode(ACTIVATION_MAIL_WAIT_TIME) + " секунд)")

        ############################################################################


        # step 3. final. activating the account and getting the credentials
        ############################################################################
        dprint(0, u"Ссылка активации получена. Завершение регистрации...")

        success = False
        for i in range(0, DEFAULT_RETRY_LIMIT):
            try:
                r = self.http_client.Get(activation_link)

                if not r.history:
                    dprint(1, "http_client.Get(): redirect is missing, r.text=" + r.text)
                    halt(u"Переход по ссылке активации закончился неудачей.")

                if not r.history[0].headers['Location'] == '/register/confirmed':
                    dprint(1, "http_client.Get(): redirect failed, unexpected location=" + r.history[0].headers['Location'])
                    halt(u"Переход по ссылке активации закончился неудачей.")

                soup = self.http_client.GetSoup('https://rodina.tv/cabinet/1-day-test-page')

                dprint(1, "http_client.GetSoup() call, r.text=" + unicode(soup))

                # registration final results switch
                if not registration_results['success'] in unicode(soup):
                    # proxy has IP which is already used
                    if registration_results['used_ip'] in unicode(soup):
                        dprint(1, "__RegisterAccount(): Got a used proxy. (next_proxy=" + repr(next_proxy) + ")")
                        proxy_blacklist_append(next_proxy)
                        return False
                    # something is wrong
                    else:
                        halt(u"Не удалось завершить регистрацию и получить ТВ-аккаунт.")

                cabinet_data = soup.find('div', attrs={'id': 'cabinet_data'}).findAll('div')[0].findAll('div')[0].findAll('dd')

                if len(cabinet_data) >= 3:
                    self.last_account['login'] = cabinet_data[0].string.strip()
                    self.last_account['password'] = cabinet_data[1].string.strip()
                    self.last_account['expiration_time'] = cabinet_data[2].string.strip()

                proxy_blacklist_append(next_proxy) # disposing the waste
                success = True
                break # exits "for"

            except Exception as e:
                dprint(1, "__RegisterAccount() (step 3): Exception occurred: " + repr(e))
                continue # iterates "for"

        if not success:
            dprint(1, "__RegisterAccount(): Couldn't finish the registration after " + unicode(DEFAULT_RETRY_LIMIT) + " retries.")
            return False

        ############################################################################
        return True

    # primary method of the class
    def RenewAccount(self):
        dprint(0, u"Инициализация...")
        dprint(1, "debug mode on")

        if not proxy_blacklist:
            dprint(0, u"Внимание! Список использованных прокси пуст. Возможно, так и должно быть.")

        self.__PopulateProxyStack()
        self.__SetupTempInbox()

        # fault-tolerant loop
        while self.proxy_stack:
            if not self.__RegisterAccount():
                if self.proxy_stack:
                    dprint(1, "__RegisterAccount(): Restarting the procedure.")
                    dprint(0, u"Завершить регистрацию не удалось, повтор...")

                    if not self.tmpemail.Renew():
                        halt(u"Непредвиденные проблемы при пересоздании временного почтового ящика.")

                    continue
                else:
                    halt(u"После перебора всех доступных прокси, аккаунт так и не удалось зарегистрировать.")
            else:
                break # breaks "while"

        return True


"""
    Other functions
"""

def SetPlexChannelSettings(account):
    http_client = freerodina.lib.NanoHTTPClient()

    settings_urls = [
                        'http://' + PMS_IP + '/video/rodinatv/:/prefs/set?username=' + account['login'] + '&password=' + account['password'] + '&parentpass=12345',
                        'http://' + PMS_IP + '/video/rodinatv/SelectedServer?serverid=127&servername=' + RODINATV_SERVER,
                        'http://' + PMS_IP + '/video/rodinatv/SelectedTimeshift?timeshiftid=' + str(freerodina.lib.get_tz_diff(TIMEZONE_LOCAL, TIMEZONE_TV_SERVICE)) + '&timeshiftname=',
                        'http://' + PMS_IP + '/video/rodinatv/SelectedTZCity?tzcityname=Vancouver&tzcitytid=312'
                    ]

    success = True
    for url in settings_urls:
        if not http_client.FaultTolerantGet(url, DEFAULT_RETRY_LIMIT):
            dprint(1, "SetPlexChannelSettings(): retry limit exhausted. Aborting...")
            success = False
            break

    return success

def PrintLastAccount():
    filename = g_data['last_account_file']
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    if re.match('^\d+-\d+-\d+\s\d+:\d+$', line):
                        t = time.strptime(line, '%Y-%m-%d %H:%M')
                        dt = datetime.fromtimestamp(time.mktime(t))
                        dt = pytz.timezone('UTC').localize(dt)
                        dt = dt.astimezone(pytz.timezone(TIMEZONE_LOCAL))
                        print(dt.strftime('%Y-%m-%d %H:%M'))
                    else:
                        print(line)
    else:
        print u"Последний аккаунт не найден"


"""
    main() procedure
"""

def main(argv):
    action, dlevel = 'default', DEBUG_LEVEL

    # processing command line arguments
    try:
        opts, args = getopt.getopt(argv, "ndl")
        for opt, arg in opts:
            if opt == '-n':
                action = 'newaccount' if action == 'default' else 'default'
            if opt == '-l':
                action = 'lastaccount' if action == 'default' else 'default'
            if opt == '-d':
                dlevel = 1
    except getopt.GetoptError:
        pass

    dinit(dlevel, LOG_REWRITE) # initializing log/debug output

    # action switch
    if action == 'newaccount':
        print_header()

        account_provider = RodinaTVAccountProvider()
        if account_provider.RenewAccount():
            write_last_account(account_provider.last_account)

            dprint(0, u"Настройка Plex-канала...")

            if not SetPlexChannelSettings(account_provider.last_account):
                halt(u"Внимание! Не удалось настроить Plex-канал на новый аккаунт. Проверьте, что Plex-сервер доступен по указанному адресу, и что канал RodinaTV установлен.")

        dprint(0, u"Всё прошло удачно! Приятного просмотра!")
        dprint(0, u"Завершение работы...")

    elif action == 'lastaccount':
        PrintLastAccount()
    else:
       print_header()
       print_usage()

    # closing log/debug output
    dfree()


###########################################################################

# FREERODINA ENTRY POINT
if __name__ == '__main__':
    main(sys.argv[1:])
