import os
import datetime
import logging
import random

from locust import HttpUser, SequentialTaskSet, task, between, events
from faker import Faker
import pandas as pd

import requests

fake = Faker('en_IN')

BASE_URL = os.environ.get("BASE_URL", "https://testing.api.hudle.in/api/v1")
TEAM_URL = os.environ.get('TEAM_URL', 'https://testing.group-and-games.prod.hudle.in/api/v1')

df_register = pd.DataFrame(
    columns=['Name', 'Email', 'Password', 'Phone', 'Address', 'Status', 'Response'])
df_otp = pd.DataFrame(
    columns=['Phone', 'Type', 'Status', 'Response'])  # Added 'OTP' DataFrame
df_cities = pd.DataFrame(
    columns=['City', 'Latitude', 'Longitude', 'Status,Response']
)
df_nearest_city = pd.DataFrame(columns=['City', 'Latitude', 'Longitude', 'Status', 'Response'])
df_venues = pd.DataFrame(columns=['Venue ID', 'Status', 'Response'])
df_venue_details = pd.DataFrame(
    columns=['Venue ID', 'Facility ID', 'Activity ID', 'Slots ID', 'Credit Plans', 'Status', 'Response'])
df_get_slots = pd.DataFrame(columns=['Status', 'Response'])
df_get_delete = pd.DataFrame(
    columns=['Status', 'Response', 'Token'])
df_get_delete_warning = pd.DataFrame(
    columns=['Status', 'Response', 'Warning'])
df_delete_account = pd.DataFrame(
    columns=['Status', 'Response'])
# df_cart_summary = pd.DataFrame(columns=['Status', 'Response'])
# df_post_booking_consumer = pd.DataFrame(columns=['Status', 'Response'])

timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

logger = logging.getLogger('locust')
logger.setLevel(logging.INFO)


