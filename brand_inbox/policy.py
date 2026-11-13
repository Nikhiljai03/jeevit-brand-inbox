"""Deterministic business decisions. No model is allowed to override these."""
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


def rounded(value):
    return float(Decimal(str(value)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))


def usd_rate(profile):
    match=re.search(r'1\s*USD\s*=\s*(\d+(?:\.\d+)?)\s*INR',profile.get('currency_note',''),re.I)
    return Decimal(match.group(1)) if match else None


def assess(group,profile):
    t=group['terms'];today=date.fromisoformat(profile['today']);risks=[]
    def flag(code,reason,severity='medium',fields=()):
        refs={group['provenance'][k]['email_id'] for k in fields if k in group['provenance']}
        risks.append({'code':code,'severity':severity,'reason':reason,'source_email_ids':sorted(refs)})
    for signal in t.get('security_signals',[]):
        flag(signal,{'prompt_injection':'Email contains assistant-directed instructions; quarantined as untrusted.',
                     'suspected_phishing':'Account threat combined with a verification link; suspected phishing, not externally verified.',
                     'pay_to_join':'Sender asks the creator to pay to join or unlock a campaign.'}[signal],'high',('security_signals',))
    rules=' '.join(profile.get('content_rules',[])).lower()
    category=t.get('product_category')
    prohibited={'fantasy_sports':('fantasy','fantasy-sports'),'gambling':('gambling',),'betting':('betting',),
                'crypto':('crypto',),'trading_tips':('trading-tip','trading tip')}
    if category in prohibited and any(word in rules for word in prohibited[category]):
        flag('prohibited_category',f'The creator content rules prohibit {category.replace("_"," ")}.','high',('product_category',))
    for contract in profile.get('current_exclusivity',[]):
        if category and category.lower()==contract['category'].lower() and today<=date.fromisoformat(contract['until']):
            # A campaign beginning entirely after expiry is not an overlap.
            start=t.get('window_start')
            if (not start or date.fromisoformat(start)<=date.fromisoformat(contract['until'])) and (
                    not t.get('brand') or t['brand'].casefold()!=contract['brand'].casefold()):
                flag('exclusivity_conflict',f'Active {contract["category"]} exclusivity with {contract["brand"]} through {contract["until"]}.','high',('product_category','deadline'))
    baseline=Decimal(0);unpriced=[]
    for item in t.get('deliverables',[]):
        rate=profile['base_rates_inr'].get(item['kind'])
        if rate is None: unpriced.append(item['kind'])
        else: baseline+=Decimal(str(rate))*item['quantity']
    cash=t.get('cash_amount');currency=t.get('currency');cash_inr=None
    if cash is not None:
        if currency=='INR': cash_inr=Decimal(str(cash))
        elif currency=='USD' and usd_rate(profile) is not None: cash_inr=Decimal(str(cash))*usd_rate(profile)
        else: flag('unknown_conversion','Cash currency or its profile exchange rate is unavailable.',fields=('cash_amount','currency'))
    shortfall=max(Decimal(0),baseline-cash_inr) if cash_inr is not None else None
    if unpriced: flag('unpriced_deliverable','No profile rate for: '+', '.join(unpriced)+'. Baseline is a partial lower bound.',fields=('deliverables',))
    if shortfall and shortfall>0:
        flag('below_rate',f'Offer is INR {shortfall:,.0f} below the INR {baseline:,.0f} rate-card baseline.',fields=('cash_amount','deliverables'))
    if t.get('payment_type')=='gifting':
        flag('gifting_only','Product value is not cash. Discuss a paid arrangement; the profile does not categorically prohibit barter.',fields=('gift_value','payment_type'))
    included=re.search(r'(\d+)\s*months?',profile.get('usage_rights_policy',''),re.I)
    included_months=int(included.group(1)) if included else None
    if t.get('perpetual_usage') or (included_months is not None and t.get('usage_months',0)>included_months):
        flag('extended_usage','Requested usage exceeds the included policy; negotiate scope and a separate price. No invented surcharge.',fields=('usage_months','perpetual_usage'))
    if t.get('whitelisting'): flag('whitelisting','Advertising through the creator handle needs explicit scope, duration and approval.',fields=('whitelisting',))
    if t.get('deadline') and date.fromisoformat(t['deadline'])<today:
        flag('expired_deadline',f'Requested date {t["deadline"]} is before analysis date {today.isoformat()}.','high',('deadline',))
    if t.get('relative_deadline'):
        flag('relative_deadline','Deadline depends on an unknown delivery date; confirm the anchor date.',fields=('relative_deadline',))
    if t.get('attachment_missing'):
        flag('attachment_unavailable','Email refers to an attachment, but no attachment contents were supplied.',fields=('attachment_missing',))
    if group.get('unresolved_update_email_ids'):
        ids=', '.join(group['unresolved_update_email_ids'])
        flag('incomplete_analysis',f'Possible campaign update {ids} failed extraction; these terms may no longer be current.')
    missing=[]
    if not t.get('deliverables'): missing.append('deliverables')
    if cash is None and t.get('payment_type')!='gifting': missing.append('budget and currency')
    if not t.get('deadline') and not t.get('relative_deadline'): missing.append('timeline')
    if not t.get('usage_text'): missing.append('usage rights')
    if not t.get('payment_terms') and t.get('payment_type')!='gifting': missing.append('payment schedule')
    suspicious=bool(t.get('security_signals'))
    if missing and not suspicious and not t.get('newsletter'):
        flag('missing_terms','Confirm: '+', '.join(missing)+'.')
    if group['grouping_warning']: flag('ambiguous_grouping',group['grouping_warning'])
    codes={r['code'] for r in risks}
    concrete=bool(t.get('deliverables') and (cash is not None or t.get('payment_type')=='gifting'))
    if suspicious: cat,action='scam_or_phishing','report'
    elif codes & {'prohibited_category','exclusivity_conflict'}: cat,action='not_a_fit','decline'
    elif t.get('newsletter'): cat,action='spam','ignore'
    else:
        cat='deal_offer' if concrete else 'needs_more_info'
        if ('expired_deadline' in codes or not concrete or 'ambiguous_grouping' in codes
                or 'incomplete_analysis' in codes): action='ask for details'
        elif codes & {'below_rate','gifting_only','extended_usage','whitelisting'}: action='negotiate'
        elif missing or unpriced or codes & {'unknown_conversion','relative_deadline'}: action='ask for details'
        else: action='accept'
    return {'category':cat,'action':action,'risks':risks,'missing_fields':missing,
            'baseline_inr':rounded(baseline) if t.get('deliverables') else None,
            'baseline_is_partial':bool(unpriced),'cash_inr':rounded(cash_inr) if cash_inr is not None else None,
            'shortfall_inr':rounded(shortfall) if shortfall is not None else None,
            'shortfall_pct':rounded(shortfall/baseline*100) if shortfall is not None and baseline else None}


