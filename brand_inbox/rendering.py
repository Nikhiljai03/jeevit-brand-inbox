"""Human-readable summaries and a read-only HTML view. No remote assets/scripts."""
import html
import json
from pathlib import Path


def safe(text):
    # Prevent email-controlled HTML / Markdown links from becoming active content.
    return html.escape(str(text),quote=True).replace('[','\\[').replace(']','\\]').replace('`','\\`').replace('\n',' ')


def summary(result):
    meta=result['metadata'];lines=['# Brand inbox — review queue','',
        f'Analysis date: **{meta["analysis_date"]}** · Mode: **{meta["mode"]}**',
        f'Processed **{meta["processed"]}/{meta["emails_total"]} emails** into **{len(result["deals"])} conversation groups**.',
        'Groups include suspicious messages and newsletters; they are not all commercial opportunities.',
        '**Drafts only. Nothing has been sent or booked.**','']
    order={'negotiate':0,'ask for details':1,'accept':2,'decline':3,'report':4,'ignore':5}
    for d in sorted(result['deals'],key=lambda x:order[x['action']]):
        lines += [f'## {safe(d["brand"] or d["email_ids"][0])} — {d["action"].upper()}',
                  f'Category: `{d["category"]}` · Sources: {", ".join(safe(x) for x in d["email_ids"])}','']
        if d['cash_inr'] is not None: lines.append(f'- Cash offer: INR {d["cash_inr"]:,.0f}.')
        if d['terms'].get('gift_value') is not None: lines.append(f'- Stated gift value: {d["terms"].get("gift_currency") or "currency unknown"} {d["terms"]["gift_value"]:,.0f} (not cash).' )
        if d['baseline_inr'] is not None: lines.append(f'- Rate-card baseline: INR {d["baseline_inr"]:,.0f}'+(' (partial).' if d['baseline_is_partial'] else '.'))
        if d['terms'].get('deadline'): lines.append('- Requested date: '+d['terms']['deadline']+'.')
        for r in d['risks']: lines.append('- **'+r['code']+'**: '+safe(r['reason']))
        for change in d['term_history']:
            if change['field'] in ('cash_amount','deliverables','deadline','usage_months'):
                lines.append(f'- Term update: {change["field"]}: {safe(change["old"])} → {safe(change["new"])} ({safe(change["new_source"]["email_id"])}).')
        if d['draft_reply']: lines += ['','**Draft reply:** '+safe(d['draft_reply'])]
        lines.append('')
    failures=[r for r in result['emails'] if r['status']=='error']
    if failures:
        lines += ['## Processing failures','']+[f'- {safe(r["email_id"])}: {safe(r["error"])}' for r in failures]
    lines += ['','## Interpretation limits','',
        'Offline rules are a narrow baseline, not an LLM. Quoted evidence does not prove semantic correctness.',
        'Review dates, payment terms and rights before agreeing. Domain suspicion is not verified reputation.']
    return '\n'.join(lines)+'\n'


_ACTION_LABELS = {
    'negotiate': 'Negotiate',
    'ask for details': 'Ask for details',
    'accept': 'Accept for review',
    'decline': 'Decline',
    'report': 'Report',
    'ignore': 'Ignore',
}
_FIELD_LABELS = {
    'brand': 'Brand',
    'campaign': 'Campaign',
    'currency': 'Cash currency',
    'cash_amount': 'Cash amount',
    'gift_value': 'Gift value',
    'gift_currency': 'Gift currency',
    'joining_fee': 'Joining fee',
    'joining_fee_currency': 'Joining-fee currency',
    'payment_type': 'Payment type',
    'deadline': 'Requested date',
    'window_start': 'Campaign start',
    'relative_deadline': 'Relative deadline',
    'usage_text': 'Usage rights',
    'usage_months': 'Usage duration (months)',
    'perpetual_usage': 'Perpetual usage',
    'whitelisting': 'Whitelisting',
    'payment_terms': 'Payment terms',
    'product_category': 'Product category',
    'deliverables': 'Deliverables',
    'newsletter': 'Newsletter',
    'followup': 'Follow-up',
    'attachment_missing': 'Missing attachment',
    'security_signals': 'Security signals',
}
_DELIVERABLE_LABELS = {
    'instagram_reel': 'Instagram reel',
    'instagram_story': 'Instagram story',
    'youtube_integration': 'YouTube integration',
    'youtube_dedicated_video': 'YouTube dedicated video',
    'youtube_shoutout': 'YouTube shoutout',
}


