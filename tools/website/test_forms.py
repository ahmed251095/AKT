"""Post each form the way a visitor would and check what the CRM received."""
import re
import urllib.parse
import urllib.request
import http.cookiejar

BASE = 'http://127.0.0.1:8169'
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/140.0 Safari/537.36')

CASES = [
    ('/quotation', {
        'name': 'Test Quotation', 'company_name': 'Nile Builders',
        'email': 'quote@example.com', 'phone': '01000000001',
        'preferred_contact': 'whatsapp', 'service': 'industrial-projects',
        'project_type': 'Warehouse', 'sector': 'industrial',
        'governorate': 'البحيرة', 'project_location': 'Damanhour',
        'approximate_area': '2400', 'desired_start': '2027-02-01',
        'budget_amount': '7500000', 'budget_currency': 'EGP',
        'message': 'Need a quotation for a warehouse shell.', 'consent': 'on',
    }),
    ('/contact', {
        'name': 'Test Contact', 'email': 'hello@example.com',
        'phone': '01000000002', 'subject': 'General question',
        'message': 'Do you work in Alexandria?', 'consent': 'on',
    }),
    ('/appointments', {
        'name': 'Test Appointment', 'email': 'visit@example.com',
        'phone': '01000000003', 'request_type': 'visit',
        'project_location': 'Kafr El Dawar', 'preferred_date': '2027-01-20',
        'preferred_window': '09-12', 'alternative_date': '2027-01-21',
        'alternative_window': '12-15',
        'message': 'Please visit the site.', 'consent': 'on',
    }),
    ('/partners/register', {
        'company_name': 'Delta Steel', 'partner_type': 'both',
        'specialty': 'Steel structures', 'work_areas': 'Beheira, Alexandria',
        'name': 'Test Supplier', 'email': 'supplier@example.com',
        'phone': '01000000004', 'qualification_requested': 'on',
        'message': 'We would like to be registered.', 'consent': 'on',
    }),
]

REJECT = [
    ('/contact', {'name': 'No consent', 'email': 'a@b.com',
                  'subject': 's', 'message': 'm'}, 'consent missing'),
    ('/contact', {'name': 'Bad mail', 'email': 'not-an-email',
                  'subject': 's', 'message': 'm', 'consent': 'on'}, 'bad email'),
    ('/contact', {'name': 'Bot', 'email': 'a@b.com', 'subject': 's',
                  'message': 'm', 'consent': 'on',
                  'website': 'http://spam.example'}, 'honeypot filled'),
]


def opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def post(op, page, data):
    """Load the page for a CSRF token, then post the form."""
    req = urllib.request.Request(BASE + page, headers={'User-Agent': UA})
    html = op.open(req).read().decode()
    # QWeb picks the quote character itself, so accept either.
    token = re.search(r"""name="csrf_token" value=['"]([^'"]+)['"]""", html)
    assert token, 'no csrf token on %s' % page
    body = dict(data, csrf_token=token.group(1))
    action = re.search(r'<form method="post" action="([^"]+)"', html).group(1)
    req = urllib.request.Request(
        BASE + action, data=urllib.parse.urlencode(body).encode(),
        headers={'User-Agent': UA,
                 'Content-Type': 'application/x-www-form-urlencoded',
                 'Referer': BASE + page})
    return op.open(req)


for page, data in CASES:
    op = opener()
    r = post(op, page, data)
    print('%-20s -> %s  %s' % (page, r.status, r.url.split('?')[-1]))

print()
for page, data, why in REJECT:
    op = opener()
    r = post(op, page, data)
    print('%-20s %-18s -> %s' % (page, why, r.url.split('?')[-1][:60]))
