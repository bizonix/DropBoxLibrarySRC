#Embedded file name: dropbox/sync_engine/p2p/crypto.py
from __future__ import absolute_import
import time
import POW
from dropbox.trace import TRACE, unhandled_exc_handler
dhParams_data = '\n-----BEGIN DH PARAMETERS-----\nMIHHAoHBAK7J14riM20k2t9Ahup6rjr70ST8HgVhR+4hm908rgBpB5GIhlbrIAS2\nNdLsXcwpnYvf3xiT0zHQyITVv8/9pKCjR2pkkdpRCse72StyLpOq9DGB6oVc+Jst\npiU0hROT+if77uMe9IYlhozfubkbsAAPvRUtElT5IP4GRyYh1rMxqnvD3HeEBePE\n5A0Xg4aKJeuVFaYDjSpm+zuAlXlT5M4mC5dlu6MULUZUOxtimmxk2eWGkYa44zB3\nV7J9o/EZ+wIBAg==\n-----END DH PARAMETERS-----\n'
dhParams = POW.pemRead(POW.DH_PARAMS, dhParams_data)

def time2utc(val):
    return time.strftime('%y%m%d%H%M%SZ', time.gmtime(int(val)))


class CryptoData(object):

    def __init__(self, privPEM = None, pubPEM = None, certPEM = None, force_tlsv1 = False):
        priv = None
        pub = None
        cert = None
        if privPEM and (pubPEM or certPEM):
            priv = POW.pemRead(POW.RSA_PRIVATE_KEY, privPEM)
            if pubPEM:
                pub = POW.pemRead(POW.RSA_PUBLIC_KEY, pubPEM)
        else:
            rk = POW.Asymmetric(POW.RSA_CIPHER, 1536)
            priv = POW.pemRead(POW.RSA_PRIVATE_KEY, rk.pemWrite(POW.RSA_PRIVATE_KEY))
            pub = POW.pemRead(POW.RSA_PUBLIC_KEY, rk.pemWrite(POW.RSA_PUBLIC_KEY))
        cert = None
        if certPEM:
            cert = POW.pemRead(POW.X509_CERTIFICATE, certPEM)
        else:
            name = [['CN', 'dropbox-client']]
            cert = POW.X509()
            cert.setVersion(3)
            cert.setSerial(1)
            cert.setSubject(name)
            cert.setIssuer(name)
            cert.setPublicKey(pub)
            cert.setNotBefore(time2utc(0))
            cert.setNotAfter(time2utc(time.time() + 31536000))
            cert.sign(priv, POW.SHA256_DIGEST)
        assert priv, 'Private Key was not set in core/p2p/crypto.py'
        assert cert, 'Certificate was not set in core/p2p/crypto.py'
        if not (privPEM and certPEM and not pubPEM):
            assert pub, 'Public Key was not set in core/p2p/crypto.py'
        self.cert = cert
        self.priv = priv
        self.pub = pub
        self.force_tlsv1 = force_tlsv1

    def tradeSockForCryptoSock(self, sock):
        ctx = self.get_context()
        ctx.setFd(sock.fileno())
        ctx.setCiphers(['HIGH',
         '!eNULL',
         '!aNULL',
         '!SSLv2'])
        return ctx

    def get_context(self):
        ctx = POW.Ssl(POW.TLSV1_METHOD if self.force_tlsv1 else POW.SSLV23_METHOD)
        try:
            ctx.useCertificate(self.cert)
            ctx.useKey(self.priv)
            ctx.setVerifyMode(POW.SSL_VERIFY_SELF_SIGNED)
            ctx.enableDH(dhParams)
        except Exception:
            unhandled_exc_handler()

        return ctx
