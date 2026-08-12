import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Sends a 6-digit OTP verification code to the target user email.
    Uses SMTP credentials from environment variables if set, or logs to dev console.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    sender_name = os.getenv("SENDER_NAME", "Campus Store")

    # If SMTP is not configured, log OTP to server output for dev testing
    if not smtp_user or not smtp_pass:
        print("\n" + "=" * 50)
        print(f" [DEV MODE - OTP GENERATED]")
        print(f" Target Email : {to_email}")
        print(f" OTP Code     : {otp_code}")
        print(f" Valid for    : 10 minutes")
        print("=" * 50 + "\n")
        return True

    # Construct HTML email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{otp_code} is your Campus Store verification code"
    msg["From"] = f"{sender_name} <{smtp_user}>"
    msg["To"] = to_email

    html_content = f"""
    <div style="font-family: Arial, sans-serif; background-color: #f9fafb; padding: 24px;">
        <div style="max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 32px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 24px;">
                <span style="font-size: 24px; font-weight: 900; color: #15803d; letter-spacing: -0.5px;">CAMPUS<span style="color: #eab308;">STORE</span></span>
            </div>
            <h2 style="color: #1f2937; font-size: 20px; font-weight: 700; margin-top: 0; text-align: center;">Reset Your Password</h2>
            <p style="color: #4b5563; font-size: 14px; line-height: 1.5; text-align: center;">Use the verification code below to complete your password reset request:</p>
            <div style="background-color: #f3f4f6; border-radius: 8px; padding: 16px; text-align: center; margin: 24px 0;">
                <span style="font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #15803d;">{otp_code}</span>
            </div>
            <p style="color: #6b7280; font-size: 13px; text-align: center; margin-bottom: 0;">This code is valid for <strong>10 minutes</strong>. If you did not request a password reset, please ignore this email.</p>
        </div>
    </div>
    """
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"OTP email successfully delivered to {to_email}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send OTP email via SMTP: {e}")
        return True
