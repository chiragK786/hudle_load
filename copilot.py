# import os
# import datetime
# import logging
# from locust import HttpUser, task, between, events
# from faker import Faker
# import pandas as pd
# from pandas import ExcelWriter
#
# fake = Faker()
#
# # Set the base URL from environment variable or default
# BASE_URL = os.environ.get("BASE_URL", "https://testing.api.hudle.in/api/v1")
#
# # Initialize a DataFrame to store the responses
# df = pd.DataFrame(
#     columns=['Name', 'Email', 'Password', 'Phone', 'Address', 'ID', 'Created At', 'Status', 'Response', 'Code'])
#
# # Generate a timestamp
# timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#
# # Create a logger
# logger = logging.getLogger('locust')
# logger.setLevel(logging.INFO)
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
#         # Generate fake data for the request
#         data = {
#             "name": fake.name(),
#             "email": fake.email(),
#             'password': fake.password(),
#             "phone": fake.phone_number(),
#             "address": fake.address()
#         }
#
#         # Send a POST request to the specified endpoint
#         response = self.client.post(f"{BASE_URL}/register/partner", json=data)
#
#         # Extract the response and status
#         response_data = response.json()
#         status = response.status_code
#
#         # Store the code as a string
#         code = """
#         data = {
#             "name": "%s",
#             "email": "%s",
#             'password': "%s",
#             "phone": "%s",
#             "address": "%s"
#         }
#         response = self.client.post("%s/register/partner", json=data)
#         """ % (data['name'], data['email'], data['password'], data['phone'], data['address'], BASE_URL)
#
#         # Append the data, response, and code to the DataFrame
#         new_row = {
#             'Name': data['name'],
#             'Email': data['email'],
#             'Password': data['password'],
#             'Phone': data['phone'],
#             'Address': data['address'],
#             'ID': response_data['data']['id'],
#             'Created At': response_data['data']['created_at'],
#             'Status': status,
#             'Response': response_data,
#             'Code': code
#         }
#         df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
#
#         # Log the response
#         if status == 200:
#             logger.info("Data sent successfully! %s", response_data)
#         else:
#             logger.error("Error sending data: %s", response_data)
#
#
# # Function to save the DataFrame to an Excel file with formatting
# def save_to_excel(df, filename):
#     with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
#         # Write the DataFrame to Excel with the specified sheet name
#         df.to_excel(writer, index=False, sheet_name='Responses')
#
#         # Access the workbook and the worksheet to apply formatting
#         workbook = writer.book
#         worksheet = writer.sheets['Responses']
#
#         # Set the format for the entire sheet
#         format = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
#         worksheet.set_column('A:J', 20, format)  # Set the width of columns A-J to 20
#
#
# # Event hook for when the test is quitting
# def on_quitting(environment):
#     global df
#     # Save the DataFrame to an Excel file with a unique name
#     save_to_excel(df, f'response_{timestamp}.xlsx')
#
#
# events.quitting.add_listener(on_quitting)
#
# def login(self, email, password):
#     # Prepare the form data
#     data = {
#         "email": email,
#         'password': password,
#     }
#
#     # Send a POST request to the login API with the form data and headers
#     response = self.client.post(f"{BASE_URL}/login", data=data)
#
#     # Log the response
#     if response.status_code == 200:
#         logger.info("Login successful! %s", response.json())
#     else:
#         logger.error("Error logging in: %s", response.json())