def _format_amount(value):
    if type(value) not in (int, float):
        return str(value)
    return f'{value:,.0f}' if float(value).is_integer() else f'{value:,.2f}'.rstrip('0').rstrip('.')


def _term_text(field, value):
    if field == 'deliverables' and isinstance(value, list):
        labels = []
        for item in value:
            if not isinstance(item, dict):
                continue
            quantity = item.get('quantity', '?')
            label = _DELIVERABLE_LABELS.get(item.get('kind'), item.get('kind', 'deliverable'))
            if quantity != 1 and isinstance(label, str):
                label += 'ies' if label.endswith('y') else 's'
            labels.append(f'{quantity} {label}')
        return ', '.join(labels) or 'Not specified'
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, list):
        return ', '.join(str(item) for item in value) or 'None recorded'
    if isinstance(value, (int, float)):
        return _format_amount(value)
    if value is None or value == '':
        return 'Not specified'
    return str(value)


def _money(currency, value):
    amount = _format_amount(value)
    return f'{currency} {amount}' if currency else f'{amount} (currency not specified)'


def _normalized_subject(value):
    import re
    return re.sub(r'[^a-z0-9]+', ' ', re.sub(r'^(?:(?:re|fw|fwd):\s*)+', '', value, flags=re.I).lower()).strip()


def _deal_update_ids(deal, records):
    ids = list(deal.get('unresolved_update_email_ids') or [])
    for record in records:
        if record.get('status') != 'error' or not record.get('could_be_campaign_update'):
            continue
        email = record.get('email') or {}
        for contact in deal.get('contacts', []):
            source = next((r.get('email', {}) for r in records if r.get('email_id') == contact.get('email_id')), {})
            if (
                source.get('from', '').casefold() == email.get('from', '').casefold()
                and _normalized_subject(source.get('subject', '')) == _normalized_subject(email.get('subject', ''))
            ):
                ids.append(record['email_id'])
                break
    return list(dict.fromkeys(ids))


def _display_title(deal, emails):
    if deal.get('brand'):
        return str(deal['brand'])
    email_ids = deal.get('email_ids') or []
    email = emails.get(email_ids[0], {}) if email_ids else {}
    source = email.get('email', {})
    subject = source.get('subject') or 'Unknown brand'
    sender = source.get('from')
    return f'{subject} — {sender}' if sender else str(subject)


def _cash_offer(deal):
    terms = deal.get('terms') or {}
    amount = terms.get('cash_amount')
    currency = terms.get('currency')
    equivalent = deal.get('cash_inr')
    if amount is None:
        return 'Not specified'
    original = _money(currency, amount)
    if equivalent is None:
        return original
    if currency == 'INR' and amount == equivalent:
        return original
    return f'{original} · INR equivalent {_money("INR", equivalent)}'


def _evidence_rows(deal, emails):
    terms = deal.get('terms') or {}
    provenance = deal.get('provenance') or {}
    rows = []
    for field, value in terms.items():
        label = _FIELD_LABELS.get(field, field.replace('_', ' ').capitalize())
        source = provenance.get(field) or {}
        quote = source.get('quote')
        source_id = source.get('email_id')
        if not quote and source_id in emails:
            quote = (emails[source_id].get('evidence') or {}).get(field)
        if not source_id and field in ('newsletter', 'security_signals'):
            source_id = next((item for item in deal.get('email_ids', []) if item in emails), None)
            if source_id:
                quote = quote or (emails[source_id].get('evidence') or {}).get(field)
        rows.append(
            '<tr><th scope="row">{}</th><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                html.escape(label),
                html.escape(_term_text(field, value)),
                html.escape(str(quote) if quote else 'No source quote recorded'),
                html.escape(str(source_id) if source_id else 'Source not recorded'),
            )
        )
    return ''.join(rows) or '<tr><td colspan="4">No extracted terms recorded.</td></tr>'


