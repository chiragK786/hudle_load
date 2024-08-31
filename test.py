import os
import datetime
import logging
from locust import HttpUser, SequentialTaskSet, task, between, events
from faker import Faker
import pandas as pd
from pandas import ExcelWriter

unique_fake = Faker().unique

BASE_URL = os.environ.get("BASE_URL", "https://testing.api.hudle.in/api/v1")

df_register = pd.DataFrame(
    columns=['Name', 'Email', 'Password', 'Phone', 'Address', 'ID', 'Created At', 'Status', 'Response', 'Code'])
df_login = pd.DataFrame(
    columns=['Email', 'Password', 'Status', 'Response', 'Code'])
df_get = pd.DataFrame(
    columns=['Status', 'Response', 'Token'])
df_get_delete = pd.DataFrame(
    columns=['Status', 'Response', 'Token'])
df_get_delete_warning = pd.DataFrame(
    columns=['Status', 'Response', 'Warning'])
df_delete_account = pd.DataFrame(
    columns=['Status', 'Response'])

timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

logger = logging.getLogger('locust')
logger.setLevel(logging.INFO)

# Set up a file handler for the logger
file_handler = logging.FileHandler('api_logs.log')
logger.addHandler(file_handler)


class UserBehavior(SequentialTaskSet):
    def __init__(self, parent):
        super().__init__(parent)
        self.email = None
        self.password = None
        self.token = None
        self.delete_token = None
        self.reason = None  # Define 'reason' attribute here

        # Set the headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Api-Secret': 'hudle-api1798@prod',
            'x-app-source': 'partner'
        }

    @task
    def register_login_get_config_and_get_deletion_token(self):
        self.email, self.password = self.post_data()
        self.token = self.login()
        if self.token is not None:
            self.headers['Authorization'] = f'Bearer {self.token}'  # Add the auth token to the headers
            self.get_config()
            self.get_deletion_token()
            self.get_deletion_warning()
            self.delete_account()

    def post_data(self):
        global df_register
        data = {
            "name": unique_fake.name(),
            "email": unique_fake.email(),
            'password': unique_fake.password(),
            "phone": unique_fake.phone_number(),
            "address": unique_fake.address()
        }

        try:
            response = self.client.post(f"{BASE_URL}/register/partner", json=data)
            response.raise_for_status()
        except Exception as e:
            logger.error("Error sending data: %s. Response: %s", e, response.content)
            return None, None

        response_data = response.json()
        status = response.status_code

        code = """
        data = {
            "name": "%s",
            "email": "%s",
            'password': "%s",
            "phone": "%s",
            "address": "%s"
        }
        response = self.client.post("%s/register/partner", json=data)
        """ % (data['name'], data['email'], data['password'], data['phone'], data['address'], BASE_URL)

        new_row = {
            'Name': data['name'],
            'Email': data['email'],
            'Password': data['password'],
            'Phone': data['phone'],
            'Address': data['address'],
            'ID': response_data['data']['id'],
            'Created At': response_data['data']['created_at'],
            'Status': status,
            'Response': response_data,
            'Code': code
        }
        df_register = pd.concat([df_register, pd.DataFrame([new_row])], ignore_index=True)

        logger.info("Data sent successfully! %s", response_data)

        return data['email'], data['password']

    def login(self):
        global df_login
        data = {
            'email': self.email,
            # 'password': "hsqhud23"
            'password': self.password
        }

        logger.info("Making POST request to /login")  # Logging statement

        try:
            response = self.client.post(f"{BASE_URL}/login", json=data)
            response.raise_for_status()
        except Exception as e:
            logger.error("Error logging in: %s. Response: %s", e, response.content)
            return None

        response_data = response.json()
        status = response.status_code
        token = response_data['data']['token']
        logger.info(response_data)

        new_row = {
            'Email': self.email,
            'Password': self.password,
            'Status': status,
            'Response': response_data,
            'Token': token
        }
        df_login = pd.concat([df_login, pd.DataFrame([new_row])], ignore_index=True)

        return token

    def get_config(self):
        global df_get
        try:
            response = self.client.get(f"{BASE_URL}/config/partner?device=android")
            response.raise_for_status()
        except Exception as e:
            logger.error("Error retrieving config: %s. Response: %s", e, response.content)
            return

        response_data = response.json()
        status = response.status_code

        new_row = {
            'Status': status,
            'Response': response_data
        }
        df_get = pd.concat([df_get, pd.DataFrame([new_row])], ignore_index=True)

        logger.info("Config retrieved successfully! %s", response.json())

    def get_deletion_token(self):
        global df_get_delete
        try:
            response = self.client.get(f"{BASE_URL}/get-deletion-token", headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            logger.error("Error retrieving deletion token: %s. Response: %s", e, response.content)
            return

        response_data = response.json()
        status = response.status_code
        self.reason = response_data['data']['reason'][0]
        self.delete_token = response_data['data']['token']

        new_row = {
            'Status': status,
            'Response': response_data,
            'Token': self.delete_token,
            'Reason': self.reason
        }
        df_get_delete = pd.concat([df_get_delete, pd.DataFrame([new_row])], ignore_index=True)
        print(self.delete_token)

        logger.info("Deletion token retrieved successfully! %s", response.json())

        # Extract the token from the response

    def get_deletion_warning(self):
        global df_get_delete_warning
        try:
            response = self.client.get(f"{BASE_URL}/get-deletion-warning", headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            logger.error("Error retrieving deletion warning: %s. Response: %s", e, response.content)
            return

        response_data = response.json()
        status = response.status_code

        # Extract the warning from the response
        warning = response_data['data']

        new_row = {
            'Status': status,
            'Response': response_data,
            'Warning': warning  # Add the warning to the DataFrame
        }
        print(warning)
        df_get_delete_warning = pd.concat([df_get_delete_warning, pd.DataFrame([new_row])], ignore_index=True)

        logger.info("Deletion warning retrieved successfully! %s", response.json())

    @task
    def delete_account(self):
        global df_delete_account

        # Define the payload
        payload = {
            "reason": self.reason,
            "deletion_token": self.delete_token
        }

        try:
            # Make the POST request
            response = self.client.post(f"{BASE_URL}/delete-account", headers=self.headers, json=payload)
            response.raise_for_status()
        except Exception as e:
            logger.error("Error deleting account: %s. Response: %s", e, response.content)
            return

        response_data = response.json()
        status = response.status_code

        # Log the response
        new_row = {
            'Status': status,
            'Response': response_data
        }
        df_delete_account = pd.concat([df_delete_account, pd.DataFrame([new_row])], ignore_index=True)

        logger.info("Account deleted successfully! %s", response.json())
        print(response_data)


class QuickstartUser(HttpUser):
    host = "https://testing.api.hudle.in/"
    wait_time = between(1, 2)
    tasks = [UserBehavior]

    def __init__(self, environment):
        super().__init__(environment)
        self.client.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Api-Secret': 'hudle-api1798@prod',
            'x-app-source': 'partner'
        })


