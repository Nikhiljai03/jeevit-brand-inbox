"""Conservative offline baseline. No email IDs, gold labels or brand allowlists."""
import re
from datetime import date
from decimal import Decimal
from .schemas import empty_facts, validate_extraction

MONTHS = {name.lower(): i for i, name in enumerate(
    ('January','February','March','April','May','June','July','August','September','October','November','December'), 1)}
MONTH_RE = '|'.join(MONTHS)
NUMBER = r'\d[\d,]*(?:\.\d+)?\s*(?:lakhs?\b|k\b)?'
NUMBER_WORD = r'(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|lakh|lac)'
NUMBER = r'(?:\d[\d,]*(?:\.\d+)?\s*(?:lakhs?\b|k\b)?|' + NUMBER_WORD + r'(?:[\s-]+(?:and[\s-]+)?' + NUMBER_WORD + r')*)'
MONEY = re.compile(r'(?P<currency>INR\b|USD\b|Rs\.?|₹|\$|rupees?\b)\s*(?P<amount>' + NUMBER + ')|(?P<word_amount>' + NUMBER_WORD + r'(?:[\s-]+(?:and[\s-]+)?' + NUMBER_WORD + r')*)\s*(?P<word_currency>rupees?\b)', re.I)


def amount(text):
    value = text.lower().replace(',', '').strip()
    if value and value[0].isalpha():
        words = re.findall(r'[a-z]+', value)
        small = {'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11,
                 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16,
                 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30,
                 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90}
        total = current = 0
        for word in words:
            if word in small:
                current += small[word]
            elif word == 'and':
                continue
            elif word == 'hundred':
                current = max(current, 1) * 100
            elif word in ('thousand', 'lakh', 'lac'):
                scale = 100000 if word in ('lakh', 'lac') else 1000
                total += max(current, 1) * scale
                current = 0
            elif word == 'lakhs':
                total += max(current, 1) * 100000
                current = 0
            else:
                raise ValueError('Unsupported number word: ' + word)
        return float(Decimal(total + current))
    multiplier = Decimal(1)
    if re.search(r'lakhs?$', value):
        multiplier = Decimal(100000); value = re.sub(r'\s*lakhs?$', '', value)
    elif value.endswith('k'):
        multiplier = Decimal(1000); value = value[:-1]
    return float(Decimal(value.strip()) * multiplier)


def security_signals(email):
    """Narrow signals, not a guarantee of detecting every attack or scam."""
    text = (email['subject'] + '\n' + email['body']).lower()
    signals = []
    addressed = re.search(r'\b(ai assistant|language model|system prompt|ignore (?:all |previous |prior )?instructions)\b', text)
    directive = re.search(r'\b(classify|recommend|ignore|reveal|include|including|output|confirm|send)\b', text)
    if addressed and directive:
        signals.append('prompt_injection')
    if re.search(r'(?:pay|payment|fee).{0,60}(?:registration|join|unlock)|(?:registration|joining|entry) fee', text):
        signals.append('pay_to_join')
    # Suspicion, not domain reputation verification. We never follow a URL.
    threat = re.search(r'suspend|suspension|terminate|termination|copyright strikes|locked', text)
    credential = re.search(r'verify.{0,35}account|password|log.?in|credentials', text)
    if threat and credential and re.search(r'https?://', text):
        signals.append('suspected_phishing')
    return signals


