import os
import json
from locust import HttpUser, task, between, runners, events
from faker import Faker
import logging
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from email.utils import formatdate
from email import encoders
from email.mime.base import MIMEBase

fake = Faker()

BASE_URL = os.environ.get("BASE_URL", "https://testing.api.hudle.in/api/v1")


class QuickstartUser(HttpUser):
    host = "https://testing.api.hudle.in/"
    wait_time = between(1, 2)

    def __init__(self, environment):
        super().__init__(environment)
        self.client.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Api-Secret': 'hudle-api1798@prod',
            'x-app-source': 'partner'

        })

    @task(1)
    def post_data(self):
        data = {
            "name": fake.name(),
            "email": fake.email(),
            'password': fake.password(),
            'password_confirmation': fake.password(),
            "phone": fake.phone_number(),
            "address": fake.address()
        }

        response = self.client.post(f"{BASE_URL}/register/partner", json=data)

        if response.status_code == 200:
            print("Data sent successfully!")
        else:
            print("Error sending data:", response.text)


@events.test_stop.add_listener
def _(environment, **kw):
    num_users = environment.runner.user_count
    # Generate HTML report
    html_report = """
    <html>
      <head>
        <title>Locust Report</title>
      </head>
      <body>
        <h1>Locust Report</h1>
        <p>Test execution completed at {}</p>
      </body>
    </html>
    """.format(time.strftime("%Y-%m-%d %H:%M:%S"))

    with open("locust_report.html", "w") as f:
        f.write(html_report)

    # Send email with log file and HTML report as attachments
    sender_email = "carmen.welch32@ethereal.email"
    recipient_email = "carmen.welch32@ethereal.email"
    subject = "Locust Test Report"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)

    body = ("Please find the test report attached.\n\nTest execution summary:\nTotal users: {}\nSpawn rate: {}\nRun "
            "time: {}").format(

        num_users,
        environment.runner.spawn_rate,
        environment.runner.time_limit
    )
    msg.attach(MIMEText(body, 'plain'))

    attachment1 = open("locust.log", "rb")
    part1 = MIMEBase('application', 'octet-stream')
    part1.set_payload(attachment1.read())
    encoders.encode_base64(part1)
    part1.add_header('Content-Disposition', "attachment; filename= locust.log")
    msg.attach(part1)

    attachment2 = open("locust_report.html", "rb")
    part2 = MIMEBase('application', 'octet-stream')
    part2.set_payload(attachment2.read())
    encoders.encode_base64(part2)
    part2.add_header('Content-Disposition', "attachment; filename= locust_report.html")
    msg.attach(part2)

    try:
        server = smtplib.SMTP('smtp.ethereal.email', 587)
        server.starttls()
        server.login(sender_email, 'uaxqpyPwvpYsEuxHpC')
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except smtplib.SMTPRecipientsRefused as e:
        print("Error sending email:", e)
    except smtplib.SMTPException as e:
        print("Error sending email:", e)
    except Exception as e:
        print("Error sending email:", e)