def _deal_card(deal, result, email_map):
    esc = html.escape
    title = _display_title(deal, email_map)
    action = _ACTION_LABELS.get(deal.get('action'), 'Review')
    action_class = 'action-' + (deal.get('action') or 'review').replace(' ', '-')
    ids = deal.get('email_ids') or []
    terms = deal.get('terms') or {}
    deliverables = _term_text('deliverables', terms.get('deliverables'))
    deadline = _term_text('deadline', terms.get('deadline'))
    if deadline == 'Not specified' and terms.get('relative_deadline'):
        deadline = str(terms['relative_deadline'])
    if deal.get('action') == 'negotiate' and deal.get('shortfall_inr') is not None and deal.get('shortfall_inr', 0) > 0:
        reason = f'Offer is {_money("INR", deal["shortfall_inr"])} below the rate-card baseline.'
    elif deal.get('risks'):
        reason = str(deal['risks'][0].get('reason') or 'A review risk was recorded.')
    else:
        reason = 'No additional risk was recorded in the analysis.'
    risks_html = ''.join(
        '<li><strong>{}</strong>: {}{}</li>'.format(
            esc(str(risk.get('severity', ''))).capitalize(),
            esc(risk.get('reason', 'Risk recorded.')),
            ' <span class="source-ref">Sources: {}</span>'.format(
                esc(', '.join(risk.get('source_email_ids') or []))
            ) if risk.get('source_email_ids') else '',
        )
        for risk in deal.get('risks', [])
    ) or '<li>No risks recorded.</li>'
    missing = ', '.join(str(item) for item in (deal.get('missing_fields') or [])) or 'None recorded'
    baseline = _money('INR', deal['baseline_inr']) if deal.get('baseline_inr') is not None else 'Not available'
    shortfall = _money('INR', deal['shortfall_inr']) if deal.get('shortfall_inr') is not None else 'Not available'
    rights = _term_text('usage_text', terms.get('usage_text'))
    if rights == 'Not specified' and terms.get('usage_months') is not None:
        rights = f'{_term_text("usage_months", terms["usage_months"])} months'
    payment = _term_text('payment_terms', terms.get('payment_terms'))
    update_ids = _deal_update_ids(deal, result.get('emails', []))
    incomplete = deal.get('terms_current') is False or bool(update_ids)
    warning = ''
    if incomplete:
        affected = ', '.join(update_ids) or 'an unresolved campaign update'
        warning = (
            '<p class="notice notice-danger"><strong>Incomplete analysis — terms may be outdated.</strong> '
            'Potentially related update {}</p>'.format(esc(affected))
        )
    history = []
    for email_id in ids:
        record = email_map.get(email_id)
        if not record:
            continue
        source = record.get('email') or {}
        history.append(
            '<li><h4>{} · {}</h4><p class="muted">{}</p><p>{}</p></li>'.format(
                esc(email_id), esc(source.get('received_at', 'Date not recorded')),
                esc(source.get('subject', 'Subject not recorded')),
                esc(source.get('body', 'Message text not recorded')),
            )
        )
    changes = ''.join(
        '<li><strong>{}</strong>: {} → {} (updated in {})</li>'.format(
            esc(_FIELD_LABELS.get(change.get('field'), change.get('field', 'Term'))),
            esc(_term_text(change.get('field', ''), change.get('old'))),
            esc(_term_text(change.get('field', ''), change.get('new'))),
            esc((change.get('new_source') or {}).get('email_id', 'source not recorded')),
        )
        for change in deal.get('term_history', [])
    ) or '<li>No explicit term changes recorded.</li>'
    grouping = ''.join(
        '<li>{}: {}</li>'.format(esc(link.get('email_id', '')), esc(link.get('reason', '')))
        for link in deal.get('grouping_reasons', [])
    )
    grouping = '<ul>{}</ul>'.format(grouping) if grouping else '<p>No additional grouping note.</p>'
    compact = {
        'deal': deal,
        'source_emails': [email_map[email_id] for email_id in ids if email_id in email_map],
    }
    gift_value = terms.get('gift_value')
    gift_text = (
        _money(terms.get('gift_currency'), gift_value) + ' (not cash)'
        if gift_value is not None else 'Not specified'
    )
    return (
        '<article class="review-item"><div class="item-heading"><div><p class="eyebrow">{}</p>'
        '<h3>{}</h3></div><span class="badge {}">{}</span></div>{}'
        '<div class="quick-facts"><p><span>Cash offer</span><strong>{}</strong></p>'
        '<p><span>Gift value</span><strong>{}</strong></p>'
        '<p><span>Deliverables</span><strong>{}</strong></p>'
        '<p><span>Requested date</span><strong>{}</strong></p></div>'
        '<p class="reason"><strong>Why:</strong> {}</p>'
        '<p class="muted source-line">{} message{} · Sources: {}</p>'
        '<details class="item-details"><summary>Deal details</summary><dl>'
        '<dt>Latest terms</dt><dd>{}</dd><dt>Rate-card baseline</dt><dd>{}{}</dd>'
        '<dt>Shortfall</dt><dd>{}</dd><dt>Usage rights</dt><dd>{}</dd>'
        '<dt>Payment terms</dt><dd>{}</dd><dt>Missing information</dt><dd>{}</dd></dl></details>'
        '<details class="item-details"><summary>Why this recommendation</summary>{}<p>{}</p>{}</details>'
        '<details class="item-details"><summary>Conversation history</summary><ol class="history">{}</ol>'
        '<h4>Term changes</h4><ul>{}</ul></details>'
        '<details class="item-details"><summary>Source evidence</summary>'
        '<div class="table-wrap"><table><thead><tr><th>Field</th><th>Selected value</th>'
        '<th>Source quote</th><th>Source</th></tr></thead><tbody>{}</tbody></table></div></details>'
        '{}<details class="technical"><summary>Technical JSON</summary><pre>{}</pre></details>'
        '</article>'
    ).format(
        esc(str(deal.get('category', '')).replace('_', ' ').title()),
        esc(title), esc(action_class), esc(action), warning,
        esc(_cash_offer(deal)), esc(gift_text), esc(deliverables), esc(deadline),
        esc(reason), len(ids), '' if len(ids) == 1 else 's', esc(', '.join(ids) or 'None'),
        esc('; '.join(f'{_FIELD_LABELS.get(k, k.replace("_", " ").capitalize())}: {_term_text(k, v)}'
                      for k, v in terms.items()) or 'No latest terms recorded.'),
        esc(baseline), ' (partial lower bound)' if deal.get('baseline_is_partial') else '',
        esc(shortfall), esc(rights), esc(payment), esc(missing),
        '<ul>{}</ul>'.format(risks_html), esc(reason), grouping,
        ''.join(history) or '<li>No source messages recorded.</li>', changes,
        _evidence_rows(deal, email_map),
        '<details class="draft"><summary>Draft reply · review only</summary><blockquote>{}</blockquote></details>'.format(
            esc(deal['draft_reply'])
        ) if deal.get('draft_reply') else '',
        esc(json.dumps(compact, indent=2, ensure_ascii=False)),
    )


