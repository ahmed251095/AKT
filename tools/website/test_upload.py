"""Post the contact form with two attachments, the way a browser would."""
import http.cookiejar
import re
import urllib.request
import uuid

BASE = 'http://127.0.0.1:8169'
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/140.0 Safari/537.36')

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

html = op.open(urllib.request.Request(
    BASE + '/contact', headers={'User-Agent': UA})).read().decode()
token = re.search(r"""name="csrf_token" value=['"]([^'"]+)['"]""", html).group(1)

fields = {
    'name': 'Upload Test', 'email': 'upload@example.com',
    'phone': '01000000005', 'subject': 'With documents',
    'message': 'Two files attached.', 'consent': 'on', 'csrf_token': token,
}
files = [
    ('documents', 'site-plan.txt', b'plan contents'),
    ('documents', 'boq.csv', b'item,qty\nbrick,100\n'),
]

boundary = '----akt' + uuid.uuid4().hex
parts = []
for key, value in fields.items():
    parts.append(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
                  % (boundary, key, value)).encode())
for key, filename, data in files:
    parts.append(('--%s\r\nContent-Disposition: form-data; name="%s"; '
                  'filename="%s"\r\nContent-Type: application/octet-stream\r\n\r\n'
                  % (boundary, key, filename)).encode() + data + b'\r\n')
parts.append(('--%s--\r\n' % boundary).encode())

req = urllib.request.Request(
    BASE + '/akt/form/contact', data=b''.join(parts),
    headers={'User-Agent': UA, 'Referer': BASE + '/contact',
             'Content-Type': 'multipart/form-data; boundary=%s' % boundary})
r = op.open(req)
print('status', r.status, '->', r.url.split('?')[-1])