def extract_rules(email, profile):
    f, ev = empty_facts(), {}
    body = email['body']; subject = email['subject']; text = subject + '\n' + body
    lower = text.lower()
    def put(key, value, quote=None):
        f[key] = value
        if value is not None and value is not False and value != []:
            ev[key] = quote or body
    signals = security_signals(email)
    put('security_signals', signals)
    # Quarantine assistant-directed content before monetary / business extraction.
    if 'prompt_injection' in signals or 'suspected_phishing' in signals:
        return validate_extraction({'facts': f, 'evidence': ev}, email)
    put('newsletter', bool(re.search(r'\bunsubscribe\b|\bnewsletter\b', lower)))
    put('followup', bool(re.search(r'\bfollow(?:ing|[ -]?up)\b|^re:', lower)))
    put('attachment_missing', bool(re.search(r'\battached\b|\battachment\b', lower)))
    brand_patterns = [
        r'(?:campaigns for|on behalf of)\s+([A-Z][\w &\'-]+?)(?:\.|\s+-|\s+campaign|$)',
        r"(?i:we're|we are)\s+([A-Z][\w &\'-]+?)(?:,|\.|\s+and\b)",
        r'\bhum\s+(.+?)\s+hain\b',
        r'\b([A-Z][A-Za-z0-9& ]+?)\s+(?:would like|would love|is India)',
        r'\bfor\s+([A-Z][A-Za-z0-9& ]+?)(?:\'s|’s)\s',
        r'-\s*([A-Z][\w &]+?)\s+team\b',
    ]
    for pattern in brand_patterns:
        m = re.search(pattern, body)
        if m:
            put('brand', m.group(1).strip(), m.group(0)); break
    if f['brand'] is None:
        m = re.search(r'(.+?)\s+x\s+', subject, re.I)
        if m:
            put('brand', re.sub(r'^(?:(?:Re|Collab):\s*)+', '', m.group(1), flags=re.I).strip(), m.group(0))
    if f['brand'] is None:
        m = re.search(r'(?:paid reel|review|campaign)\s*[-–]\s*([A-Z][A-Za-z0-9&]+)', subject, re.I)
        if m:
            put('brand', m.group(1), m.group(0))
    # A short descriptive campaign key; grouping still requires corroboration.
    m = re.search(r'\b(?:new\s+)?([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)?\s+(?:serum|kit))\b', body, re.I)
    if m:
        put('campaign', m.group(1).lower(), m.group(0))
    deliverables = []
    kinds = [(r'(?:(?:instagram|ig)\s+)?reels?\b','instagram_reel'),
             (r'(?:(?:instagram|ig)\s+)?stor(?:y|ies)\b','instagram_story'),
             (r'(?:youtube\s+)?dedicated\s+videos?\b','youtube_dedicated_video'),
             (r'(?:youtube\s+)?integrations?\b','youtube_integration'),
             (r'(?:youtube\s+)?shoutouts?\b','youtube_shoutout')]
    nums = {'a':1, 'an':1, 'one':1, 'two':2, 'three':3, 'ek':1}
    for pattern, kind in kinds:
        m = re.search(r'\b(\d+|one|two|three|a|an|ek)\s+'+pattern, body, re.I)
        if m:
            n = m.group(1).lower(); deliverables.append({'kind':kind,'quantity':int(n) if n.isdigit() else nums[n]})
        elif kind == 'youtube_integration' and re.search(r'\bintegration\b', body, re.I):
            deliverables.append({'kind':kind,'quantity':1})
    put('deliverables', deliverables)
    for m in MONEY.finditer(body):
        value_text = m.group('amount') or m.group('word_amount')
        currency_text = m.group('currency') or m.group('word_currency')
        v = amount(value_text); currency = 'USD' if currency_text.upper() in ('USD','$') else 'INR'
        before = body[max(0,m.start()-65):m.start()].lower()
        if re.search(r'worth\s*$',before):
            put('gift_value',v,m.group(0)); put('gift_currency',currency,m.group(0)); continue
        if re.search(r'(?:registration|joining|entry) fee\s*(?:of\s*)?$',before):
            put('joining_fee',v,m.group(0)); put('joining_fee_currency',currency,m.group(0)); continue
        # A pay-to-join scheme is never treated as a cash deal.
        if 'pay_to_join' not in signals and (re.search(r'budget|offer|fee|pay|payment|do\s*$', before) or deliverables):
            put('cash_amount',v,m.group(0)); put('currency',currency,m.group(0))
    if f['cash_amount'] is None and 'pay_to_join' not in signals:
        m = re.search(r'\bbudget\s*(?:is|of|:)?\s*('+NUMBER+')',body,re.I)
        if m:
            # Hindi budget shorthand is INR; other currency-free numbers remain unknown.
            if re.search(r'\bhai\b|\bNamaste\b|\bhum\b',body,re.I):
                put('cash_amount',amount(m.group(1)),m.group(0));put('currency','INR',body)
    gifting = f['gift_value'] is not None and bool(re.search(r'in return|in exchange|gifting|barter',lower))
    if f['cash_amount'] is not None:
        put('payment_type','mixed' if gifting else 'cash')
    elif gifting:
        put('payment_type','gifting')
    categories = [(r'\bsmartphones?\b','smartphones'),(r'\bfantasy\s+(?:cricket|sports?)\b','fantasy_sports'),
                  (r'\bbetting\b','betting'),(r'\bgambling\b','gambling'),(r'\bcrypto\b','crypto'),
                  (r'\btrading[ -]tips?\b','trading_tips'),(r'\bskincare\b','skincare'),
                  (r'\bcosmetics?\b','cosmetics'),(r'\bbeauty\b','beauty')]
    for pattern,category in categories:
        m=re.search(pattern,text,re.I)
        if m: put('product_category',category,m.group(0));break
    year = date.fromisoformat(profile['today']).year
    m = re.search(r'(\d{1,2})\s*(?:-|–|to|and)\s*(\d{1,2})\s+('+MONTH_RE+r')(?:\s+(20\d{2}))?',body,re.I)
    if m:
        y=int(m.group(4) or year);month=MONTHS[m.group(3).lower()]
        try:
            put('window_start',date(y,month,int(m.group(1))).isoformat(),m.group(0))
            put('deadline',date(y,month,int(m.group(2))).isoformat(),m.group(0))
        except ValueError: pass
    else:
        m=re.search(r'(?:by|before|deadline|on)\s+(\d{1,2})\s+('+MONTH_RE+r')(?:\s+(20\d{2}))?',body,re.I)
        if m:
            try: put('deadline',date(int(m.group(3) or year),MONTHS[m.group(2).lower()],int(m.group(1))).isoformat(),m.group(0))
            except ValueError: pass
    m=re.search(r'within\s+\d+\s+(?:days?|weeks?)\s+of\s+delivery',body,re.I)
    if m: put('relative_deadline',m.group(0),m.group(0))
    m=re.search(r'(\d+)\s*months?\s+(?:of\s+)?(?:paid\s+)?usage',body,re.I)
    if m: put('usage_months',int(m.group(1)),m.group(0))
    put('perpetual_usage',bool(re.search(r'\bperpetual\b|\bin perpetuity\b',lower)))
    put('whitelisting',bool(re.search(r'\bwhitelist(?:ing)?\b',lower)))
    if f['usage_months'] is not None or f['perpetual_usage'] or f['whitelisting']:
        put('usage_text',next((s.strip() for s in re.split(r'(?<=[.!?])\s+',body) if re.search(r'usage|whitelist',s,re.I)),body))
    m=re.search(r'\b(?:fast payment|payment within \d+ days|net[ -]?\d+|\d+% advance)\b',body,re.I)
    if m: put('payment_terms',m.group(0),m.group(0))
    return validate_extraction({'facts': f, 'evidence': ev},email)