class UserBehavior(SequentialTaskSet):
    def __init__(self, parent):
        super().__init__(parent)
        self.token = None
        self.delete_token = None
        self.reason = None

        # Set the headers
        self.headers = {
            'Api-Secret': 'hudle-api1798@prod',
            'x-app-id': str(fake.random_number(digits=10, fix_len=True))
            # Use Faker to generate a random 10-digit number
        }

    @task
    def register_and_request_otp(self):
        phone_number, response_data, email, name, date_of_birth = self.register_consumer()
        if response_data is not None:
            self.request_otp(phone_number)  # Pass the phone number to request_otp
            self.verify_otp(phone_number, "48353")  # Verify OTP
            latitude, longitude = self.fetch_cities()
            if latitude and longitude:
                self.fetch_nearest_city(latitude, longitude)
            venue_id = self.fetch_venues()
            facility_id, activity_id = self.fetch_venue_details_with_retry(
                venue_id)  # Fetch venue details with retry logic
            slot_id, price = self.get_slots(venue_id, facility_id)
            self.get_deletion_token()
            self.get_deletion_warning()
            self.delete_account()
            # self.post_booking_consumer(price, slot_id, activity_id, venue_id, name, email, date_of_birth, phone_number)
            # self.get_summary(venue_id, activity_id, facility_id, slot_id)  # Fetch slots

    def register_consumer(self):
        global df_register  # Make sure df_register is accessible
        data = {
            "email": f"{fake.random_number(digits=10, fix_len=True)}@testing.com",  # Modified this line
            "name": fake.name(),
            "password": fake.password(),
            "password_confirmation": fake.password(),
            "address": fake.address(),
            "phone_number": int(str(fake.random_int(min=1, max=5)) + str(fake.random_number(digits=9, fix_len=True))),
            "date_of_birth": fake.date_of_birth().isoformat(),
            "gender": 1,
            "email_updates": 1,
            "//x-x": 1,
            "//sports[]": 5,
            "//fcm_id": "e4645646456"
        }

        logger.info(f"Calling Register API: {BASE_URL}/register/consumer")  # Log the API endpoint
        response = self.client.post(f"{BASE_URL}/register/consumer", json=data, headers=self.headers)

        if response.status_code != 200:
            logger.error("Error registering consumer: %s", response.content)
            return None, None

        response_data = response.json()
        logger.info("Consumer registered successfully! %s", response_data)

        # Add the response data to df_register
        new_row = {
            'Name': data['name'],
            'Email': data['email'],
            'Password': data['password'],
            'Phone': data['phone_number'],
            'Address': data['address'],
            'Status': response.status_code,
            'Response': response_data
        }
        df_register = pd.concat([df_register, pd.DataFrame([new_row])], ignore_index=True)

        return data['phone_number'], data['name'], data[
            'date_of_birth'], data['email'], response_data  # Return the phone number and the response data

    def request_otp(self, phone_number):  # Add phone_number as a parameter
        # Make sure df_otp is accessible
        data = {
            "phone_number": phone_number,  # Use the phone number from the Register API
            "type": 2
        }

        logger.info(f"Calling OTP API: {BASE_URL}/otp/new")  # Log the API endpoint
        response = self.client.post(f"{BASE_URL}/otp/new", json=data, headers=self.headers)

        if response.status_code != 204:
            logger.error("Error requesting OTP: %s", response.content)
            return None

        response_data = response.json() if response.content else "No content in response"
        logger.info(f"OTP requested successfully! Response: {response_data}")

        return response_data

    def verify_otp(self, phone_number, otp_code):
        global df_otp
        data = {
            "code": otp_code,
            "phone_number": phone_number,
            "type": 2
        }

        logger.info(f"Calling OTP Verify API: {BASE_URL}/otp/verify")  # Log the API endpoint
        response = self.client.post(f"{BASE_URL}/otp/verify", json=data, headers=self.headers)

        if response.status_code != 200:
            logger.error("Error verifying OTP: %s", response.content)
            return None

        response_data = response.json() if response.content else "No content in response"
        logger.info(f"OTP verified successfully! Response: {response_data}")

        # Capture the token from the response
        if isinstance(response_data, dict) and 'data' in response_data and 'token' in response_data['data']:
            token = response_data['data']['token']
            logger.info(f"Token: {token}")
            self.headers['Authorization'] = f'Bearer {token}'
        else:
            token = None

        # Add the response data to df_otp
        new_row = {
            'Phone': data['phone_number'],
            'Type': data['type'],
            'Status': response.status_code,
            'Response': response_data,
            'Token': token
        }
        df_otp = pd.concat([df_otp, pd.DataFrame([new_row])], ignore_index=True)

        return response_data

    @task
    def fetch_cities(self):
        global df_cities  # Make sure df_cities is accessible

        logger.info(f"Calling Cities API: {BASE_URL}/cities")  # Log the API endpoint
        response = self.client.get(f"{BASE_URL}/cities", headers=self.headers)

        if response.status_code != 200:
            logger.error("Error fetching cities: %s", response.content)
            return None

        response_data = response.json()
        logger.info("Cities fetched successfully! %s", response_data)

        # Add the response data to df_cities
        for city in response_data['data']:
            new_row = {
                'City': city['name'],
                'Latitude': city['latitude'],
                'Longitude': city['longitude'],
                'Status': response.status_code,
                'Response': response_data
            }
            if df_cities.empty:
                df_cities = pd.DataFrame([new_row])
            else:
                df_cities = pd.concat([df_cities, pd.DataFrame([new_row])], ignore_index=True)

        # Select a random city from the response data
        random_city = random.choice(response_data['data'])
        random_city_latitude = random_city['latitude']
        random_city_longitude = random_city['longitude']

        logger.info(
            f"Random city: {random_city['name']}, Latitude: {random_city_latitude}, Longitude: {random_city_longitude}")

        return random_city_latitude, random_city_longitude

    def fetch_nearest_city(self, latitude, longitude):
        global df_nearest_city  # Make sure df_nearest_city is accessible

        data = {
            "latitude": latitude,
            "longitude": longitude
        }

        logger.info(f"Calling Nearest City API: {BASE_URL}/cities/nearest")  # Log the API endpoint
        response = self.client.post(f"{BASE_URL}/cities/nearest", data=data, headers=self.headers)

        if response.status_code != 200:
            logger.error("Error fetching nearest city: %s", response.content)
            return None

        response_data = response.json()
        logger.info("Nearest city fetched successfully! %s", response_data)

        # Add the response data to df_nearest_city
        new_row = {
            'City': response_data['data']['name'],
            'Latitude': response_data['data']['latitude'],
            'Longitude': response_data['data']['longitude'],
            'Status': response.status_code,
            'Response': response_data
        }
        df_nearest_city = pd.concat([df_nearest_city, pd.DataFrame([new_row])], ignore_index=True)

        return response_data

    def fetch_venues(self):
        global df_venues  # Make sure df_venues is accessible
        logger.info(f"Calling Venues API: {TEAM_URL}/venues/elastic?per_page=1000")  # Log the API endpoint
        response = self.client.get(f"{TEAM_URL}/venues/elastic?per_page=1000", headers=self.headers)
        if response.status_code != 200:
            logger.error("Error fetching venues: %s", response.content)
            return None

        response_data = response.json()
        logger.info("Venues fetched successfully! %s", response_data)

        # Add the response data to df_venues
        venue_ids = [venue['id'] for venue in response_data['data']]
        for venue in response_data['data']:
            new_row = {
                'Venue ID': venue['id'],
                'Status': response.status_code,
                'Response': response_data
            }
            df_venues = pd.concat([df_venues, pd.DataFrame([new_row])], ignore_index=True)

        # Select a random venue ID from the response data
        random_venue = random.choice(response_data['data'])
        random_venue_id = random_venue['id']

        logger.info(f"Random venue ID: {random_venue_id}")

        return random_venue_id

    def fetch_venue_details_with_retry(self, venue_id):  # venue_id is now a parameter
        global df_venue_details  # Make sure df_venue_details is accessible

        url = f"{BASE_URL}/venues/{venue_id}?include=activities.facilities,credit_plans"

        logger.info(f"Calling Venue Details API: {url}")  # Log the API endpoint
        response = requests.get(url, headers=self.headers)

        if response.status_code == 404:
            logger.error(f"Venue details not found (404). Retrying fetch_venues and fetch_venue_details.")
            venue_id = self.fetch_venues()
            return self.fetch_venue_details_with_retry(venue_id)

        if response.status_code != 200:
            logger.error(f"Error fetching venue details: {response.content}")
            return None

        response_data = response.json()
        logger.info(f"Venue details fetched successfully! {response_data}")

        # Capture the facility ID, activity ID, and slots ID if present
        facility_id = response_data['data']['activities'][0]['facilities'][0]['id'] if 'activities' in response_data[
            'data'] and response_data['data']['activities'] else None
        activity_id = response_data['data']['activities'][0]['id'] if 'activities' in response_data['data'] and \
                                                                      response_data['data']['activities'] else None

        # Add the response data to df_venue_details
        new_row = {
            'Venue ID': venue_id,
            'Facility ID': facility_id,
            'Activity ID': activity_id,
            'Credit Plans': response_data['data']['credit_plans'],
            'Status': response.status_code,
            'Response': response_data
        }
        df_venue_details = pd.concat([df_venue_details, pd.DataFrame([new_row])], ignore_index=True)
        print('this fac', facility_id)

        return facility_id, activity_id

    def get_slots(self, venue_id, facility_id):
        global df_get_slots  # Assuming you have defined this DataFrame

        today_date = datetime.date.today()
        start_date = today_date + datetime.timedelta(days=1)
        end_date = start_date + datetime.timedelta(days=2)

        params = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'grid': '1',
            'facility': facility_id
        }

        logger.info(f"Making GET request to /venues/{venue_id}/slots")  # Logging statement

        response = self.client.get(f"{BASE_URL}/venues/{venue_id}/slots", params=params, headers=self.headers)
        response_data = response.json()
        status = response.status_code
        logger.info(response_data)

        new_row = {
            'Status': status,
            'Response': response_data
        }
        df_get_slots = pd.concat([df_get_slots, pd.DataFrame([new_row])], ignore_index=True)

        if status == 404:
            logger.error("Error 404: Slots not found. Retrying fetch_venues and fetch_venue_details.")
            venue_id = self.fetch_venues()
            facility_id, _ = self.fetch_venue_details_with_retry(venue_id)
            return self.get_slots(venue_id, facility_id)

        # Extract the slot ID from the response
        slots = response_data['data']['slot_data'][0]['slots']
        random_index = random.randint(0, len(slots) - 1)
        slot_id = slots[random_index]['id']
        price = slots[random_index]['price']

        print(slot_id)
        print('the price', price)
        logger.info(slot_id)
        return slot_id, price

    # def post_booking_consumer(self, price, activity_id, slot_id, Venue_id, name, email, date_of_birth, phone_number):
    #     global df_post_booking_consumer  # Make sure df_register is accessible
    #     data = {
    #         "activity_id": activity_id,
    #
    #         "user_details[name]": name,
    #         "user_details[email]": "",
    #         "user_details[phone_number]": phone_number,
    #         "user_details[date_of_birth]": "",
    #         "sms_channel": 1,
    #         "amount_paid": price,
    #         "payable_now": price,
    #         "update_email": False,
    #         "includes": "payments,participants,order",
    #         "invoice_type": 1,
    #         "slots": {
    #             slot_id: 1
    #         }
    #     }
    #     print(date_of_birth, "this is dob")
    #
    #     logger.info(f"Calling Register API: {BASE_URL}/register/consumer")  # Log the API endpoint
    #     response = self.client.post(f"{BASE_URL}/venues/{Venue_id}/bookings/new", data=data, headers=self.headers)
    #
    #     if response.status_code != 200:
    #         logger.error("Error Booking Creation: %s", response.content)
    #         return None, None
    #
    #     response_data = response.json()
    #     logger.info("Booking Created successfully! %s", response_data)
    #
    #     # Add the response data to df_register
    #     new_row = {
    #
    #         'Status': response.status_code,
    #         'Response': response_data
    #     }
    #     df_post_booking_consumer = pd.concat([df_post_booking_consumer, pd.DataFrame([new_row])], ignore_index=True)
    #     print(response_data)
    #
    #     return response_data  # Return the phone number and the response data

    # def get_summary(self, venue_id, facility_id, activity_id, slot_id):
    #     global df_cart_summary
    #     logger.info('Calling the Get Summary API')
    #
    #     json = {
    #         "venue_id": venue_id,
    #         "facility_id": facility_id,
    #         "activity_id": activity_id,
    #         "slots": {
    #             slot_id: 1
    #         }
    #     }
    #     response = self.client.post(f"{BASE_URL}/cart/get-summary", json=json, headers=self.headers)
    #     response_data = response.json
    #     status = response.status_code
    #     logger.info('Summary fetch Successfully', response_data)
    #
    #     print(response_data)
    #     new_row = {
    #         'Status': status,
    #         'Response': response_data
    #     }
    #     df_cart_summary = pd.concat([df_cart_summary, pd.DataFrame([new_row])], ignore_index=True)
    #     price = response_data['data']['price'] if 'data' in response_data and 'price' in response_data['data'] else None
    #
    #     if price is not None:
    #         logger.info(f"Price fetched from response: {price}")
    #
    #     return price
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


