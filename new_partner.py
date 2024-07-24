# import os
# import json
# from locust import HttpUser, task, between, runners, events
# from faker import Faker
# import logging
# import time
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import smtplib
# from email.utils import formatdate
# from email import encoders
# from email.mime.base import MIMEBase
# import pandas as pd
#
# fake = Faker()
#
# BASE_URL = os.environ.get("BASE_URL", "https://testing.api.hudle.in/api/v1")
#
# # Create a DataFrame to store the responses
# df = pd.DataFrame(columns=['Response'])
#
#
# class QuickstartUser(HttpUser):
#     host = "https://testing.api.hudle.in/"
#     wait_time = between(1, 2)
#
#     def __init__(self, environment):
#         super().__init__(environment)
#         self.client.headers.update({
#             'Content-Type': 'application/json',
#             'Accept': 'application/json',
#             'Api-Secret': 'hudle-api1798@prod',
#             'x-app-source': 'partner'
#         })
#
#     @task(1)
#     def post_data(self):
#         global df
#         data = {
#             "name": fake.name(),
#             "email": fake.email(),
#             'password': fake.password(),
#             'password_confirmation': fake.password(),
#             "phone": fake.phone_number(),
#             "address": fake.address()
#         }
#
#         response = self.client.post(f"{BASE_URL}/register/partner", json=data)
#
#         # Log the response
#         new_row = {'Response': response.json()}
#         df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
#
#         if response.status_code == 200:
#             print("Data sent successfully!", response.json())
#         else:
#             print("Error sending data:", response.json())
#
#
# # Save the DataFrame to an Excel file when the test is done
# def on_quitting(environment):
#     global df
#     df.to_excel('response.xlsx', index=False)
#
#
# events.quitting.add_listener(on_quitting)
import os
from locust import HttpUser, task, between, events
from faker import Faker
import pandas as pd
from pandas import ExcelWriter
import datetime

fake = Faker()

# Set the base URL from environment variable or default
BASE_URL = os.environ.get("BASE_URL", "https://testing.api.hudle.in/api/v1")

# Initialize a DataFrame to store the responses
df = pd.DataFrame(columns=['Name', 'Email', 'Password', 'Phone', 'Address', 'Status', 'Response'])


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
        global df
        # Generate fake data for the request
        data = {
            "name": fake.name(),
            "email": fake.email(),
            'password': fake.password(),
            "phone": fake.phone_number(),
            "address": fake.address()
        }

        # Send a POST request to the specified endpoint
        response = self.client.post(f"{BASE_URL}/register/partner", json=data)

        # Extract the response and status
        response_data = response.json()
        status = response.status_code

        # Append the data and response to the DataFrame
        new_row = {
            'Name': data['name'],
            'Email': data['email'],
            'Password': data['password'],
            'Phone': data['phone'],
            'Address': data['address'],
            'ID': response_data['data']['id'],  # Add this line
            'Created At': response_data['data']['created_at'],
            'Status': status,
            # 'Code': response_data['data']['code']
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Log the response
        if status == 200:
            print("Data sent successfully!", response_data)
        else:
            print("Error sending data:", response_data)


# Function to save the DataFrame to an Excel file with formatting
def save_to_excel(df, filename):
    with ExcelWriter(filename) as writer:
        # Write the DataFrame to Excel with the specified sheet name
        df.to_excel(writer, index=False, sheet_name='Responses')

        # Access the workbook and the worksheet to apply formatting
        workbook = writer.book
        worksheet = writer.sheets['Responses']

        # Set the format for the entire sheet
        format = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
        worksheet.set_column('A:F', 20, format)  # Set the width of columns A-F to 20

        # Save the workbook
        writer.save()


# Event hook for when the test is quitting
def on_quitting(environment):
    global df
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    # Save the DataFrame to an Excel file with a unique name
    save_to_excel(df, f'response_{timestamp}.xlsx')


events.quitting.add_listener(on_quitting)
