import argparse
import json
import os
import sys
from pathlib import Path
from .pipeline import run
from .provider import Ollama, OpenAICompatibleAPI
from .rendering import write_outputs
from .evaluation import evaluate, report


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main(argv=None):
    p=argparse.ArgumentParser(description='Review creator brand emails. Nothing is sent.')
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('analyze',help='Analyze using offline rules, local Ollama, or a hosted API.')
    a.add_argument('--profile',default='data/creator_profile.json');a.add_argument('--inbox',default='data/inbox.json')
    a.add_argument('--out',default='artifacts/run');a.add_argument('--provider',choices=('rules','ollama','api'),default='rules')
    a.add_argument('--model',help='Override JEEVIT_MODEL or JEEVIT_API_MODEL for the selected provider.')
    a.add_argument('--ollama-url',default=os.getenv('JEEVIT_OLLAMA_URL','http://127.0.0.1:11434'))
    a.add_argument('--api-base-url',default=os.getenv('JEEVIT_API_BASE_URL','https://api.groq.com/openai/v1'))
    a.add_argument('--api-attempts',type=int,default=3,help='Maximum hosted API attempts per email (1-3).')
    a.add_argument('--timeout',type=float,default=90)
    a.add_argument(
        '--debug-model-response',action='store_true',
        help='Print model response text to stderr for diagnosis (may include email quotes); API keys are redacted.',
    )
    e=sub.add_parser('evaluate',help='Compare a saved run with independent expectations.')
    e.add_argument('--expected',default='eval/expected_answers.json');e.add_argument('--actual',default='artifacts/run/analysis.json')
    e.add_argument('--out',default='artifacts/evaluation');e.add_argument('--strict',action='store_true',help='Exit 1 for any mismatch or grouping failure.')
    args=p.parse_args(argv)
    try:
        if args.command=='analyze':
            if args.timeout<=0 or args.timeout>300: raise ValueError('timeout must be between 0 and 300 seconds.')
            if args.provider=='ollama':
                provider=Ollama(
                    args.model or os.getenv('JEEVIT_MODEL'),args.ollama_url,args.timeout,
                    debug_model_response=args.debug_model_response,
                )
            elif args.provider=='api':
                if args.api_attempts<1 or args.api_attempts>3:
                    raise ValueError('--api-attempts must be between 1 and 3.')
                provider=OpenAICompatibleAPI(
                    args.model or os.getenv('JEEVIT_API_MODEL','openai/gpt-oss-20b'),
                    os.getenv('JEEVIT_API_KEY'),
                    args.api_base_url,args.timeout,
                    attempts=args.api_attempts,
                    debug_model_response=args.debug_model_response,
                )
            else:
                if args.debug_model_response: raise ValueError('--debug-model-response requires --provider ollama or api.')
                provider=None
            result=run(
                load(args.profile),load(args.inbox),provider,
                progress=lambda line: print(line,flush=True),
            );write_outputs(result,args.out);m=result['metadata']
            print(f'{m["mode"]}: {m["processed"]}/{m["emails_total"]} processed; {len(result["deals"])} groups. Outputs: {args.out}')
            return 0 if m['status']=='complete' else 1
        result=evaluate(load(args.expected),load(args.actual));out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
        (out/'evaluation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        (out/'evaluation.md').write_text(report(result),encoding='utf-8');print(report(result))
        return 1 if args.strict and (result['mismatches'] or not result['grouping']['exact_match']) else 0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print('Error: '+str(exc),file=sys.stderr);return 2