def save_to_excel(df_register, df_otp, df_cities, df_nearest_city, df_venues, df_venue_details, df_get_slots,
                  df_get_delete, df_get_delete_warning, df_delete_account, filename):
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df_register.to_excel(writer, index=False, sheet_name='Register Responses')
        df_otp.to_excel(writer, index=False, sheet_name='OTP Responses')
        df_cities.to_excel(writer, index=False, sheet_name='Cities Responses')  # Save df_cities to Excel
        df_nearest_city.to_excel(writer, index=False,
                                 sheet_name='Nearest City Responses')  # Save df_nearest_city to Excel
        df_venues.to_excel(writer, index=False, sheet_name='Venues Responses')
        df_venue_details.to_excel(writer, index=False, sheet_name='Venue Details Responses')
        df_get_slots.to_excel(writer, index=False, sheet_name='Get Slots Responses')
        df_get_delete.to_excel(writer, index=False, sheet_name='Get Delete Token Responses')
        df_get_delete_warning.to_excel(writer, index=False,
                                       sheet_name='Get Deletion Warning Responses')
        df_delete_account.to_excel(writer, index=False, sheet_name='Delete Account Responses')
        # df_cart_summary.to_excel(writer, index=False, sheet_name='Get Cart Responses')

        workbook = writer.book
        worksheet1 = writer.sheets['Register Responses']
        worksheet2 = writer.sheets['OTP Responses']
        worksheet3 = writer.sheets['Cities Responses']  # Added worksheet for Cities
        worksheet4 = writer.sheets['Nearest City Responses']  # Added worksheet for Nearest City
        worksheet5 = writer.sheets['Venues Responses']
        worksheet6 = writer.sheets['Venue Details Responses']  # Added worksheet for Venue Details
        worksheet7 = writer.sheets['Get Slots Responses']
        worksheet8 = writer.sheets['Get Delete Token Responses']
        worksheet9 = writer.sheets['Get Deletion Warning Responses']
        worksheet10 = writer.sheets['Delete Account Responses']
        # worksheet8 = writer.sheets['Get Cart Responses']

        format = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
        worksheet1.set_column('A:G', 20, format)
        worksheet2.set_column('A:E', 20, format)
        worksheet3.set_column('A:E', 20, format)  # Set column width for Cities worksheet
        worksheet4.set_column('A:E', 20, format)  # Set column width for Nearest City worksheet
        worksheet5.set_column('A:E', 20, format)  # Set column width for Venues worksheet
        worksheet6.set_column('A:G', 20, format)  # Set column width for Venue Details worksheet
        worksheet7.set_column('A:E', 20, format)  # Set column width for Get Slots worksheet
        worksheet8.set_column('A:D', 20, format)  # Adjusted for the new 'Token' column
        worksheet9.set_column('A:D', 20, format)
        worksheet10.set_column('A:C', 20, format)


def on_quitting(environment):
    global df_register, df_otp, df_cities, df_nearest_city, df_venues, df_venue_details, df_get_slots
    save_to_excel(df_register, df_otp, df_cities, df_nearest_city, df_venues, df_venue_details, df_get_slots,
                  df_get_delete, df_get_delete_warning,
                  df_delete_account, f'responses_{timestamp}.xlsx')


events.quitting.add_listener(on_quitting)
