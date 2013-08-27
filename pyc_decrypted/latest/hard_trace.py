#Embedded file name: hard_trace.py
import socket
import platform
import client_api.connection_hub
import json
from trace_report import make_report, MAX_REPORT_LENGTH
from build_number import BUILD_KEY
from dropbox.build_common import get_build_number
from dropbox.functions import lenient_decode
from dropbox.url_info import dropbox_url_info
import dropbox.client.high_trace
HARD_HOST = 'd.dropbox.com' if BUILD_KEY == 'Dropbox' or BUILD_KEY.startswith('DropboxBuild') else 'd-tarak.corp.getdropbox.com'
HARD_PORT = 443

def unhandled_exc_handler(hash = None, report = None):
    exc_conn = client_api.connection_hub.HTTPConnectionHub([(HARD_HOST, HARD_PORT)], True)
    if hash is None:
        report, hash = make_report()
    if len(report) > MAX_REPORT_LENGTH:
        report = report[-MAX_REPORT_LENGTH:]
    ret = exc_conn.request('exception', dict(hash=hash, report=report, count='1', host_id=dropbox_url_info.host_id(), hostname=socket.gethostname(), buildno=get_build_number() or '', un=json.dumps([ lenient_decode(i) for i in platform.uname() ])))
    if isinstance(ret['ret'], list) or isinstance(ret['ret'], tuple) and ret['ret'][0] == 'send_trace':
        try:
            import dropbox.client.high_trace
            latest, related_exception = ret['ret'][1:]
            dropbox.client.high_trace._rtrace_thread.log.send_all(latest, related_exception)
        except Exception:
            unhandled_exc_handler()