def save_to_excel(df_register, df_login, df_get, df_get_delete, df_get_delete_warning, df_delete_account, filename):
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df_register.to_excel(writer, index=False, sheet_name='Register Responses')
        df_login.to_excel(writer, index=False, sheet_name='Login Responses')
        df_get.to_excel(writer, index=False, sheet_name='Get Config Responses')
        df_get_delete.to_excel(writer, index=False, sheet_name='Get Delete Token Responses')
        df_get_delete_warning.to_excel(writer, index=False,
                                       sheet_name='Get Deletion Warning Responses')
        df_delete_account.to_excel(writer, index=False, sheet_name='Delete Account Responses')

        workbook = writer.book
        worksheet1 = writer.sheets['Register Responses']
        worksheet2 = writer.sheets['Login Responses']
        worksheet3 = writer.sheets['Get Config Responses']
        worksheet4 = writer.sheets['Get Delete Token Responses']
        worksheet5 = writer.sheets['Get Deletion Warning Responses']
        worksheet6 = writer.sheets['Delete Account Responses']

        format = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
        worksheet1.set_column('A:J', 20, format)
        worksheet2.set_column('A:E', 20, format)
        worksheet3.set_column('A:C', 20, format)
        worksheet4.set_column('A:D', 20, format)  # Adjusted for the new 'Token' column
        worksheet5.set_column('A:D', 20, format)
        worksheet6.set_column('A:C', 20, format)  # Added this line


def on_quitting(environment):
    global df_register, df_login, df_get
    save_to_excel(df_register, df_login, df_get, df_get_delete, df_get_delete_warning,
                  df_delete_account, f'responses_{timestamp}.xlsx')  # Added df_get_delete_warning


events.quitting.add_listener(on_quitting)
