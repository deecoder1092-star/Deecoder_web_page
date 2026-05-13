"""
Dee Coder Portfolio - Flask Backend
Permanent PIN system + Request management + Auto-reply emails
"""

import os
import csv
import io
import json
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from functools import wraps
from threading import Thread

from flask import (
    Flask, render_template, request, jsonify, session,
    send_file, redirect, url_for
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'deecoder-portfolio-secret-2024')

# ─── Email Configuration ─────────────────────────────────────────────────
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'deecoder1092@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'kzlyxzfvbdqqbqcy')
EMAIL_ENABLED = bool(EMAIL_SENDER and EMAIL_PASSWORD)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587


def send_email_async(recipient, subject, html_body):
    """Send an email in a background thread."""
    def _send():
        if not EMAIL_ENABLED:
            return
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f'Dee Coder <{EMAIL_SENDER}>'
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(html_body, 'html'))

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipient, msg.as_string())
            server.quit()
        except Exception as e:
            print(f"Email error (non-fatal): {e}")

    try:
        Thread(target=_send, daemon=True).start()
    except Exception:
        pass


def send_submission_confirmation(name, email, service):
    """Send auto-reply when someone submits a contact form."""
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;
                background: #0a0a0a; border-radius: 16px; overflow: hidden;
                border: 1px solid rgba(168, 85, 247, 0.2);">
      <div style="background: linear-gradient(135deg, #7c3aed, #4f46e5);
                   padding: 32px 24px; text-align: center;">
        <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 800;">Dee Coder</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">
          Front-End Developer &amp; Website Reviewer
        </p>
      </div>
      <div style="padding: 32px 24px; color: #e5e5e5;">
        <h2 style="color: #a855f7; font-size: 22px; margin: 0 0 16px 0;">Hello {name}!</h2>
        <p style="font-size: 16px; line-height: 1.7; color: #d1d5db; margin: 0 0 16px 0;">
          Thank you for reaching out! I have received your request for
          <strong style="color: #a855f7;">{service}</strong>.
        </p>
        <p style="font-size: 16px; line-height: 1.7; color: #d1d5db; margin: 0 0 16px 0;">
          I will review your request and get back to you as soon as possible.
          You will receive another email once your request has been approved.
        </p>
        <div style="background: rgba(168, 85, 247, 0.1); border: 1px solid rgba(168, 85, 247, 0.3);
                     border-radius: 12px; padding: 16px 20px; margin: 24px 0;">
          <p style="margin: 0; font-size: 14px; color: #c4b5fd;"><strong>What happens next?</strong></p>
          <ul style="margin: 12px 0 0 0; padding-left: 20px; color: #d1d5db; font-size: 14px; line-height: 2;">
            <li>Your request is now <strong style="color: #eab308;">pending review</strong></li>
            <li>I will assess your project requirements</li>
            <li>You will be notified once your request is approved</li>
            <li>Feel free to reach out on WhatsApp for urgent inquiries</li>
          </ul>
        </div>
        <p style="font-size: 14px; color: #9ca3af; margin: 24px 0 0 0;">
          In the meantime, you can also contact me directly on
          <a href="https://wa.me/2348075346224" style="color: #22c55e; text-decoration: none; font-weight: 600;">WhatsApp</a> for a faster response.
        </p>
      </div>
      <div style="background: rgba(255,255,255,0.03); padding: 20px 24px; text-align: center;
                   border-top: 1px solid rgba(255,255,255,0.05);">
        <p style="margin: 0; font-size: 12px; color: #6b7280;">
          Dee Coder &mdash; Front-End Developer<br>
          Nigeria &bull;
          <a href="https://wa.me/2348075346224" style="color: #22c55e; text-decoration: none;">WhatsApp</a> &bull;
          <a href="https://www.tiktok.com/@dee_coder1" style="color: #a855f7; text-decoration: none;">TikTok</a> &bull;
          <a href="https://www.instagram.com/Otf_brother" style="color: #ec4899; text-decoration: none;">Instagram</a>
        </p>
      </div>
    </div>
    """
    send_email_async(email, f"We received your request, {name}! — Dee Coder", html)


def send_approval_email(name, email, service, status):
    """Send email when a request is approved or declined."""
    if status == 'accepted':
        status_color = '#22c55e'
        status_text = 'Approved!'
        message = f"Great news! Your request for <strong style='color: #a855f7;'>{service}</strong> has been <strong style='color: #22c55e;'>approved</strong>! I'm excited to work with you on this project."
        next_steps = """
          <li>I will reach out to you shortly to discuss the details</li>
          <li>We will agree on timeline and deliverables</li>
          <li>Work will begin once all details are confirmed</li>
        """
    else:
        status_color = '#ef4444'
        status_text = 'Declined'
        message = f"Thank you for your interest in <strong style='color: #a855f7;'>{service}</strong>. Unfortunately, I am unable to take on this request at this time due to my current workload."
        next_steps = """
          <li>You may submit a new request in the future</li>
          <li>Feel free to reach out on WhatsApp to discuss alternatives</li>
        """

    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;
                background: #0a0a0a; border-radius: 16px; overflow: hidden;
                border: 1px solid rgba(168, 85, 247, 0.2);">
      <div style="background: linear-gradient(135deg, #7c3aed, #4f46e5);
                   padding: 32px 24px; text-align: center;">
        <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 800;">Dee Coder</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">
          Front-End Developer &amp; Website Reviewer
        </p>
      </div>
      <div style="text-align: center; padding: 24px 24px 0 24px;">
        <span style="display: inline-block; background: {status_color}20; color: {status_color};
                     border: 2px solid {status_color}; border-radius: 50px;
                     padding: 8px 24px; font-size: 18px; font-weight: 800;">
          Request {status_text}
        </span>
      </div>
      <div style="padding: 24px 24px 32px 24px; color: #e5e5e5;">
        <h2 style="color: #a855f7; font-size: 22px; margin: 0 0 16px 0;">Hello {name},</h2>
        <p style="font-size: 16px; line-height: 1.7; color: #d1d5db; margin: 0 0 16px 0;">{message}</p>
        <div style="background: rgba(168, 85, 247, 0.1); border: 1px solid rgba(168, 85, 247, 0.3);
                     border-radius: 12px; padding: 16px 20px; margin: 24px 0;">
          <p style="margin: 0; font-size: 14px; color: #c4b5fd;"><strong>What happens next?</strong></p>
          <ul style="margin: 12px 0 0 0; padding-left: 20px; color: #d1d5db; font-size: 14px; line-height: 2;">
            {next_steps}
          </ul>
        </div>
        <p style="font-size: 14px; color: #9ca3af; margin: 24px 0 0 0;">
          If you have any questions, feel free to reach out on
          <a href="https://wa.me/2348075346224" style="color: #22c55e; text-decoration: none; font-weight: 600;">WhatsApp</a>.
        </p>
      </div>
      <div style="background: rgba(255,255,255,0.03); padding: 20px 24px; text-align: center;
                   border-top: 1px solid rgba(255,255,255,0.05);">
        <p style="margin: 0; font-size: 12px; color: #6b7280;">
          Dee Coder &mdash; Front-End Developer<br>
          Nigeria &bull;
          <a href="https://wa.me/2348075346224" style="color: #22c55e; text-decoration: none;">WhatsApp</a> &bull;
          <a href="https://www.tiktok.com/@dee_coder1" style="color: #a855f7; text-decoration: none;">TikTok</a> &bull;
          <a href="https://www.instagram.com/Otf_brother" style="color: #ec4899; text-decoration: none;">Instagram</a>
        </p>
      </div>
    </div>
    """
    send_email_async(email, f"Your request has been {status_text}, {name} — Dee Coder", html)


