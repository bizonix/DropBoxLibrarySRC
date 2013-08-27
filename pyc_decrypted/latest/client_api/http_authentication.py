#Embedded file name: client_api/http_authentication.py
import urllib2
import base64
try:
    from dropbox.trace import TRACE
except Exception:

    def TRACE(string, *n):
        print string % n


def get_proxy_authorization_line(auth_type, auth_details, method, url, proxy_username, proxy_password):
    if auth_type.lower() == 'basic':
        response = base64.encodestring('%s:%s' % (proxy_username, proxy_password)).strip()
    elif auth_type.lower() == 'digest':

        class Passwd:

            def __init__(self, user, passwd):
                self.user, self.passwd = user, passwd

            def add_password(self, user, passwd):
                pass

            def find_user_password(self, realm, url):
                return (self.user, self.passwd)

            def get_full_url(self):
                return ''

        class DummyRequest:

            def __init__(self, method, url):
                self.method, self.url = method, url

            def get_method(self):
                return self.method

            def get_selector(self):
                return self.url

            def get_full_url(self):
                return self.url

            def has_data(self):
                return False

        digest_auth_handler = urllib2.AbstractDigestAuthHandler(passwd=Passwd(proxy_username or '', proxy_password or ''))
        chal = urllib2.parse_keqv_list(urllib2.parse_http_list(auth_details))
        response = digest_auth_handler.get_authorization(DummyRequest(method, url), chal)
    else:
        raise ValueError('Invalid proxy-authenticate line %r' % auth_type)
    return 'Proxy-Authorization: %s %s' % (auth_type, response)


def parse_proxy_authentication(reqlines):
    for reqline in reqlines:
        reqlinel = reqline.lower()
        if not reqlinel.startswith('proxy-authenticate: '):
            continue
        auth_type = None
        rest = []
        for a in reqline[len('proxy-authenticate:'):].split(','):
            a = a.strip()
            if auth_type is None:
                try:
                    hmm, hmm2 = a.split(None, 1)
                except ValueError:
                    if '=' not in a and a.lower() in ('basic', 'digest'):
                        auth_type = a
                        break
                else:
                    if hmm.lower() in ('basic', 'digest') and '=' in hmm2:
                        auth_type = hmm
                        rest.append(hmm2)
            else:
                try:
                    hmm, hmm2 = a.strip().split('=', 1)
                except ValueError:
                    break
                else:
                    if ' ' in hmm:
                        break
                    else:
                        rest.append(a.strip())

        if auth_type:
            hey = ', '.join(rest)
            TRACE('Using proxy authentication info: %r, %r', auth_type, hey)
            return (auth_type, hey)

    raise ValueError('No Proxy-Authenticate line specified')
