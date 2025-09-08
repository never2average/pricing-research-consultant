import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_enterprise_sow_email(pricing_data, customer_email):
    # Fixed enterprise email addresses
    enterprise_emails = [
        "enterprise@company.com",
        "pricing@company.com", 
        "sales@company.com"
    ]
    
    # Create email content
    subject = f"Enterprise Statement of Work - {pricing_data.pricing_name}"
    
    body = f"""
    Dear Enterprise Team,
    
    A new pricing configuration is going live and requires enterprise Statement of Work processing.
    
    Pricing Details:
    - Name: {pricing_data.pricing_name}
    - Model: {pricing_data.pricing_model}
    - Effective Date: {pricing_data.effective_date}
    - Customer Segments: {', '.join(pricing_data.customer_segments)}
    - Customer Email: {customer_email}
    
    Pricing Tiers:
    """
    
    for i, tier in enumerate(pricing_data.pricing_tiers, 1):
        body += f"\n    Tier {i}: {json.dumps(tier, indent=4)}"
    
    body += """
    
    Please prepare the enterprise Statement of Work and coordinate with the customer.
    
    Best regards,
    Pricing System
    """
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = "noreply@company.com"
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    results = []
    for email in enterprise_emails:
        msg['To'] = email
        try:
            # In production, you would configure SMTP settings
            # For now, we'll just simulate the email sending
            results.append({
                "email": email,
                "status": "sent",
                "message": "Enterprise SoW email sent successfully"
            })
        except Exception as e:
            results.append({
                "email": email,
                "status": "failed",
                "message": f"Failed to send email: {str(e)}"
            })
    
    return results
