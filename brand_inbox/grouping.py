"""Conservative campaign resolution and explicit field-level term history."""
import re
from copy import deepcopy
from datetime import datetime


def normalized(text):
    return re.sub(r'[^a-z0-9]+',' ',text.lower()).strip()


def subject_key(text):
    return normalized(re.sub(r'^(?:(?:re|fw|fwd):\s*)+','',text,flags=re.I))


def potential_campaign_update(email):
    subject=email['subject']
    body=email['body']
    return bool(
        re.match(r'^\s*(?:re|fw|fwd):',subject,re.I)
        or re.search(
            r'\b(?:follow(?:ing)? up|revised?\s+(?:budget|offer|terms?)|'
            r'updated?\s+(?:budget|offer|terms?)|same deliverables|'
            r'everything else remains unchanged|terms? remain unchanged)\b',
            body,re.I,
        )
    )


def compatible(a,b):
    # Different explicit schedules or campaign names are evidence against merging.
    for key in ('deadline','window_start'):
        if a.get(key) and b.get(key) and a[key]!=b[key]: return False
    if a.get('campaign') and b.get('campaign') and normalized(a['campaign'])!=normalized(b['campaign']):
        # SPF serum vs new SPF serum are still compatible.
        aa,bb=set(normalized(a['campaign']).split()),set(normalized(b['campaign']).split())
        if len(aa&bb)<2: return False
    return True


def can_link(record, group):
    e,f=record['email'],record['facts']; terms=group['terms']
    if f['security_signals'] or f['newsletter'] or group['blocked']: return None
    if not compatible(f,terms): return None
    for old in group['records']:
        oe,of=old['email'],old['facts']
        if e['from'].lower()==oe['from'].lower() and subject_key(e['subject'])==subject_key(oe['subject']) and f['followup']:
            return 'same sender + normalized subject + explicit follow-up'
    brand=f.get('brand');prev=terms.get('brand')
    if brand and prev and normalized(brand)==normalized(prev) and f['followup']:
        shared_scope = bool(f['deliverables'] and f['deliverables']==terms.get('deliverables'))
        shared_date = bool(f['deadline'] and f['deadline']==terms.get('deadline'))
        scope_inherited = not f['deliverables']
        if (shared_scope or scope_inherited) and shared_date:
            return 'same brand + explicit reference + matching scope and schedule'
    return None


def mark_unresolved_updates(records, groups):
    unresolved=[]
    for record in records:
        if record['status']!='error' or not potential_campaign_update(record['email']):
            continue
        email=record['email']
        key=subject_key(email['subject'])
        same_thread=[
            group for group in groups
            if any(
                old['email']['from'].casefold()==email['from'].casefold()
                and subject_key(old['email']['subject'])==key
                for old in group['records']
            )
        ]
        if len(same_thread)==1:
            same_thread[0].setdefault('unresolved_update_email_ids',[]).append(record['email_id'])
        elif len(same_thread)>1:
            for group in same_thread:
                group.setdefault('unresolved_update_email_ids',[]).append(record['email_id'])
        unresolved.append(record['email_id'])
        record['could_be_campaign_update']=True
    return unresolved


def group_records(records):
    groups=[]
    for record in sorted((r for r in records if r['status']=='ok'),key=lambda r:(datetime.fromisoformat(r['email']['received_at']),r['email']['id'])):
        candidates=[(g,can_link(record,g)) for g in groups]
        candidates=[(g,reason) for g,reason in candidates if reason]
        if len(candidates)==1:
            g,reason=candidates[0]
            g['links'].append({'email_id':record['email']['id'],'reason':reason})
        else:
            g={'id':f'D-{len(groups)+1:02d}','records':[],'terms':{},'provenance':{},'term_history':[],
               'links':[],'unresolved_update_email_ids':[],
               'grouping_warning':'Multiple plausible campaigns; kept separate.' if len(candidates)>1 else None,
               'blocked':bool(record['facts']['security_signals'] or record['facts']['newsletter'])}
            groups.append(g)
        g['records'].append(record)
        for field,value in record['facts'].items():
            # false means unstated in this schema, not an explicit retraction.
            if value is None or value is False or value==[]: continue
            prior=g['terms'].get(field)
            source={'email_id':record['email']['id'],'received_at':record['email']['received_at'],
                    'quote':record['evidence'].get(field),
                    'method':record.get('field_sources',{}).get(field,record['method'])}
            if prior is not None and prior!=value:
                g['term_history'].append({'field':field,'old':deepcopy(prior),'new':deepcopy(value),
                                          'old_source':g['provenance'][field],'new_source':source})
            g['terms'][field]=deepcopy(value);g['provenance'][field]=source
    return groups
