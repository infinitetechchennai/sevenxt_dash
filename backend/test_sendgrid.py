import sys
sys.path.insert(0, '.')

from app.modules.auth.sendgrid_utils import send_email

print("=" * 60)
print("TESTING SENDGRID EMAIL FUNCTIONALITY")
print("=" * 60)

# Test sending a simple email
to_email = "loguloges77@gmail.com"
subject = "🧪 Test Email from SevenXT"
html_content = """
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #4F46E5;">Test Email</h2>
    <p>This is a test email to verify SendGrid is working correctly.</p>
    <p>If you receive this, the email system is configured properly! ✅</p>
</body>
</html>
"""

print(f"\nSending test email to: {to_email}")
print(f"Subject: {subject}")
print("\n" + "=" * 60)

try:
    result = send_email(to_email, subject, html_content)
    
    if result:
        print("\n✅ SUCCESS! Email sent successfully!")
        print(f"📧 Check your inbox: {to_email}")
    else:
        print("\n❌ FAILED! Email was not sent.")
        print("Check the error messages above for details.")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nPossible issues:")
    print("1. SendGrid API key is invalid")
    print("2. Sender email not verified in SendGrid")
    print("3. Network/firewall blocking SendGrid")

print("\n" + "=" * 60)