def draft(decision,terms):
    """Fixed templates: no arbitrary model prose or private details can enter drafts."""
    action=decision['action'];codes={r['code'] for r in decision['risks']}
    if action in ('ignore','report'): return None
    if action=='decline': return 'Thanks for reaching out. I’m unable to take this campaign forward because it conflicts with my current content guidelines or brand commitments.'
    if 'expired_deadline' in codes: return 'Thanks for the brief. The requested publication date has already passed. Could you share an updated timeline and confirm the current campaign terms?'
    if 'attachment_unavailable' in codes: return 'Thanks for reaching out. I couldn’t access the brief here. Please resend it or paste the deliverables, budget, timeline and usage requirements into your reply.'
    if action=='accept': return 'Thanks for the clear proposal. The stated scope and fee work for me in principle. Please send the agreement for my review before we confirm the booking.'
    pieces=['Thanks for reaching out!']
    if 'below_rate' in codes or 'gifting_only' in codes:
        prefix='My base fee for the priced deliverables is' if decision['baseline_is_partial'] else 'My base fee for this scope is'
        pieces.append(f'{prefix} INR {decision["baseline_inr"]:,.0f}. Would a paid budget at this level work for you?')
    if codes & {'extended_usage','whitelisting'}:
        pieces.append('Please confirm the ad channels, usage duration and whitelisting scope so we can agree a separate rights fee.')
    if decision['missing_fields']:
        pieces.append('Please also confirm '+', '.join(decision['missing_fields'])+'.')
    if len(pieces)==1: pieces.append('Could you share the full scope, budget and timeline so I can review the proposal?')
    return ' '.join(pieces)
