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

count = config.get('leads_per_run', 5)

for city in config['target_cities']:
    for industry in config['target_industries']:
        prompt = (
            f"Generate {count} realistic business leads for {industry} in {city}, Pakistan. "
            "Return ONLY a valid JSON array. Each item must have exactly these keys: "
            "business, city, industry, service, email, why, priority. "
            f"City must be '{city}', industry must be '{industry}', service must be 'Web Design'. "
            "Use realistic Pakistani business email addresses. "
            "Example format: "
            '[{"business":"Example Cafe","city":"Lahore","industry":"restaurants",'
            '"service":"Web Design","email":"info@example.pk",'
            '"why":"No website found","priority":"High"}]'
        )
        msg = client.messages.create(
            model='claude-sonnet-4-5',
            max_tokens=1500,
            messages=[{'role': 'user', 'content': prompt}]
        )
        text = msg.content[0].text
        m = re.search(r'\[.*?\]', text, re.DOTALL)
        if m:
            try:
                new_leads = json.loads(m.group())
                for lead in new_leads:
                    lead['id'] = len(db['leads']) + 1
                    lead['status'] = 'New'
                    lead['type'] = 'AI Generated'
                    lead['date_added'] = str(date.today())
                    db['leads'].append(lead)
                print(f"Added {len(new_leads)} leads for {industry} in {city}")
            except json.JSONDecodeError as e:
                print(f"JSON error for {industry}/{city}: {e}")

db['last_updated'] = str(date.today())
db['total_count'] = len(db['leads'])

with open('leads.json', 'w') as f:
    json.dump(db, f, indent=2)

print(f"Done. Total leads in database: {len(db['leads'])}")
