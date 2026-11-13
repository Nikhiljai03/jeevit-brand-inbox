"""Shared pipeline; evaluation files are deliberately absent from this module."""
import hashlib
import json
import time
from copy import deepcopy
from .schemas import validate_inputs, validate_extraction
from .extraction import extract_rules, security_signals
from .grouping import group_records, mark_unresolved_updates
from .policy import assess, draft
from .provider import ProviderError, PROMPT_VERSION


def run(profile,inbox,provider=None,progress=None):
    validate_inputs(profile,inbox)
    started=time.perf_counter();records=[]
    for index,email in enumerate(inbox,1):
        before=time.perf_counter();record={'email_id':email['id'],'email':deepcopy(email),'status':'ok'}
        if progress:
            progress(f'[{index}/{len(inbox)}] Processing {email["id"]}...')
        try:
            signals=security_signals(email)
            if provider and not signals:
                if provider.fatal_error:
                    raise ProviderError(
                        f'{provider.name} unavailable; remaining requests skipped after a fatal provider error.',
                        fatal=True,
                    )
                record.update(provider.extract(email,profile));record['method']=provider.name
                record['model_facts']=deepcopy(provider.last_model_facts)
                record['model_evidence']=deepcopy(provider.last_model_evidence)
                record['model_reconciliations']=deepcopy(provider.last_reconciliations)
                record['field_sources']=deepcopy(provider.last_field_sources)
                # Independently observed security flags cannot be removed by the model.
            else:
                record.update(extract_rules(email,profile));record['method']='rules_safety' if provider else 'rules'
            validate_extraction({'facts':record['facts'],'evidence':record['evidence']},email)
        except (ProviderError,ValueError) as exc:
            record.update(
                status='error',error=str(exc),facts=None,evidence={},
                method=provider.name if provider else 'rules',
            )
        record['elapsed_ms']=round((time.perf_counter()-before)*1000,3)
        records.append(record)
        if progress:
            if record['status']=='error':
                progress(f'[{index}/{len(inbox)}] {email["id"]} failed: {record["error"]}')
            else:
                progress(f'[{index}/{len(inbox)}] {email["id"]} completed in {record["elapsed_ms"] / 1000:.1f}s')
    deals=[]
    groups=group_records(records)
    unresolved_updates=mark_unresolved_updates(records,groups)
    for group in groups:
        decision=assess(group,profile)
        row={'id':group['id'],'email_ids':[r['email_id'] for r in group['records']],
             'brand':group['terms'].get('brand'), 'terms':group['terms'],
             'contacts':[{'email_id':r['email_id'],'sender':r['email']['from']} for r in group['records']],
             'provenance':group['provenance'],'term_history':group['term_history'],'grouping_reasons':group['links'],
             'unresolved_update_email_ids':group.get('unresolved_update_email_ids',[]),
             'terms_current':not bool(group.get('unresolved_update_email_ids')),
             **decision,'draft_reply':draft(decision,group['terms'])}
        deals.append(row)
        for r in group['records']:
            r.update(category=decision['category'],deal_id=group['id'])
    for record in records:
        if record['status']=='error': record.update(category=None,deal_id=None)
    elapsed=time.perf_counter()-started
    payload=json.dumps({'profile':profile,'inbox':inbox},sort_keys=True,ensure_ascii=False)
    calls=getattr(provider,'calls',0)
    input_tokens=getattr(provider,'input_tokens',0)
    output_tokens=getattr(provider,'output_tokens',0)
    if provider and calls and provider.name=='api' and not getattr(provider,'_usage_complete',False):
        input_tokens=output_tokens=None
    elif provider and not calls:
        input_tokens=output_tokens=0
    mode={'ollama':'ollama_live','api':'api_live'}.get(
        getattr(provider,'name',None),'rules_offline'
    )
    reported_model=getattr(provider,'reported_model',None)
    return {'metadata':{'schema_version':'1.0','prompt_version':PROMPT_VERSION,'analysis_date':profile['today'],
        'creator_name':profile.get('name'),
        'mode':mode,'provider':getattr(provider,'name','rules'),'model':reported_model or getattr(provider,'model',None),
        'configured_model':getattr(provider,'model',None),
        'structured_output_mode':getattr(provider,'structured_output_mode',None),
        'status':'partial' if any(r['status']=='error' for r in records) else 'complete',
        'input_sha256':hashlib.sha256(payload.encode()).hexdigest(),'emails_total':len(inbox),
        'processed':sum(r['status']=='ok' for r in records),'elapsed_seconds':round(elapsed,6),
        'model_calls':calls,'model_retries':getattr(provider,'retries',0),
        'input_tokens':input_tokens,'output_tokens':output_tokens,
        'model_reconciliations':sum(len(r.get('model_reconciliations',[])) for r in records),
        'unresolved_campaign_updates':unresolved_updates,
        'api_cost_usd':None if getattr(provider,'name',None)=='api' else 0,
        'cost_note':(
            'Hosted API billing is not queried; cost is unknown and no price estimate is included.'
            if getattr(provider,'name',None)=='api' else
            'No paid API calls. Local compute/electricity excluded; rules mode uses no model.'
        ),
        'nothing_sent':True},'emails':records,'deals':deals}