def _failure_card(record):
    esc = html.escape
    email = record.get('email') or {}
    title = email.get('subject') or 'Unknown subject'
    sender = email.get('from') or 'Sender not recorded'
    impact = (
        '<p class="notice notice-danger">This failed message may contain a campaign update; '
        'related earlier terms must not be treated as confidently current.</p>'
        if record.get('could_be_campaign_update') else ''
    )
    return (
        '<article class="review-item failed-item"><div class="item-heading"><div>'
        '<p class="eyebrow">Analysis failed · {}</p><h3>{}</h3></div>'
        '<span class="badge badge-error">Needs review</span></div>'
        '<p class="muted">{}</p>{}<p class="error-text">{}</p>'
        '<details class="item-details"><summary>Source message</summary><p>{}</p></details>'
        '</article>'
    ).format(
        esc(record.get('email_id', '')), esc(title), esc(sender), impact,
        esc(record.get('error', 'Processing failed; no further details recorded.')),
        esc(email.get('body', 'Message text not recorded.')),
    )


def html_report(result):
    esc = html.escape
    meta = result.get('metadata') or {}
    deals = result.get('deals') or []
    emails = result.get('emails') or []
    email_map = {record.get('email_id'): record for record in emails}
    failures = [record for record in emails if record.get('status') == 'error']
    suspicious = [deal for deal in deals if deal.get('category') == 'scam_or_phishing' or deal.get('action') == 'report']
    ignored = [deal for deal in deals if deal.get('action') == 'ignore']
    declined = [deal for deal in deals if deal.get('action') == 'decline']
    assigned = {id(deal) for deal in suspicious + ignored + declined}
    response = [deal for deal in deals if id(deal) not in assigned]
    buckets = (
        ('Needs your response', response),
        ('Decline', declined),
        ('Suspicious messages', suspicious),
        ('Ignored newsletters', ignored),
    )
    sections = []
    for heading, items in buckets:
        cards = ''.join(_deal_card(deal, result, email_map) for deal in items)
        if heading == 'Needs your response':
            cards += ''.join(_failure_card(record) for record in failures)
        sections.append(
            '<section class="queue-section"><h2>{} <span class="count">{}</span></h2>{}</section>'.format(
                esc(heading), len(items) + (len(failures) if heading == 'Needs your response' else 0),
                cards or '<p class="empty">None in this section.</p>',
            )
        )
    negotiations = sum(deal.get('action') == 'negotiate' for deal in deals)
    requests = sum(deal.get('action') == 'ask for details' for deal in deals)
    creator = meta.get('creator_name')
    creator_line = f'<p class="creator">{esc(creator)}</p>' if creator else ''
    coverage = '{}/{} emails processed'.format(
        meta.get('processed', 0), meta.get('emails_total', len(emails))
    )
    failures_block = ''
    if failures:
        failure_rows = ''.join(
            '<li><strong>{}</strong>: {}{}</li>'.format(
                esc(record.get('email_id', '')),
                esc(record.get('error', 'Processing failed.')),
                ' <span>Potential campaign update; related terms may be stale.</span>'
                if record.get('could_be_campaign_update') else '',
            )
            for record in failures
        )
        failures_block = (
            '<aside class="notice notice-danger"><h2>Processing needs attention</h2>'
            '<p>{} email{} failed; affected conversations may have outdated terms.</p><ul>{}</ul></aside>'
        ).format(len(failures), '' if len(failures) == 1 else 's', failure_rows)
    run_details = {
        key: meta.get(key) for key in (
            'mode', 'provider', 'model', 'configured_model', 'structured_output_mode',
            'elapsed_seconds', 'model_calls', 'model_retries', 'input_tokens',
            'output_tokens', 'api_cost_usd', 'cost_note',
        ) if key in meta
    }
    run_rows = ''.join(
        '<dt>{}</dt><dd>{}</dd>'.format(
            esc(key.replace('_', ' ').capitalize()),
            esc('Unknown' if value is None else str(value)),
        ) for key, value in run_details.items()
    )
    status_text = 'Complete' if not failures else 'Partial — failed messages need review'
    template = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Brand deal inbox</title>
