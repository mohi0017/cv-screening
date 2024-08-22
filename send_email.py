import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

# Define paths to your assets
asset1 = "static/assets/your_company_logo.png"
asset2 = "static/assets/your_company_signature.jpg"

def send_interview_invitation(
    dest_email, c_name, c_designation, sendermail, hr_name, hr_pos, company_name, server
):
    today = datetime.today()

    SUBJECT = f"Interview Invitation | {company_name}"
    TEXT = f"""
    <p style="text-align: center; font-size: 20px;"><b>Dear {c_name},</b></p>

    <p style="font-size: 16px;">
    We are pleased to invite you for an interview at {company_name} for the position of {c_designation}. The interview process will consist of two stages:</p>

    <p style="font-size: 16px;">
    <ol>
        <li><b>Online Interview:</b> This will be conducted remotely via video conferencing. You will receive further details regarding the online interview schedule and platform shortly.</li>
        <li><b>In-Person Interview:</b> Upon successful completion of the online interview, you will be shortlisted for an in-person interview at our office location. Details about the in-person interview will be provided after the online interview.</li>
    </ol></p>

    <p style="font-size: 16px;">
    We believe that your skills and experience make you a strong candidate for this position, and we are looking forward to discussing your qualifications further.

    Please confirm your availability for the online interview by {today.strftime("%B %d, %Y")}. If you have any scheduling conflicts or need further information, please feel free to contact us.

    We appreciate your interest in joining our team at {company_name} and look forward to meeting you soon.<br>

    <b>Sincerely,</b><br><br>

    {hr_name}<br>
    {hr_pos}<br>
    {company_name}<br><br>

    <b>Accepted by:</b><br><br>

    {c_name}<br><br>

    <b>Date:</b> {today.strftime("%B %d, %Y")}
    </p>
    """

    message = MIMEMultipart()
    message["From"] = sendermail
    message["To"] = dest_email
    message["Subject"] = SUBJECT

    # Attach HTML content
    html_content = f"""
    <html>
        <head>
            <style>
                .outer {{
                    background-color: #f2f2f2;
                    padding: 20px;
                    border-radius: 10px;
                }}
                .inner {{
                    background-color: #ffffff;
                    padding: 20px;
                    text-align: center;
                }}
                img {{
                    display: block;
                    margin: 0 auto;
                    width: 150px;
                    height: auto;
                }}
                p {{
                    font-size: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="outer">
                <div class="inner">
                    <a href="#"><img src="cid:company_logo" alt="Company Logo"></a>
                    {TEXT}
                    <a href="#"><img src="cid:signature" alt="Signature"></a>
                </div>
            </div>
        </body>
    </html>
    """
    html_part = MIMEText(html_content, "html")
    message.attach(html_part)

    # Attach images
    with open(asset1, "rb") as f:
        logo = MIMEImage(f.read())
        logo.add_header("Content-ID", "<company_logo>")
        message.attach(logo)

    with open(asset2, "rb") as f:
        signature = MIMEImage(f.read())
        signature.add_header("Content-ID", "<signature>")
        message.attach(signature)

    return message
