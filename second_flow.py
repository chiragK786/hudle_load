import os
import datetime
import logging
import random

from locust import HttpUser, SequentialTaskSet, task, between, events
from faker import Faker
import pandas as pd

fake = Faker().unique

BASE_URL = os.environ.get("BASE_URL", "https://testing.api.hudle.in/api/v1")

df_login = pd.DataFrame(columns=['Response', 'Code', 'Token'])
df_get = pd.DataFrame(columns=['Status', 'Response'])
df_post = pd.DataFrame(columns=['Status', 'Response'])
df_get_venue = pd.DataFrame(columns=['Status', 'Venue Names'])
df_get_id = pd.DataFrame(columns=['Status', 'Response', 'Facility IDs'])  # Added 'Facility IDs'
df_get_facility = pd.DataFrame(columns=['Status', 'Response'])  # DataFrame for get_facility_by_id
df_get_slots = pd.DataFrame(columns=['Status', 'Response'])  # DataFrame for get_slots
df_get_slots_meta = pd.DataFrame(columns=['Status', 'Response'])  # DataFrame for get_slots_meta
df_post_booking = pd.DataFrame(columns=['Status', 'Response'])  # DataFrame for post_booking

timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

logger = logging.getLogger('locust')
logger.setLevel(logging.INFO)


class UserBehavior(SequentialTaskSet):
    def __init__(self, parent):
        super().__init__(parent)
        self.email = None
        self.password = None
        self.token = None

        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Api-Secret': 'hudle-api1798@prod',
            'x-app-source': 'partner'
        }

    @task
    def register_login_get_config_and_get_deletion_token(self):
        global facility_id
        self.token = self.login()
        if self.token is not None:
            self.headers['Authorization'] = f'Bearer {self.token}'
            self.get_config()
            # self.post_venue()
            venue_ids = self.get_user_venues()
            if venue_ids:  # Check if the list is not empty
                venue_id = venue_ids[4]  # Get the first venue ID
                facility_ids = self.get_venue_by_id(venue_id)
                for facility_id in facility_ids:
                    self.get_facility_by_id(venue_id, facility_id)
                slot_id = self.get_slots(venue_id, facility_id)  # Call the new method
                # self.get_slots_meta(venue_id, facility_id)  # Call the new method
                self.post_booking(venue_id, facility_id, slot_id)
                self.get_event()
                # Call the new method

    def login(self):
        global df_login
        data = {
            'email': "dhruv@hudle.in",
            # 'password': "hsqhud23"
            'password': "password"

        }

        logger.info("Making POST request to /login")  # Logging statement

        response = self.client.post(f"{BASE_URL}/login", json=data)
        if response.status_code != 200:
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

        logger.info("Making GET request to /config/partner?device=android")  # Logging statement

        response = self.client.get(f"{BASE_URL}/config/partner?device=android")
        response_data = response.json()
        status = response.status_code

        new_row = {
            'Status': status,
            'Response': response_data
        }
        df_get = pd.concat([df_get, pd.DataFrame([new_row])], ignore_index=True)

    def get_user_venues(self):
        global df_get_venue

        logger.info("Making GET request to /user/venues")  # Logging statement

        response = self.client.get(f"{BASE_URL}/user/venues", headers=self.headers)

        response_data = response.json()
        status = response.status_code
        logger.info(response_data)
        venue_names = [item['name'] for item in response_data['data']]
        venue_ids = [item['id'] for item in response_data['data']]

        new_row = {
            'Status': status,
            'Venue Names': venue_names
        }
        df_get_venue = pd.concat([df_get_venue, pd.DataFrame([new_row])], ignore_index=True)

        return venue_ids

    def get_venue_by_id(self, venue_id):
        global df_get_id

        logger.info(f"Making GET request to /venues/{venue_id}")  # Logging statement

        response = self.client.get(f"{BASE_URL}/venues/{venue_id}/facilities/", headers=self.headers)
        response_data = response.json()
        status = response.status_code
        logger.info(response_data)

        facility_ids = [facility['id'] for facility in response_data['data']]
        fac_name = [facility['name'] for facility in response_data['data']]

        new_row = {
            'Status': status,
            'Response': response_data,
            'Facility IDs': facility_ids,
            'facility_name': fac_name  # Capture the facility IDs
        }
        df_get_id = pd.concat([df_get_id, pd.DataFrame([new_row])], ignore_index=True)

        return facility_ids

    def get_facility_by_id(self, venue_id, facility_id):
        global df_get_facility

        logger.info(f"Making GET request to /venues/{venue_id}/facilities/{facility_id}")  # Logging statement

        response = self.client.get(f"{BASE_URL}/venues/{venue_id}/facilities/{facility_id}", headers=self.headers)
        response_data = response.json()
        status = response.status_code

        new_row = {
            'Status': status,
            'Response': response_data,
            # 'name': response_data['data']['name']
        }
        df_get_facility = pd.concat([df_get_facility, pd.DataFrame([new_row])], ignore_index=True)
        logger.info(response_data)

    def get_slots(self, venue_id, facility_id):
        global df_get_slots  # Assuming you have defined this DataFrame

        today_date = datetime.date.today()
        start_date = today_date + datetime.timedelta(days=1)
        end_date = start_date + datetime.timedelta(days=2)

        params = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'grid': '1'
        }

        logger.info(f"Making GET request to /venues/{venue_id}/facilities/{facility_id}/slots")  # Logging statement

        response = self.client.get(f"{BASE_URL}/venues/{venue_id}/facilities/{facility_id}/slots", params=params,
                                   headers=self.headers)
        response_data = response.json()
        status = response.status_code
        logger.info(response_data)

        new_row = {
            'Status': status,
            'Response': response_data
        }
        df_get_slots = pd.concat([df_get_slots, pd.DataFrame([new_row])], ignore_index=True)

        # Extract the slot ID from the response
        slots = response_data['data']['slot_data'][0]['slots']
        random_index = random.randint(0, len(slots) - 1)
        slot_id = slots[random_index]['id']

        print(slot_id)
        logger.info(slot_id)
        return slot_id

    def post_booking(self, venue_id, facility_id, slot_id):
        global df_post_booking  # Ensure df_post_booking is defined in global scope

        # Define the request body as form data
        request_body = {
            "user_details[name]": "Chirag test",
            "user_details[phone_number]": "1245454545",
            "user_details[date_of_birth]": "1991-01-01",
            "activity_id": "194",
            "payment_status": "1",
            "discount": "",
            "amount_paid": "100.0",
            "note": "",
            "invoice_type": "1",
            "use_offline_credits": "0",
            "slots[0]": slot_id,
            "send_payment_link": "0",
            "equipment_note": ""
        }

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        logger.info(
            f"Making POST request to /venues/{venue_id}/facilities/{facility_id}/bookings/new")
        logger.info(request_body)  # Logging statement

        # Make a POST request to the /bookings/new endpoint
        response = self.client.post(
            f"{BASE_URL}/venues/{venue_id}/facilities/{facility_id}/bookings/new",
            headers={**self.headers, 'Content-Type': 'application/x-www-form-urlencoded'},
            # Ensure Content-Type is set correctly
            data=request_body  # Use data parameter for form data
        )
        response_data = response.json()
        status = response.status_code
        logger.info(response_data)

        logger.info(f"Received response with status code {status}")  # Logging statement

        new_row = {
            'Status': status,
            'Response': response_data
        }
        df_post_booking = pd.concat([df_post_booking, pd.DataFrame([new_row])], ignore_index=True)

    def get_event(self):
        global df_post

        logger.info(f"Making GET request to {BASE_URL}/user/events")  # Logging statement

        response = self.client.get(f"{BASE_URL}/user/events",
                                   headers=self.headers)
        response_data = response.json()
        status = response.status_code
        logger.info(response_data)
        print(response_data)

        new_row = {
            'Status': status,
            'Response': response_data,

        }

        df_post = pd.concat([df_post, pd.DataFrame([new_row])], ignore_index=True)


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