# ─── Data Storage ────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

PIN_FILE = os.path.join(DATA_DIR, 'pin.json')
REQUESTS_FILE = os.path.join(DATA_DIR, 'requests.json')
DEFAULT_PIN = '2024'


def load_pin():
    try:
        if os.path.exists(PIN_FILE):
            with open(PIN_FILE, 'r') as f:
                return json.load(f).get('pin', DEFAULT_PIN)
    except Exception:
        pass
    return DEFAULT_PIN


def save_pin(pin):
    try:
        with open(PIN_FILE, 'w') as f:
            json.dump({'pin': pin, 'updated': datetime.now().isoformat()}, f)
    except Exception as e:
        print(f"Error saving PIN: {e}")


def load_requests():
    try:
        if os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_requests(requests_list):
    try:
        with open(REQUESTS_FILE, 'w') as f:
            json.dump(requests_list, f, indent=2)
    except Exception as e:
        print(f"Error saving requests: {e}")


# Initialize files
if not os.path.exists(PIN_FILE):
    save_pin(DEFAULT_PIN)
if not os.path.exists(REQUESTS_FILE):
    save_requests([])


# ─── Auth ────────────────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


# ─── Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/verify-pin', methods=['POST'])
def verify_pin():
    try:
        data = request.get_json(silent=True) or {}
        if data.get('pin', '') == load_pin():
            session['admin_logged_in'] = True
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Incorrect PIN'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/change-pin', methods=['POST'])
@admin_required
def change_pin():
    try:
        data = request.get_json(silent=True) or {}
        if data.get('current_pin', '') != load_pin():
            return jsonify({'success': False, 'error': 'Current PIN is incorrect'}), 403
        if len(data.get('new_pin', '')) < 4:
            return jsonify({'success': False, 'error': 'PIN must be at least 4 digits'}), 400
        save_pin(data['new_pin'])
        return jsonify({'success': True, 'message': 'PIN updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('admin_logged_in', None)
    return jsonify({'success': True})


@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    return jsonify({'authenticated': session.get('admin_logged_in', False)})


# ─── Contact Form ───────────────────────────────────────────────────────

@app.route('/api/submit-request', methods=['POST'])
def submit_request():
    try:
        data = request.get_json(silent=True) or {}

        for field in ['name', 'email', 'service', 'message']:
            if not data.get(field, '').strip():
                return jsonify({'success': False, 'error': f'{field.title()} is required'}), 400

        new_request = {
            'id': str(uuid.uuid4()),
            'name': data.get('name', '').strip(),
            'email': data.get('email', '').strip(),
            'phone': data.get('phone', '').strip(),
            'company': data.get('company', '').strip(),
            'website': data.get('website', '').strip(),
            'service': data.get('service', '').strip(),
            'message': data.get('message', '').strip(),
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
        }

        requests_list = load_requests()
        requests_list.insert(0, new_request)
        save_requests(requests_list)

        # Try to send confirmation email (won't block on failure)
        try:
            send_submission_confirmation(new_request['name'], new_request['email'], new_request['service'])
        except Exception:
            pass

        return jsonify({
            'success': True,
            'message': 'Your request has been submitted! We will get back to you shortly.',
            'request_id': new_request['id']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500


@app.route('/api/requests', methods=['GET'])
@admin_required
def get_requests():
    requests_list = load_requests()
    status_filter = request.args.get('status', '')
    if status_filter:
        requests_list = [r for r in requests_list if r['status'] == status_filter]
    return jsonify({'requests': requests_list, 'total': len(requests_list)})


@app.route('/api/requests/<request_id>/status', methods=['PATCH'])
@admin_required
def update_request_status(request_id):
    data = request.get_json(silent=True) or {}
    new_status = data.get('status', '')

    if new_status not in ('accepted', 'declined', 'pending'):
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

    requests_list = load_requests()
    for req in requests_list:
        if req['id'] == request_id:
            req['status'] = new_status
            req['updated_at'] = datetime.now().isoformat()
            save_requests(requests_list)

            try:
                if new_status in ('accepted', 'declined'):
                    send_approval_email(req['name'], req['email'], req['service'], new_status)
            except Exception:
                pass

            return jsonify({'success': True, 'message': f'Request {new_status}'})

    return jsonify({'success': False, 'error': 'Request not found'}), 404


@app.route('/api/requests/<request_id>', methods=['DELETE'])
@admin_required
def delete_request(request_id):
    requests_list = load_requests()
    original_len = len(requests_list)
    requests_list = [r for r in requests_list if r['id'] != request_id]
    if len(requests_list) == original_len:
        return jsonify({'success': False, 'error': 'Request not found'}), 404
    save_requests(requests_list)
    return jsonify({'success': True, 'message': 'Request deleted'})


@app.route('/api/requests/export-csv', methods=['GET'])
@admin_required
def export_csv():
    requests_list = load_requests()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Company', 'Website', 'Service', 'Message', 'Status', 'Date'])
    for req in requests_list:
        writer.writerow([req['id'], req['name'], req['email'], req.get('phone', ''),
                         req.get('company', ''), req.get('website', ''), req['service'],
                         req['message'], req['status'], req['created_at']])
    output.seek(0)
    mem = io.BytesIO(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem, mimetype='text/csv', as_attachment=True,
                     download_name=f'deecoder-requests-{datetime.now().strftime("%Y%m%d")}.csv')


@app.route('/api/requests/stats', methods=['GET'])
@admin_required
def get_stats():
    requests_list = load_requests()
    return jsonify({
        'total': len(requests_list),
        'pending': len([r for r in requests_list if r['status'] == 'pending']),
        'accepted': len([r for r in requests_list if r['status'] == 'accepted']),
        'declined': len([r for r in requests_list if r['status'] == 'declined']),
    })


# ─── Run ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 50)
    print("  Dee Coder Portfolio Server")
    print("=" * 50)
    print(f"  Default PIN: {load_pin()}")
    print(f"  Email: {'ENABLED' if EMAIL_ENABLED else 'NOT CONFIGURED'}")
    print(f"  Admin: Triple-tap 'deecoder' logo")
    print(f"  URL: http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=5000)
