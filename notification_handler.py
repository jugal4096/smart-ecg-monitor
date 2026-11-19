import os
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests

class NotificationHandler:
    def __init__(self):
        self.notification_config = {
            'email_enabled': True,
            'sms_enabled': False,
            'recipient_email': '',
            'recipient_phone': ''
        }
        self.last_alert_time = {}
        self.alert_cooldown = 300
        
    def set_config(self, config):
        self.notification_config.update(config)
    
    def get_clinical_suggestions(self, alert_type, bpm):
        suggestions = {
            'bradycardia': {
                'title': 'Bradycardia Detected',
                'description': f'Heart rate is below normal range at {bpm} BPM (normal: 60-100 BPM)',
                'severity': 'MEDIUM',
                'recommendations': [
                    'Monitor patient closely for symptoms of fatigue, dizziness, or shortness of breath',
                    'Check if patient is on beta-blockers or other heart rate-lowering medications',
                    'Consider ECG evaluation to rule out heart block or sinus node dysfunction',
                    'If symptomatic, patient may need pacemaker evaluation',
                    'Ensure adequate hydration and electrolyte balance'
                ],
                'immediate_actions': [
                    'Check patient responsiveness and vital signs',
                    'Review current medications',
                    'Contact physician if patient is symptomatic'
                ]
            },
            'tachycardia': {
                'title': 'Tachycardia Detected',
                'description': f'Heart rate is above normal range at {bpm} BPM (normal: 60-100 BPM)',
                'severity': 'MEDIUM',
                'recommendations': [
                    'Assess for signs of distress, chest pain, or palpitations',
                    'Check for fever, dehydration, or anxiety as potential causes',
                    'Review medications and caffeine intake',
                    'Consider 12-lead ECG to evaluate rhythm abnormalities',
                    'Monitor for atrial fibrillation or other arrhythmias'
                ],
                'immediate_actions': [
                    'Calm the patient and encourage slow, deep breathing',
                    'Check blood pressure and oxygen saturation',
                    'Contact physician if sustained or patient is symptomatic'
                ]
            },
            'sudden_change': {
                'title': 'Sudden Heart Rate Change',
                'description': f'Significant heart rate fluctuation detected (current: {bpm} BPM)',
                'severity': 'HIGH',
                'recommendations': [
                    'Immediately assess patient condition and consciousness level',
                    'Check for chest pain, shortness of breath, or other acute symptoms',
                    'Review recent activities, medications, or changes in condition',
                    'Perform full vital signs assessment',
                    'Consider cardiac enzyme testing if chest pain present'
                ],
                'immediate_actions': [
                    'Stay with patient and provide reassurance',
                    'Contact physician immediately',
                    'Prepare for possible emergency intervention',
                    'Document exact time and circumstances of change'
                ]
            }
        }
        
        return suggestions.get(alert_type, {})
    
    def format_email_message(self, alert_type, bpm, timestamp):
        clinical_info = self.get_clinical_suggestions(alert_type, bpm)
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }}
                .severity-high {{ background-color: #ff4444; color: white; padding: 5px 10px; border-radius: 4px; }}
                .severity-medium {{ background-color: #ff9800; color: white; padding: 5px 10px; border-radius: 4px; }}
                .section {{ margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 8px; }}
                .recommendations li {{ margin: 10px 0; }}
                .footer {{ margin-top: 30px; padding: 15px; background: #e0e0e0; border-radius: 8px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🫀 ECG Alert: {clinical_info.get('title', 'Clinical Alert')}</h1>
                <p><strong>Timestamp:</strong> {timestamp}</p>
                <p><strong>Severity:</strong> <span class="severity-{clinical_info.get('severity', 'medium').lower()}">{clinical_info.get('severity', 'MEDIUM')}</span></p>
            </div>
            
            <div class="section">
                <h2>Alert Details</h2>
                <p><strong>Current Heart Rate:</strong> {bpm} BPM</p>
                <p>{clinical_info.get('description', '')}</p>
            </div>
            
            <div class="section">
                <h2>⚡ Immediate Actions Required</h2>
                <ul>
                    {''.join([f'<li>{action}</li>' for action in clinical_info.get('immediate_actions', [])])}
                </ul>
            </div>
            
            <div class="section">
                <h2>📋 Clinical Recommendations</h2>
                <ul class="recommendations">
                    {''.join([f'<li>{rec}</li>' for rec in clinical_info.get('recommendations', [])])}
                </ul>
            </div>
            
            <div class="footer">
                <p><strong>Source:</strong> Real-Time ECG Monitor - MIT-BIH Arrhythmia Database Record 100</p>
                <p><strong>Note:</strong> This is an automated alert. Please verify with direct patient assessment and contact appropriate medical personnel.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def send_email_notification(self, alert_type, bpm):
        if not self.notification_config.get('email_enabled'):
            return False
        
        recipient = self.notification_config.get('recipient_email')
        if not recipient:
            print("No recipient email configured")
            return False
        
        if self._is_on_cooldown(alert_type):
            print(f"Alert {alert_type} is on cooldown, skipping notification")
            return False
        
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            clinical_info = self.get_clinical_suggestions(alert_type, bpm)
            
            message = MIMEMultipart('alternative')
            message['Subject'] = f"ECG Alert: {clinical_info.get('title', 'Clinical Alert')} - {bpm} BPM"
            message['From'] = 'ECG Monitor <noreply@ecgmonitor.replit.app>'
            message['To'] = recipient
            
            html_content = self.format_email_message(alert_type, bpm, timestamp)
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)
            
            self._send_via_gmail_api(message, recipient)
            
            self.last_alert_time[alert_type] = datetime.now().timestamp()
            print(f"Email notification sent successfully for {alert_type}")
            return True
            
        except Exception as e:
            print(f"Error sending email notification: {e}")
            return False
    
    def _send_via_gmail_api(self, message, recipient):
        hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
        repl_identity = os.environ.get('REPL_IDENTITY')
        web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')
        
        if not hostname:
            raise Exception("Gmail connection not configured - REPLIT_CONNECTORS_HOSTNAME not found")
        
        x_replit_token = None
        if repl_identity:
            x_replit_token = f'repl {repl_identity}'
        elif web_repl_renewal:
            x_replit_token = f'depl {web_repl_renewal}'
        else:
            raise Exception("X_REPLIT_TOKEN not found for repl/depl")
        
        headers = {
            'Accept': 'application/json',
            'X_REPLIT_TOKEN': x_replit_token
        }
        
        url = f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=google-mail'
        response = requests.get(url, headers=headers)
        connection_data = response.json()
        
        items = connection_data.get('items', [])
        if not items:
            raise Exception("Gmail not connected")
        
        access_token = items[0].get('settings', {}).get('access_token')
        if not access_token:
            oauth_creds = items[0].get('settings', {}).get('oauth', {}).get('credentials', {})
            access_token = oauth_creds.get('access_token')
        
        if not access_token:
            raise Exception("Gmail access token not found")
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        gmail_api_url = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send'
        gmail_headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        gmail_response = requests.post(
            gmail_api_url,
            headers=gmail_headers,
            json={'raw': raw_message}
        )
        
        if gmail_response.status_code not in [200, 201]:
            raise Exception(f"Gmail API error: {gmail_response.text}")
    
    def send_sms_notification(self, alert_type, bpm):
        if not self.notification_config.get('sms_enabled'):
            return False
        
        phone = self.notification_config.get('recipient_phone')
        if not phone:
            print("No recipient phone configured")
            return False
        
        if self._is_on_cooldown(alert_type):
            return False
        
        clinical_info = self.get_clinical_suggestions(alert_type, bpm)
        message = f"ECG ALERT: {clinical_info.get('title')} - {bpm} BPM. {clinical_info.get('description')} Check patient immediately."
        
        print(f"SMS notification ready: {message[:50]}...")
        print("Note: SMS sending requires Twilio integration setup")
        return False
    
    def _is_on_cooldown(self, alert_type):
        if alert_type not in self.last_alert_time:
            return False
        
        time_since_last = datetime.now().timestamp() - self.last_alert_time[alert_type]
        return time_since_last < self.alert_cooldown
    
    def send_alert(self, alert_type, bpm):
        email_sent = self.send_email_notification(alert_type, bpm)
        sms_sent = self.send_sms_notification(alert_type, bpm)
        
        return {
            'email_sent': email_sent,
            'sms_sent': sms_sent,
            'clinical_info': self.get_clinical_suggestions(alert_type, bpm)
        }
