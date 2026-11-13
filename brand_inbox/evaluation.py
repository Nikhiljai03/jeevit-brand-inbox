"""Evaluation-only code. Gold labels never enter the runtime pipeline."""
from collections import Counter
from itertools import combinations


def pairs(groups):
    return {tuple(sorted(pair)) for group in groups for pair in combinations(group,2)}


def same(expected,actual):
    if isinstance(expected,list) and isinstance(actual,list):
        return sorted(map(str,expected))==sorted(map(str,actual))
    return expected==actual


def evaluate(expected,actual):
    rows={r['email_id']:r for r in actual['emails']};mismatches=[];confusion=Counter()
    correct=processed=fields_total=fields_correct=0
    for gold in expected['emails']:
        row=rows.get(gold['id'],{});ok=row.get('status')=='ok';processed+=ok
        predicted=row.get('category') if ok else '<processing_error>'
        confusion[(gold['category'],predicted)]+=1
        if predicted==gold['category']: correct+=1
        else: mismatches.append({'id':gold['id'],'check':'category','expected':gold['category'],'actual':predicted})
        facts=row.get('facts') or {}
        for key,value in gold.get('fields',{}).items():
            fields_total+=1
            hit=ok and key in facts and same(value,facts.get(key));fields_correct+=hit
            if not hit: mismatches.append({'id':gold['id'],'check':'field:'+key,'expected':value,'actual':facts.get(key)})
    expected_groups={frozenset(g) for g in expected.get('groups',[])}
    predicted_groups={frozenset(d['email_ids']) for d in actual['deals']}
    ep=pairs(expected.get('groups',[]));ap=pairs([d['email_ids'] for d in actual['deals']]);tp=len(ep&ap)
    checks=passed=0;by_group={frozenset(d['email_ids']):d for d in actual['deals']}
    for gold in expected.get('deals',[]):
        row=by_group.get(frozenset(gold['members']),{});tests=[('action',gold['action'],row.get('action'))]
        codes={r['code'] for r in row.get('risks',[])}
        tests += [('risk:'+code,True,code in codes) for code in gold.get('risks',[])]
        for k,v in gold.get('fields',{}).items(): tests.append(('deal_field:'+k,v,row.get(k,row.get('terms',{}).get(k))))
        if gold.get('draft_is_null'): tests.append(('draft_is_null',True,bool(row) and row.get('draft_reply') is None))
        for key,want,got in tests:
            checks+=1
            if same(want,got): passed+=1
            else: mismatches.append({'id':','.join(gold['members']),'check':key,'expected':want,'actual':got})
    total=len(expected['emails'])
    return {'mode':actual['metadata']['mode'],'model':actual['metadata']['model'],
            'coverage':{'processed':processed,'total':total},
            'categories':{'correct':correct,'total':total,'accuracy_all_inputs':correct/total if total else None,
                          'accuracy_processed':correct/processed if processed else None},
            'key_fields':{'correct':fields_correct,'total':fields_total},
            'grouping':{'exact_match':expected_groups==predicted_groups,'correct_groups':len(expected_groups&predicted_groups),
                        'expected_groups':len(expected_groups),'predicted_groups':len(predicted_groups),
                        'pair_precision':tp/len(ap) if ap else (1.0 if not ep else 0.0),'pair_recall':tp/len(ep) if ep else 1.0},
            'deal_checks':{'passed':passed,'total':checks},
            'confusion_matrix':[{'expected':k[0],'predicted':k[1],'count':v} for k,v in sorted(confusion.items())],
            'mismatches':mismatches,'interpretation':'Development fixture accuracy, not blind generalization. No live-model claim for rules_offline.',
            'normalization':'Numbers compare numerically; strings exact; lists order-insensitive. Risks checked for expected presence. Processing failures count against all-input accuracy.'}


def report(result):
    c=result['categories'];f=result['key_fields'];d=result['deal_checks'];cov=result['coverage']
    accuracy='not measurable' if c['accuracy_processed'] is None else f'{c["accuracy_processed"]:.1%}'
    lines=['# Evaluation report','',f'Mode: **{result["mode"]}** · Model: {result["model"] or "none"}',
           f'- Coverage: {cov["processed"]}/{cov["total"]}',f'- Category correctness: {c["correct"]}/{c["total"]}; processed-only accuracy: {accuracy}',
           f'- Key fields: {f["correct"]}/{f["total"]}',f'- Exact grouping: {result["grouping"]["exact_match"]}',
           f'- Deal/risk/action checks: {d["passed"]}/{d["total"]}','',result['interpretation'],'',result['normalization'],'','## Mismatches','']
    if not result['mismatches']: lines.append('No mismatches on these checks. This does not establish generalization.')
    for item in result['mismatches']: lines.append(f'- {item["id"]} / {item["check"]}: expected `{item["expected"]}`; actual `{item["actual"]}`.')
    lines+=['','## Confusion matrix','', '| Expected | Predicted | Count |','|---|---|---:|']
    for x in result['confusion_matrix']: lines.append(f'| {x["expected"]} | {x["predicted"]} | {x["count"]} |')
    return '\n'.join(lines)+'\n'
