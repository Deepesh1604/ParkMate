#!/bin/bash

echo "🔐 Logging in as admin..."
curl -s -X POST "http://localhost:5000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -c cookies.txt > /dev/null

echo "📧 Triggering monthly report for user 'dd' (ID: 249)..."
RESPONSE=$(curl -s -X POST "http://localhost:5000/api/admin/trigger-monthly-reports" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"user_id": 249}')

echo "Response: $RESPONSE"

echo "⏳ Waiting 5 seconds for email processing..."
sleep 5

echo "📬 Checking MailHog for email to dd@gmail.com..."
curl -s "http://localhost:8025/api/v1/messages" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    dd_emails = [msg for msg in data if any('dd@gmail.com' in to['Mailbox'] + '@' + to['Domain'] for to in msg['To'])]
    if dd_emails:
        latest = dd_emails[0]
        print('✅ SUCCESS: Monthly report email found for dd@gmail.com!')
        print(f'📧 Subject: {latest[\"Content\"][\"Headers\"][\"Subject\"][0]}')
        print(f'👤 From: {latest[\"Content\"][\"Headers\"][\"From\"][0]}')
        print(f'🕐 Sent: {latest[\"Created\"]}')
        print()
        print('🌐 View in MailHog: http://localhost:8025')
    else:
        print('❌ No monthly report email found for dd@gmail.com')
        print(f'📊 Total emails in MailHog: {len(data)}')
except Exception as e:
    print(f'Error checking emails: {e}')
"

# Cleanup
rm -f cookies.txt

echo "Done! Check MailHog web interface at http://localhost:8025"
