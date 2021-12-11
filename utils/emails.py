import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from static.api_keys import emailpassword
from random import randrange

class EmailClass:
    def __init__(self):
        self.auth = ""

    def regenAuth(self):
        self.auth = randrange(100000, 999999)

    def createVerifMsg(self, email):
        msg = EmailMessage()
        msg.set_content(f'Your authentication code is {self.auth}')
        msg['Subject'] = 'Authentication Code'
        msg['From'] = "ScheduleCreation@gmail.com"
        msg['To'] = email
        print(f"Successfuly sent {self.auth}\n")
        return msg

    def confirmPassChange(self, email):
        msg = MIMEMultipart("alternative")
        msg['Subject'] = 'URStudent Password Change'
        msg['From'] = "ScheduleCreation@gmail.com"
        msg['To'] = email
        link = f"http://127.0.0.1:5000/passreset/Reset={email}"
        
        text = f"""Hello
        The password for your URStudent account was just changed.
        If this was you, you can safely ignore this email.
        
        If this was not you, your account as been compromised.
        Click on this link to reset your password: {link}
        """
        html = f"""\
        <html>
            <body>
                <h3> Hello </h3>
                <p> The password for your URStudent account was just changed.<br>
                    If this was you, you can safely ignore this email.<br><br>
                    
                    If this was not you, your account as been compromised.<br>
                    <a href={link}> Click here to reset your password</a>. 
                </p>
            </body>
        </html>
        """
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        return msg

    def resetPassword(self, email):
        msg = MIMEMultipart("alternative")
        msg['Subject'] = 'Reset Password for URStudent'
        msg['From'] = "ScheduleCreation@gmail.com"
        msg['To'] = email
        link = f"http://127.0.0.1:5000/passreset/Reset={email}"
        
        text = f"""Hello
        Someone has just requested the password for URStudent to be reset.
        If this was you, click on this link: {link}
        
        If it wasn't you, your account has been compromised and you should probably reset your password anyway.
        """
        html = f"""\
        <html>
            <body>
                <h3> Hello </h3>
                <p> Someone has just requested the password for URStudent to be reset.<br>
                    If this was you, click <a href={link}>here</a>.<br><br> 
                    If it wasn't you, your account has been compromised and you should probably reset your password anyway.
                </p>
            </body>
        </html>
        """
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        return msg

    def sendEmail(self, msg):
        # Send the message via our own SMTP server.
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login("ScheduleCreation", emailpassword)
        server.send_message(msg)
        server.quit()





class TextClass:
    def __init__(self):
        self.auth = ""

    def regenAuth(self):
        self.auth = randrange(100000, 999999)
    
    def carriers(self):
        self.Carriers = {
            'AT&T': '@mms.att.net',
            'T-Mobile' : '@tmomail.net',
            'Verizon' : '@vzwpix.com',
            'Sprint' : '@pm.sprint.com',
            'XFinity Mobile' : '@mypixmessages.com',
            'Virgin Mobile' : '@vmpix.com',
            'Tracfone' : '@mmst5.tracfone.com',
            'Metro PCS' : '@mymetropcs.com',
            'Boost Mobile' : '@myboostmobile.com',
            'Cricket' : '@mms.cricketwireless.net',
            'Google Fi (Project Fi)' : '@msg.fi.google.com',
            'U.S. Cellular' : '@mms.uscc.net',
            'Ting' : '@message.ting.com'
            }

    def sendText(self, number):
        # Send the message via our own SMTP server.
        message = (f'Your authentication code is {self.auth}')
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login("ScheduleCreation", emailpassword)
        for i in self.Carriers.values():
            num = '{0}{1}'.format(number, i)
            server.sendmail(
            "ScheduleCreation@gmail.com", 
            num, 
            message)

        server.quit()
        print(f"Successfuly sent {self.auth}\n")