def save_to_excel(df_login, df_get, df_post, df_get_venue, df_get_id, df_get_facility, df_get_slots, df_post_booking,
                  filename):
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df_login.to_excel(writer, index=False, sheet_name='Login Responses')
        df_get.to_excel(writer, index=False, sheet_name='Get Config Responses')
        df_post.to_excel(writer, index=False, sheet_name='Get Event Responses')
        df_get_venue.to_excel(writer, index=False, sheet_name='Get Venue Responses')
        df_get_id.to_excel(writer, index=False, sheet_name='Get Venue By ID Responses')
        df_get_facility.to_excel(writer, index=False, sheet_name='Get Facility By ID Responses')
        df_get_slots.to_excel(writer, index=False, sheet_name='Get Slots Responses')

        df_post_booking.to_excel(writer, index=False, sheet_name='Get Booking Responses')
        workbook = writer.book
        wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})

        for sheet_name in writer.sheets.keys():
            worksheet = writer.sheets[sheet_name]
            worksheet.set_column('A:Z', 20, wrap_format)


def on_quitting(environment):
    global df_login, df_get, df_post, df_get_venue
    save_to_excel(df_login, df_get, df_post, df_get_venue, df_get_id, df_get_facility, df_get_slots,
                  df_post_booking, f'responses_{timestamp}.xlsx')


events.quitting.add_listener(on_quitting)
