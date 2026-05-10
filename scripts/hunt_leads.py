import anthropic
import json
import os
import re
from datetime import date

client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

with open('config.json') as f:
    config = json.load(f)

with open('leads.json') as f:
    db = json.load(f)

for city in config['target_cities']:
    for industry in config['target_industries']:
        msg = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=1000,
            messages=[{
                'role': 'user',
                'content': f'Generate {config["leads_per_run"]} realistic leads for {industry} businesses in {city}, Pakistan. Return ONLY a JSON array: [{{"business":"Name","city":"{city}","industry":"{industry}","service":"Web Design","email":"email@example.pk","why":"one sentence reason","priority":"High"}}]. JSON only, no markdown.'
            }]
        )
        m = re.search(r'\[.*\]', msg.content[0].text, re.DOTALL)
        if m:
            new_leads = json.loads(m.group())
            for lead in new_leads:
                lead['id'] = len(db['leads']) + 1
                lead['status'] = 'New'
                lead['type'] = 'AI Generated'
                lead['date_added'] = str(date.today())
                db['leads'].append(lead)

db['last_updated'] = str(date.today())
db['total_count'] = len(db['leads'])

with open('leads.json', 'w') as f:
    json.dump(db, f, indent=2)

print(f'Done. Total leads: {len(db["leads"])}')
