import smtplib, json, os, anthropic
from email.mime.text import MIMEText
from datetime import date
from time import sleep

GMAIL_USER = os.environ['GMAIL_USER']
GMAIL_PASS = os.environ['GMAIL_PASS']
client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

with open('config.json') as f:
    config = json.load(f)
with open('leads.json') as f:
    db = json.load(f)

def generate_email(lead):
    msg = client.messages.create(
        model='claude-sonnet-4-20250514',
        max_tokens=300,
        messages=[{'role': 'user', 'content': f'Write a cold outreach email from {config["agency_name"]} to {lead["business"]}, a {lead["industry"]} in {lead["city"]}. Offer: {lead["service"]}. Reason: {lead["why"]}. Under 100 words. Friendly. Start: Hi {lead["business"]} Team,'}]
    )
    return msg.content[0].text

def send_email(to, subject, body):
    m = MIMEText(body)
    m['Subject'] = subject
    m['From'] = GMAIL_USER
    m['To'] = to
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(m)

sent = 0
for lead in db['leads']:
    if lead.get('status') == 'New':
        body = generate_email(lead)
        send_email(lead['email'], f'Quick question about {lead["business"]}', body)
        lead['status'] = 'Contacted'
        lead['email_sent'] = str(date.today())
        sent += 1
        sleep(config.get('email_delay_seconds', 30))

db['last_updated'] = str(date.today())
with open('leads.json', 'w') as f:
    json.dump(db, f, indent=2)
print(f'Sent {sent} emails')
