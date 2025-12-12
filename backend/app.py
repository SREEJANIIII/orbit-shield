from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import random
import smtplib
from email.mime.text import MIMEText
import os
import ssl

load_dotenv()  # Load .env variables

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this'

# In-memory OTP storage
otps = {}

def send_otp_email(to_email, otp):
    from_email = os.environ.get('EMAIL_USER')
    from_password = os.environ.get('EMAIL_PASS')
    
    if not from_email or not from_password:
        raise ValueError("Set EMAIL_USER and EMAIL_PASS in .env file!")
    
    subject = "Your Login OTP"
    body = f"Your 6-digit OTP is: <strong>{otp}</strong><br><br>It expires in 5 minutes."
    
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    
    ports = [(587, False), (465, True)]  # Try 587 (STARTTLS) first, then 465 (SSL)
    
    for attempt in range(2):  # Retry once
        for port, use_ssl in ports:
            try:
                context = ssl.create_default_context()
              # Your previous Python 3.13 fix
                
                if use_ssl:
                    server = smtplib.SMTP_SSL('smtp.gmail.com', port, context=context, timeout=30, local_hostname="localhost")
                else:
                    server = smtplib.SMTP('smtp.gmail.com', port, timeout=30, local_hostname="localhost")
                    server.starttls(context=context)

                    
                
                server.set_debuglevel(1)  # Verbose logging—check terminal for details
                server.local_hostname = "localhost"

                server.ehlo()  # Identify ourselves
                
                server.login(from_email, from_password)
                server.sendmail(from_email, to_email, msg.as_string())
                server.quit()
                print(f"OTP sent successfully to {to_email} via port {port}")
                return
            
            except Exception as e:
                print(f"Attempt {attempt+1}, Port {port} error: {e}")
                if '10053' in str(e) or '10060' in str(e):
                    print("Network block detected—check firewall/antivirus.")
                continue  # Try next port/retry
    
    raise Exception("All attempts failed. See terminal logs for details.")

# Home - Login Page
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# Send OTP to user's entered email
@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.form.get('email').strip()
    
    if not email:
        flash("Please enter an email address.", "error")
        return redirect(url_for('index'))
    
    # Generate OTP
    otp = random.randint(100000, 999999)
    otps[email] = otp
    
    try:
        send_otp_email(email, otp)
        flash("OTP sent successfully to your email! Check inbox/spam.", "success")
        return render_template('verify.html', email=email)
    except Exception as e:
        flash(f"Failed to send OTP: {str(e)}", "error")
        return redirect(url_for('index'))

# Verify OTP
@app.route('/verify', methods=['POST'])
def verify():
    email = request.form.get('email')
    user_otp = request.form.get('otp')
    
    if not user_otp:
        flash("Please enter the OTP.", "error")
        return render_template('verify.html', email=email)
    
    try:
        user_otp = int(user_otp)
    except ValueError:
        flash("OTP must be 6 digits.", "error")
        return render_template('verify.html', email=email)
    
    stored_otp = otps.get(email)
    
    if stored_otp == user_otp:
        session['user'] = email
        if email in otps:
            del otps[email]
        flash("Login Successful! 🎉", "success")
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid OTP. Try again.", "error")
        return render_template('verify.html', email=email)

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Please log in first.", "error")
        return redirect(url_for('index'))
    return render_template('dashboard.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
