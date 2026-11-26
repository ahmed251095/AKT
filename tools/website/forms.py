"""Turn the Django forms in the mirrored pages into Odoo ones.

Four pages post: the quotation, the supplier registration, the appointment
request and the contact form - the last reused on the consultancy and
technical-office pages. The markup is kept; what changes is where it posts,
the CSRF field, and the two selects whose option values were Django row ids.
"""
import re

# page url -> (kind, controller route)
POSTING = {
    '/quotation': 'quotation',
    '/partners/register': 'partner',
    '/appointments': 'appointment',
    '/contact': 'contact',
    '/pages/consultancy': 'contact',
    '/pages/technical-office': 'contact',
}

CSRF = re.compile(r'<input type="hidden" name="csrfmiddlewaretoken"[^>]*/>')
FORM_OPEN = re.compile(r'<form method="post"([^>]*)>')

# Django rendered these as row ids; a slug survives a rebuild and is what the
# quotation page already accepts in ?service=.
SERVICE_SLUGS = ['general-contracting', 'construction-development',
                 'industrial-projects', 'residential-projects',
                 'administrative-projects', 'government-projects',
                 'engineering-consultancy', 'technical-office']
SECTOR_SLUGS = ['industrial', 'residential', 'administrative', 'government']


def _renumber(body, field, slugs):
    """Replace <option value="1"> ... with the matching slug, in order."""
    m = re.search(r'<select name="%s"[^>]*>.*?</select>' % field, body, re.S)
    if not m:
        return body
    block = m.group(0)
    seen = []

    def one(om):
        val = om.group(1)
        if not val:
            return om.group(0)
        seen.append(val)
        try:
            slug = slugs[int(val) - 1]
        except (ValueError, IndexError):
            return om.group(0)
        return om.group(0).replace('value="%s"' % val, 'value="%s"' % slug, 1)

    new = re.sub(r'<option value="([^"]*)"', one, block)
    return body.replace(block, new)


def rewrite(url, body):
    """Return the page body with its form wired to the Odoo controller."""
    kind = POSTING.get(url)
    if not kind:
        return body

    body = CSRF.sub(
        '<input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>',
        body)
    body = FORM_OPEN.sub(
        r'<form method="post" action="/akt/form/%s"\1>' % kind, body, count=1)
    body = _renumber(body, 'service', SERVICE_SLUGS)
    body = _renumber(body, 'sector', SECTOR_SLUGS)

    # Where the result of the post is shown. The panel uses the site's own
    # classes so it reads as part of the page rather than as Odoo chrome.
    panel = '''<t t-if="request.params.get('akt_sent')">
  <div class="form-field akt-form-result akt-form-ok" role="status">
    <strong>Your request has been received.</strong>
    <span>Our team will get back to you shortly.</span>
  </div>
</t>
<t t-if="request.params.get('akt_error')">
  <div class="form-field akt-form-result akt-form-error" role="alert">
    <strong>The request was not sent.</strong>
    <span t-out="request.params.get('akt_error')"/>
  </div>
</t>
'''
    i = body.find('<form method="post"')
    j = body.index('>', i) + 1
    return body[:j] + panel + body[j:]