<style>
:root{color-scheme:light;--ink:#172b35;--muted:#52666e;--line:#d8e1e3;--paper:#f4f7f6;--teal:#087f78;--teal-soft:#e7f4f2;--amber:#8b4b08;--amber-bg:#fff4df;--red:#9c2929;--red-bg:#fff0ef}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}main{max-width:1060px;margin:0 auto;padding:32px 28px 56px}
a{color:inherit}a:focus-visible,summary:focus-visible{outline:3px solid #087f78;outline-offset:3px}
h1,h2,h3,h4,p{margin-top:0}h1{font-size:clamp(28px,4vw,36px);line-height:1.2;letter-spacing:-.025em;margin:4px 0 8px}h2{font-size:21px;line-height:1.3;margin:0 0 14px}h3{font-size:20px;line-height:1.3;margin:0}h4{font-size:15px;margin:16px 0 5px}
.topline,.eyebrow{font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--teal);font-weight:750;margin:0 0 6px}
.creator{font-size:18px;font-weight:650;margin:0 0 10px}.header-meta{color:var(--muted);margin:0 0 5px}.draft-status{display:inline-block;font-size:13px;font-weight:650;color:#315b58;background:var(--teal-soft);padding:4px 9px;border-radius:4px;margin:8px 0 14px}
header{padding-bottom:18px;border-bottom:1px solid var(--line);margin-bottom:20px}.run-details{margin:8px 0;color:var(--muted);font-size:14px}.run-details summary,details summary{cursor:pointer;font-weight:650}
.run-details dl,.item-details dl{display:grid;grid-template-columns:minmax(150px,220px) 1fr;gap:4px 14px;margin:12px 0}.run-details dt,.item-details dt{font-weight:650}.run-details dd,.item-details dd{margin:0;overflow-wrap:anywhere}
.summary-strip{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:20px 0 28px}.metric{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px 14px}.metric strong{display:block;font-size:22px;line-height:1.2}.metric span{display:block;color:var(--muted);font-size:13px;margin-top:3px}
.notice{border-radius:7px;padding:13px 16px;margin:16px 0}.notice h2{margin-bottom:5px}.notice ul{margin:8px 0 0;padding-left:22px}.notice-danger{color:#692121;background:var(--red-bg);border:1px solid #edc7c5}
.queue-section{margin:28px 0}.queue-section>h2{display:flex;align-items:center;gap:9px;padding-bottom:9px;border-bottom:1px solid var(--line)}.count{font-size:13px;color:var(--muted);font-weight:550}
.review-item{background:#fff;border:1px solid var(--line);border-radius:9px;padding:18px 20px;margin:12px 0;overflow-wrap:anywhere}.item-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:16px}.eyebrow{margin-bottom:4px}.badge{display:inline-block;border:1px solid #b9d6d2;background:var(--teal-soft);color:#075b56;border-radius:5px;padding:4px 9px;font-size:13px;font-weight:750;white-space:nowrap}.action-decline,.action-report,.badge-error{background:var(--red-bg);border-color:#e5b7b5;color:#762323}.action-ask-for-details{background:var(--amber-bg);border-color:#e7d0a6;color:#70400c}.action-ignore{background:#eef1f1;border-color:#d6dede;color:#435158}
.quick-facts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px 18px;margin:17px 0 9px}.quick-facts p{margin:0;min-width:0}.quick-facts span{display:block;color:var(--muted);font-size:12px;font-weight:650;margin-bottom:2px}.quick-facts strong{display:block;font-size:15px;line-height:1.4}.reason{margin:12px 0 5px}.source-line{margin:0 0 12px}.muted,.source-ref{color:var(--muted);font-size:13px}.source-ref{font-weight:500}
.item-details{border-top:1px solid #edf0f0;padding-top:10px;margin-top:10px}.item-details summary{color:#23434a}.item-details p{margin:8px 0}.item-details ul,.item-details ol{padding-left:22px}.history li{margin:12px 0}.history p{margin:3px 0}
.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;margin-top:10px}th,td{text-align:left;vertical-align:top;padding:8px 9px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}th{font-weight:700;background:#f7f9f9}
.draft blockquote{margin:10px 0 0;padding:12px 14px;border-left:3px solid var(--teal);background:#f5faf9;white-space:pre-wrap}.technical{margin-top:10px;font-size:13px;color:var(--muted)}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:360px;overflow:auto;background:#f5f7f7;padding:12px;border-radius:5px;font:12px/1.5 ui-monospace,Consolas,monospace}.failed-item .error-text{color:#762323;font-weight:600}.empty{color:var(--muted);background:#fff;border:1px dashed var(--line);border-radius:7px;padding:12px 15px}
footer{border-top:1px solid var(--line);margin-top:36px;padding-top:14px;color:var(--muted);font-size:13px}
@media(max-width:720px){main{padding:22px 16px 40px}.summary-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.metric:last-child{grid-column:span 2}.quick-facts{grid-template-columns:repeat(2,minmax(0,1fr))}.review-item{padding:15px}.item-heading{align-items:flex-start}.run-details dl,.item-details dl{grid-template-columns:1fr;gap:0}.item-details dd{margin-bottom:8px}}
@media(max-width:390px){.quick-facts{grid-template-columns:1fr}.item-heading{display:block}.badge{margin-top:9px}}
</style>
</head>
<body><main>
<header><p class="topline">Creator review queue</p><h1>Brand deal inbox</h1>__CREATOR__
<p class="header-meta">__ANALYSIS_DATE__ · __COVERAGE__ · __STATUS__</p>
<p class="draft-status">Drafts only · Nothing sent</p>
<details class="run-details"><summary>Run details</summary><dl>__RUN_ROWS__</dl></details>
</header>
__FAILURES_BLOCK__
<section class="summary-strip" aria-label="Inbox summary">
<div class="metric"><strong>__PROCESSED__/__TOTAL__</strong><span>Emails processed</span></div>
<div class="metric"><strong>__GROUP_COUNT__</strong><span>Conversation groups</span></div>
<div class="metric"><strong>__NEGOTIATIONS__</strong><span>Negotiations</span></div>
<div class="metric"><strong>__REQUESTS__</strong><span>Requests for information</span></div>
<div class="metric"><strong>__SUSPICIOUS_COUNT__</strong><span>Suspicious conversations</span></div>
</section>
__SECTIONS__
<footer>Recommendations are for review, not commitments. Terms shown here come from the saved analysis; unknown values remain unspecified.</footer>
</main></body></html>'''
    replacements = {
        '__CREATOR__': creator_line,
        '__ANALYSIS_DATE__': esc(str(meta.get('analysis_date') or 'Analysis date not recorded')),
        '__COVERAGE__': esc(coverage),
        '__STATUS__': esc(status_text),
        '__RUN_ROWS__': run_rows,
        '__FAILURES_BLOCK__': failures_block,
        '__PROCESSED__': str(meta.get('processed', 0)),
        '__TOTAL__': str(meta.get('emails_total', len(emails))),
        '__GROUP_COUNT__': str(len(deals)),
        '__NEGOTIATIONS__': str(negotiations),
        '__REQUESTS__': str(requests),
        '__SUSPICIOUS_COUNT__': str(len(suspicious)),
        '__SECTIONS__': ''.join(sections),
    }
    for token, value in replacements.items():
        template = template.replace(token, value)
    return template


def write_outputs(result,out):
    path=Path(out);path.mkdir(parents=True,exist_ok=True)
    for name,value in [('analysis.json',json.dumps(result,indent=2,ensure_ascii=False)+'\n'),('summary.md',summary(result)),('report.html',html_report(result))]:
        target=path/name;temp=target.with_suffix(target.suffix+'.tmp');temp.write_text(value,encoding='utf-8');temp.replace(target)
