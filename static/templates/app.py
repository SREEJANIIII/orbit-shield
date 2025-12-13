from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from dotenv import load_dotenv
import random
import smtplib
from email.mime.text import MIMEText
import os
import ssl
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "orbitshield_secret_key_change_this"

# Temporary OTP storage: email -> (otp, expiry)
otp_store = {}

# ===================== SMTP SAFE OTP =====================
def send_otp_email(to_email, otp):
    from_email = os.environ.get("EMAIL_USER")
    from_password = os.environ.get("EMAIL_PASS")

    if not from_email or not from_password:
        raise Exception("EMAIL_USER or EMAIL_PASS missing in .env")

    msg = MIMEText(
        f"""
Your OrbitShield OTP is: {otp}

This OTP is valid for 5 minutes.
""",
        "plain"
    )
    msg["Subject"] = "OrbitShield Login OTP"
    msg["From"] = from_email
    msg["To"] = to_email

    # ---- TRY TLS (587) FIRST ----
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        return
    except Exception as e:
        print("TLS SMTP failed:", e)

    # ---- FALLBACK TO SSL (465) ----
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30, context=ssl.create_default_context())
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        return
    except Exception as e:
        print("SSL SMTP failed:", e)
        raise Exception("SMTP connection failed. Check Gmail App Password.")

# ===================== ROUTES =====================

@app.route("/")
def login():
    if "user" in session:
        return redirect(url_for("orbit"))
    return render_template("login.html")

@app.route("/send_otp", methods=["POST"])
def send_otp():
    email = request.form.get("email", "").strip()

    if not email:
        flash("Email is required", "error")
        return redirect(url_for("login"))

    otp = random.randint(100000, 999999)
    otp_store[email] = (otp, time.time() + 300)  # 5 minutes expiry

    try:
        send_otp_email(email, otp)
        flash("OTP sent successfully!", "success")
        return render_template("verify.html", email=email)
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("login"))

@app.route("/verify", methods=["POST"])
def verify():
    email = request.form.get("email")
    entered_otp = request.form.get("otp")

    if email not in otp_store:
        flash("OTP expired. Try again.", "error")
        return redirect(url_for("login"))

    stored_otp, expiry = otp_store[email]

    if time.time() > expiry:
        del otp_store[email]
        flash("OTP expired. Try again.", "error")
        return redirect(url_for("login"))

    if str(stored_otp) == entered_otp:
        session["user"] = email
        del otp_store[email]

        # 🔥 REDIRECT DIRECTLY TO ORBITSHIELD DASHBOARD
        return redirect(url_for("orbit"))

    flash("Invalid OTP", "error")
    return render_template("verify.html", email=email)

# ===================== ORBITSHIELD =====================

@app.route("/orbit")
def orbit():
    if "user" not in session:
        return redirect(url_for("login"))

    # Serve static/index.html
    return send_from_directory("static", "index.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ===================== RUN =====================
if __name__ == "__main__":
    app.run(debug=True)