# import os
# import datetime
# import logging
# from locust import HttpUser, task, between, events, SequentialTaskSet
# from faker import Faker
# import pandas as pd
# from pandas import ExcelWriter
#
# fake = Faker()
#
# # Set the base URL from environment variable or default
# BASE_URL = os.environ.get("BASE_URL", "https://testing.api.hudle.in/api/v1")
#
# # Initialize a DataFrame to store the responses
# df = pd.DataFrame(
#     columns=['Name', 'Email', 'Password', 'Phone', 'Address', 'ID', 'Created At', 'Status', 'Response', 'Code'])
#
# # Generate a timestamp
# timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#
# # Create a logger
# logger = logging.getLogger('locust')
# logger.setLevel(logging.INFO)
#
#
# class UserBehavior(SequentialTaskSet):
#     def __init__(self, parent):
#         super().__init__(parent)
#         self.email = None
#         self.password = None
#
#     @task
#     def post_data(self):
#         global df
#         # Generate fake data for the request
#         data = {
#             "name": fake.name(),
#             "email": fake.email(),
#             'password': fake.password(),
#             "phone": fake.phone_number(),
#             "address": fake.address()
#         }
#
#         # Send a POST request to the specified endpoint
#         response = self.client.post(f"{BASE_URL}/register/partner", json=data)
#
#         # Extract the response and status
#         response_data = response.json()
#         status = response.status_code
#
#         # Store the code as a string
#         code = """
#         data = {
#             "name": "%s",
#             "email": "%s",
#             'password': "%s",
#             "phone": "%s",
#             "address": "%s"
#         }
#         response = self.client.post("%s/register/partner", json=data)
#         """ % (data['name'], data['email'], data['password'], data['phone'], data['address'], BASE_URL)
#
#         # Append the data, response, and code to the DataFrame
#         new_row = {
#             'Name': data['name'],
#             'Email': data['email'],
#             'Password': data['password'],
#             'Phone': data['phone'],
#             'Address': data['address'],
#             'ID': response_data['data']['id'],
#             'Created At': response_data['data']['created_at'],
#             'Status': status,
#             'Response': response_data,
#             'Code': code
#         }
#         df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
#
#         # Log the response
#         if status == 200:
#             logger.info("Data sent successfully! %s", response_data)
#         else:
#             logger.error("Error sending data: %s", response_data)
#
#         # Store the email and password for the login task
#         self.email = data['email']
#         self.password = data['password']
#
#
# @task
# def login(self):
#     # Prepare the form data
#     data = {
#         "email": self.email,
#         'password': self.password,
#     }
#
#     # Send a POST request to the login API with the form data and headers
#     response = self.client.post(f"{BASE_URL}/login", data=data)
#
#     # Log the response
#     if response.status_code == 200:
#         logger.info("Login successful! %s", response.json())
#     else:
#         logger.error("Error logging in: %s", response.json())
#
#
# class QuickstartUser(HttpUser):
#     host = "https://testing.api.hudle.in/"
#     wait_time = between(1, 2)
#     tasks = [UserBehavior]
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
#
# # Function to save the DataFrame to an Excel file with formatting
# def save_to_excel(df, filename):
#     with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
#         # Write the DataFrame to Excel with the specified sheet name
#         df.to_excel(writer, index=False, sheet_name='Responses')
#
#         # Access the workbook and the worksheet to apply formatting
#         workbook = writer.book
#         worksheet = writer.sheets['Responses']
#
#         # Set the format for the entire sheet
#         format = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
#         worksheet.set_column('A:J', 20, format)  # Set the width of columns A-J to 20
#
#
# # Event hook for when the test is quitting
# def on_quitting(environment):
#     global df
#     # Save the DataFrame to an Excel file with a unique name
#     save_to_excel(df, f'response_{timestamp}.xlsx')
#
#
# events.quitting.add_listener(on_quitting)

import os
import datetime
import logging
from locust import HttpUser, task, between, events, SequentialTaskSet
from faker import Faker
import pandas as pd
from pandas import ExcelWriter

fake = Faker()

# Set the base URL from environment variable or default
BASE_URL = os.environ.get("BASE_URL", "https://testing.api.hudle.in/api/v1")

# Initialize a DataFrame to store the responses
df = pd.DataFrame(
    columns=['Name', 'Email', 'Password', 'Phone', 'Address', 'ID', 'Created At', 'Status', 'Response', 'Code'])

# Generate a timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

# Create a logger
logger = logging.getLogger('locust')
logger.setLevel(logging.INFO)


class UserBehavior(SequentialTaskSet):
    def __init__(self, parent):
        super().__init__(parent)
        self.email = None
        self.password = None

    @task
    def register_and_login(self):
        # Call the post_data task and get the email and password
        self.email, self.password = self.post_data()

        # Call the login task with the email and password
        self.login()

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

        # Store the code as a string
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

        # Append the data, response, and code to the DataFrame
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
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Log the response
        if status == 200:
            logger.info("Data sent successfully! %s", response_data)
        else:
            logger.error("Error sending data: %s", response_data)

        # Return the email and password for the login task
        return data['email'], data['password']

    def login(self):
        # Prepare the form data
        data = {
            'email': self.email,
            'password': self.password,
        }

        # Send a POST request to the login API with the form data and headers
        response = self.client.post(f"{BASE_URL}/login", data=data)

        # Log the response
        if response.status_code == 200:
            logger.info("Login successful! %s", response.json())
        else:
            logger.error("Error logging in: %s", response.json())


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


# Function to save the DataFrame to an Excel file with formatting
def save_to_excel(df, filename):
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        # Write the DataFrame to Excel with the specified sheet name
        df.to_excel(writer, index=False, sheet_name='Responses')

        # Access the workbook and the worksheet to apply formatting
        workbook = writer.book
        worksheet = writer.sheets['Responses']

        # Set the format for the entire sheet
        format = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
        worksheet.set_column('A:J', 20, format)  # Set the width of columns A-J to 20


# Event hook for when the test is quitting
def on_quitting(environment):
    global df
    # Save the DataFrame to an Excel file with a unique name
    save_to_excel(df, f'response_{timestamp}.xlsx')


events.quitting.add_listener(on_quitting)
