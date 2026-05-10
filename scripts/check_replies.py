import imaplib, email, json, os, re
from datetime import datetime, date
import anthropic

GMAIL_USER = os.environ['GMAIL_USER']
GMAIL_PASS = os.environ['GMAIL_PASS']
client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

def check_gmail():
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(GMAIL_USER, GMAIL_PASS)
    mail.select('INBOX')
    _, ids = mail.search(None, 'UNSEEN')
    messages = []
    for mid in ids[0].split():
        _, data = mail.fetch(mid, '(RFC822)')
        msg = email.message_from_bytes(data[0][1])
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        messages.append({'id': mid.decode(), 'from': msg.get('From',''), 'subject': msg.get('Subject',''), 'body': body[:500].strip(), 'read': False})
    mail.logout()
    return messages

def analyze_reply(body):
    msg = client.messages.create(model='claude-sonnet-4-20250514', max_tokens=100,
        messages=[{'role':'user','content':f'Analyze this reply. Return ONLY JSON: {{"sentiment":"interested|needs_followup|not_interested","summary":"one sentence"}}. Email: {body[:300]}'}])
    try:
        return json.loads(re.sub(r'```json|```','',msg.content[0].text).strip())
    except:
        return {'sentiment':'needs_followup','summary':'Review manually.'}

with open('leads.json') as f:
    db = json.load(f)
try:
    with open('inbox.json') as f:
        inbox = json.load(f)
except:
    inbox = {'replies':[],'last_checked':None}

seen = {r['id'] for r in inbox['replies']}
new_msgs = check_gmail()
added = 0
for msg in new_msgs:
    if msg['id'] in seen:
        continue
    analysis = analyze_reply(msg['body'])
    msg.update({'sentiment':analysis.get('sentiment','needs_followup'),'ai_summary':analysis.get('summary',''),'date_added':str(date.today())})
    sender = re.search(r'[w.+-]+@[w.-]+', msg['from'])
    sender_email = sender.group(0).lower() if sender else ''
    for lead in db['leads']:
        if lead.get('email','').lower() == sender_email:
            msg['lead_id'] = lead['id']
            msg['business'] = lead['business']
            if lead['status'] in ('New','Contacted'):
                lead['status'] = 'Replied'
    inbox['replies'].append(msg)
    added += 1

inbox['last_checked'] = datetime.now().isoformat()
with open('inbox.json','w') as f:
    json.dump(inbox, f, indent=2)
with open('leads.json','w') as f:
    json.dump(db, f, indent=2)
print(f'Done. {added} new replies. Total: {len(inbox["replies"])}')
