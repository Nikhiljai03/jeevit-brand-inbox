"""Small explicit contracts shared by offline extraction and the model adapter."""
from datetime import date, datetime
import math

CATEGORIES = ('deal_offer', 'needs_more_info', 'not_a_fit', 'scam_or_phishing', 'spam')
ACTIONS = ('accept', 'negotiate', 'ask for details', 'decline', 'ignore', 'report')
KINDS = ('instagram_reel', 'instagram_story', 'youtube_integration', 'youtube_dedicated_video', 'youtube_shoutout')
TEXT_FIELDS = ('brand', 'campaign', 'currency', 'payment_type', 'deadline', 'window_start',
               'relative_deadline', 'usage_text', 'product_category', 'payment_terms', 'gift_currency', 'joining_fee_currency')
NUMBER_FIELDS = ('cash_amount', 'gift_value', 'joining_fee', 'usage_months')
BOOL_FIELDS = ('perpetual_usage', 'whitelisting', 'attachment_missing', 'newsletter', 'followup')
FACT_FIELDS = TEXT_FIELDS + NUMBER_FIELDS + BOOL_FIELDS + ('deliverables', 'security_signals')


class ExtractionValidationError(ValueError):
    def __init__(self, field, reason):
        super().__init__(f'{field}: {reason}')
        self.field = field
        self.reason = reason


def invalid(field, reason):
    raise ExtractionValidationError(field, reason)


def empty_facts():
    return {**dict.fromkeys(TEXT_FIELDS + NUMBER_FIELDS),
            **dict.fromkeys(BOOL_FIELDS, False), 'deliverables': [], 'security_signals': []}


def validate_inputs(profile, inbox):
    if not isinstance(profile, dict) or not isinstance(inbox, list):
        raise ValueError('Profile must be an object and inbox must be a list.')
    date.fromisoformat(profile['today'])
    if not isinstance(profile.get('base_rates_inr'), dict):
        raise ValueError('base_rates_inr must be an object.')
    for value in profile['base_rates_inr'].values():
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError('Rates must be finite nonnegative numbers.')
    if not isinstance(profile.get('content_rules'), list):
        raise ValueError('content_rules must be a list.')
    for restriction in profile.get('current_exclusivity', []):
        date.fromisoformat(restriction['until'])
        if not all(isinstance(restriction.get(k), str) for k in ('brand', 'category', 'terms')):
            raise ValueError('Invalid exclusivity entry.')
    ids = set()
    for email in inbox:
        if not isinstance(email, dict) or not all(isinstance(email.get(k), str) and email[k].strip()
                for k in ('id', 'received_at', 'from', 'subject', 'body')):
            raise ValueError('Each email needs nonempty id, received_at, from, subject and body.')
        if email['id'] in ids:
            raise ValueError('Duplicate email ID: ' + email['id'])
        ids.add(email['id'])
        datetime.fromisoformat(email['received_at'])
        if len(email['body']) > 30000:
            raise ValueError('Email body exceeds the 30,000 character input limit.')


def validate_extraction(data, email):
    if not isinstance(data, dict) or set(data) != {'facts', 'evidence'}:
        invalid('schema', 'expected exactly facts and evidence objects.')
    f, ev = data['facts'], data['evidence']
    if not isinstance(f, dict) or set(f) != set(FACT_FIELDS):
        invalid('facts', 'keys do not match the extraction schema.')
    for key in TEXT_FIELDS:
        if f[key] is not None and (not isinstance(f[key], str) or len(f[key]) > 1000):
            invalid(key, 'expected a string of at most 1,000 characters or null.')
    for key in NUMBER_FIELDS:
        v = f[key]
        if v is not None and (type(v) not in (int, float) or not math.isfinite(v) or v < 0):
            invalid(key, 'expected a finite nonnegative number or null.')
    for key in BOOL_FIELDS:
        if type(f[key]) is not bool:
            invalid(key, 'expected a boolean.')
    if any(f[k] not in (None, 'INR', 'USD') for k in ('currency','gift_currency','joining_fee_currency')):
        invalid('currency', 'expected INR, USD, or null; do not guess conversions.')
    if f['payment_type'] not in (None, 'cash', 'gifting', 'mixed'):
        invalid('payment_type', 'expected cash, gifting, mixed, or null.')
    cash, gift, payment = f['cash_amount'], f['gift_value'], f['payment_type']
    if (cash is not None and gift is not None and payment != 'mixed'
            or cash is not None and gift is None and payment != 'cash'
            or cash is None and gift is not None and payment not in (None, 'gifting')
            or cash is None and gift is None and payment is not None):
        invalid('payment_type', 'must agree with the cash_amount and gift_value.')
    for key in ('deadline', 'window_start'):
        if f[key] is not None:
            try:
                date.fromisoformat(f[key])
            except ValueError:
                invalid(key, 'expected an ISO YYYY-MM-DD date or null.')
    if not isinstance(f['deliverables'], list):
        invalid('deliverables', 'expected a list.')
    for item in f['deliverables']:
        if (not isinstance(item, dict) or set(item) != {'kind', 'quantity'}
                or item.get('kind') not in KINDS or type(item.get('quantity')) is not int
                or not 1 <= item.get('quantity', 0) <= 10000):
            invalid('deliverables', 'each item needs a supported kind and quantity from 1 to 10,000.')
    if not isinstance(f['security_signals'], list) or any(x not in
            ('prompt_injection', 'suspected_phishing', 'pay_to_join') for x in f['security_signals']):
        invalid('security_signals', 'contains an unsupported signal.')
    if not isinstance(ev, dict):
        invalid('evidence', 'expected an object.')
    if set(ev) - set(FACT_FIELDS):
        invalid('evidence', 'contains a field outside the extraction schema.')
    source = email['subject'] + '\n' + email['body']
    for key, quote in ev.items():
        if quote is None:
            continue
        if not isinstance(quote, str) or not quote or quote not in source:
            invalid(f'evidence.{key}', 'must be an exact source substring or null.')
    for key, value in f.items():
        if key == 'payment_type':
            continue
        if value is not None and value is not False and value != [] and not ev.get(key):
            invalid(f'evidence.{key}', 'required for a populated fact.')
    return data


def model_schema():
    props = {k: {'type': ['string', 'null']} for k in TEXT_FIELDS}
    props.update({k: {'type': ['number', 'null'], 'minimum': 0} for k in NUMBER_FIELDS})
    props.update({k: {'type': 'boolean'} for k in BOOL_FIELDS})
    for k in ('currency','gift_currency','joining_fee_currency'):
        props[k] = {'enum': [None, 'INR', 'USD']}
    props['payment_type'] = {'enum': [None, 'cash', 'gifting', 'mixed']}
    props['deliverables'] = {'type': 'array', 'items': {'type': 'object', 'properties': {
        'kind': {'enum': list(KINDS)}, 'quantity': {'type': 'integer', 'minimum': 1}},
        'required': ['kind', 'quantity'], 'additionalProperties': False}}
    props['security_signals'] = {'type': 'array', 'items': {'enum':
        ['prompt_injection', 'suspected_phishing', 'pay_to_join']}}
    return {'type': 'object', 'properties': {
        'facts': {'type': 'object', 'properties': props, 'required': list(props), 'additionalProperties': False},
        'evidence': {'type': 'object', 'properties': {k: {'type': ['string', 'null']} for k in FACT_FIELDS},
                     'additionalProperties': False}}, 'required': ['facts', 'evidence'], 'additionalProperties': False}
