#!/usr/bin/env python3
"""Fetch the form definitions (questions) used by the old Webhero forms."""
import json, os, re, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools', 'source')
ids = set()
for f in os.listdir(SRC):
    ids.update(re.findall(r'event_id:\s*(\d+)', open(os.path.join(SRC, f), encoding='utf-8').read()))
out = {}
for i in sorted(ids):
    body = json.dumps({'event_id': int(i), 'domain': 'niya-solutions.be', 'language_id': '1'})
    r = subprocess.run(['curl', '-s', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', body,
                        'https://api.webhero.be/api/event/questions'], capture_output=True, text=True)
    out[i] = {'questions': json.loads(r.stdout)['questions']}
    print(i, [q['question'] for q in out[i]['questions']])
json.dump(out, open(os.path.join(ROOT, 'tools', 'forms.json'), 'w'), indent=1, ensure_ascii=False)
