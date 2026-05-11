import google.generativeai as genai
import json
import os
import re
from datetime import date

# 100% FREE - Google Gemini API (aistudio.google.com)
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')

with open('config.json') as f:
    config = json.load(f)

with open('leads.json') as f:
    db = json.load(f)

count = config.get('leads_per_run', 5)

for city in config['target_cities']:
    for industry in config['target_industries']:
        prompt = (
            f"Generate {count} realistic {industry} business leads in {city}. "
            "Return ONLY a JSON array, no extra text, no markdown. "
            "Each object must have: business, city, industry, service, email, why, priority. "
            f"city='{city}', industry='{industry}', service='Web Design'. "
            "Use realistic local email addresses. "
            "Example: "
            '[{"business":"Blue Ocean Cafe","city":"London","industry":"restaurants",'
            '"service":"Web Design","email":"info@blueocean.co.uk",'
            '"why":"No website found online","priority":"High"}]'
        )
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            # Remove markdown if present
            text = re.sub(r'```json|```', '', text).strip()
            m = re.search(r'\[.*?\]', text, re.DOTALL)
            if m:
                new_leads = json.loads(m.group())
                for lead in new_leads:
                    lead['id'] = len(db['leads']) + 1
                    lead['status'] = 'New'
                    lead['type'] = 'AI Generated'
                    lead['date_added'] = str(date.today())
                    db['leads'].append(lead)
                print(f"WizoLabs: Added {len(new_leads)} leads - {industry} in {city}")
            else:
                print(f"No JSON found for {industry}/{city}")
        except Exception as e:
            print(f"Error for {industry}/{city}: {e}")

db['last_updated'] = str(date.today())
db['total_count'] = len(db['leads'])

with open('leads.json', 'w') as f:
    json.dump(db, f, indent=2)

print(f"Done! WizoLabs database: {len(db['leads'])} international leads.")
