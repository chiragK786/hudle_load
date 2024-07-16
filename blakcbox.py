import os
import json
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from email import encoders
from email.mime.base import MIMEBase
import logging
from faker import Faker
from locust import HttpUser, between, task, events

fake = Faker()

BASE_URL = "https://testing.api.hudle.in"
if not BASE_URL:
    logging.error("BASE_URL environment variable is not set")
    exit(1)

BASE_URL = BASE_URL.rstrip("/") + "/api/v1"

HOST = "https://testing.api.hudle.in/"
API_SECRET = "hudle-api1798@prod"
APP_SOURCE = "partner"
REGISTER_ENDPOINT = "/register/partner"
# aaa
EMAIL_SUBJECT = "Locust Test Report"
EMAIL_BODY = ("Please find the test report attached.\n\nTest execution summary:\nTotal users: {}\nSpawn rate: {}\nRun "
              "time: {}")

# Set environment variables
os.environ["SMTP_SERVER"] = "smtp.ethereal.email"
os.environ["SMTP_PORT"] = "587"
os.environ["SMTP_USERNAME"] = "carmen.welch32@ethereal.email"
os.environ["SMTP_PASSWORD"] = "uaxqpyPwvpYsEuxHpC"
os.environ["SENDER_EMAIL"] = "carmen.welch32@ethereal.email"
os.environ["RECIPIENT_EMAIL"] = "carmen.welch32@ethereal.email"

SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")


class QuickstartUser(HttpUser):
    host = HOST
    wait_time = between(1, 2)

    def __init__(self, environment):
        super().__init__(environment)
        self.client.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Api-Secret': API_SECRET,
            'x-app-source': APP_SOURCE
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

        response = self.client.post(f"{BASE_URL}{REGISTER_ENDPOINT}", json=data)

        if response.status_code == 200:
            logging.info("Data sent successfully!")
        else:
            logging.error("Error sending data: %s - %s", response.status_code, response.text)


def send_email(subject, body, attachments):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)

    msg.attach(MIMEText(body, 'plain'))

    for attachment in attachments:
        if not os.path.exists(attachment):
            logging.error("Attachment %s does not exist", attachment)
            return
        if not os.access(attachment, os.R_OK):
            logging.error("Attachment %s is not readable", attachment)
            return

        with open(attachment, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={attachment}")
            msg.attach(part)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        logging.info("Email sent successfully!")
    except smtplib.SMTPAuthenticationError as e:
        logging.error("Error sending email: %s", e)
    except smtplib.SMTPServerDisconnected as e:
        logging.error("Error sending email: %s", e)
    except Exception as e:
        logging.error("Error sending email: %s", e)


@events.test_stop.add_listener
def _(environment, **kw):
    num_users = environment.runner.user_count
    html_report = """
        <html>
          <head>
            <title>Locust Report</title>
          </head>
          <body>
            <h1>Locust Report</h1>
            <p>Test execution completed at {}</p>
            <p>Total users: {}</p>
            <p>Spawn rate: {}</p>
            <p>Run time: {}</p>
            <p>Successful requests: {}</p>
            <p>Failed requests:{}</p>
            <p>Average response time: {}</p>
          </body>
        </html>
        """.format(
        time.strftime("%Y-%m-%d %H:%M:%S"),
        num_users,
        environment.parsed_options.spawn_rate,
        environment.parsed_options.run_time,
        # Add more information to the report here
    )

    with open("locust_report.html", "w") as f:
        f.write(html_report)

    attachments = ["locust.log", "locust_report.html"]
    for attachment in attachments:
        if not os.path.exists(attachment):
            logging.error("Attachment %s does not exist", attachment)
            return

    subject = EMAIL_SUBJECT
    body = EMAIL_BODY.format(
        num_users,
        environment.parsed_options.spawn_rate,
        environment.parsed_options.run_time
    )

    send_email(subject, body, attachments)


if __name__ == "__main__":
    import logging

    # Set up logging
    logging.basicConfig(filename='locust.log', level=logging.INFO)

    # Run Locust for 10 seconds
    from locust.main import main

    main()
