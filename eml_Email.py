import os
#!/usr/bin/env python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# set for gmail
smtp_server = "smtp.gmail.com"

def eml_SendEmail(fromAddr, toAddr, email_pwd, subject, body, attachFile=None):

    msg = MIMEMultipart()
    msg["From"] = fromAddr
    msg["To"] = toAddr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    if attachFile != None:
        attachment = open(attachFile, 'rb')
    
        part = MIMEBase("application", "octet-stream")
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachFile))
        msg.attach(part)
        
        server = smtplib.SMTP(smtp_server, 587)
        server.starttls()
        server.login(fromAddr, email_pwd)
        text = msg.as_string()
        
        server.sendmail(fromAddr, toAddr, text)
        server.quit()
