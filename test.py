import random
from faker import Faker
from locust import HttpUser, task, between, SequentialTaskSet

fake = Faker('en_IN')


def custom_phone_number():

    return f"3{random.randint(10 ** 9, 10 ** 10 - 1)}"


class UserBehavior(SequentialTaskSet):
    user_phone_number = None

    def on_start(self):
        self.user_phone_number = custom_phone_number()

 def _post(self, endpoint, json_body=None, files=None):
    headers = {
        'Api-Secret': self.api_key,
        'Accept': 'application/json',
        'x-app-id': self.user_phone_number
    }
    with self.client.post(endpoint, json=json_body, files=files, headers=headers, catch_response=True) as response:
        if response.ok:
            print(f"{endpoint.capitalize()} Response:", response.json())
        else:
            print(f"{endpoint.capitalize()} Failed:", response.text)
            response.failure(f"{endpoint.capitalize()} request failed")
        assert response.elapsed.total_seconds() * 1000 < self.MAX_RESPONSE_TIME_MS, f"{endpoint.capitalize()} API took too long!"


    @task
    def register_consumer(self):
        files = {
            'email': (None, fake.email()),
            'name': (None, fake.name()),
            'password': (None, fake.password()),
            'password_confirmation': (None, fake.password()),
            'address': (None, 'delhi'),
            'phone_number': (None, self.user_phone_number),
            'date_of_birth': (None, fake.date_of_birth().strftime('%Y-%m-%d')),
            'gender': (None, 1),
            'email_updates': (None, 1)
        }
        self._post('/api/v1/register/consumer', files=files)

    @task
    def generate_otp(self):
        json_body = {'phone_number': self.user_phone_number, 'type': 2}
        headers = {
            'Api-Secret': self.user.api_key,
            'x-app-source': 'consumer',
            'x-Device-Source': '1',
            'x-app-id': self.user_phone_number
        }
        with self.client.post('/api/v1/otp/new', json=json_body, headers=headers, catch_response=True) as response:
            if response.status_code == 204:
                print("OTP Generation Successful: Status code 204 received.")
            else:
                print("OTP Generation Failed:", response.text)
                response.failure("OTP generation request failed")
            assert response.elapsed.total_seconds() * 1000 < self.user.MAX_RESPONSE_TIME_MS, "OTP generation API took too long!"

    @task
    def login_consumer(self):
        json_body = {'code': '48353', 'phone_number': self.user_phone_number, 'type': 2}
        headers = {
            'Api-Secret': self.user.api_key,
            'x-app-version': '3.2.9',
            'x-app-id': self.user_phone_number
        }
        self._post('/api/v1/otp/verify', json_body, headers=headers)
        self.interrupt()

    @task
    def get_cities(self):
        headers = {
            'Api-Secret': self.user.api_key,
            'x-app-id': self.user_phone_number
        }
        with self.client.get('/api/v1/cities', headers=headers, catch_response=True) as response:
            if response.ok:
                print("Cities Response:", response.json())
            else:
                print("Cities Request Failed:", response.text)
                response.failure("Cities request failed")
            assert response.elapsed.total_seconds() * 1000 < self.user.MAX_RESPONSE_TIME_MS, "Cities API took too long!"

    @task
    def delete_account_reason(self):
        headers = {
            'Api-Secret': self.user.api_key,
            'x-app-id': self.user_phone_number
        }
        with self.client.get('/api/v1/get-deletion-token', headers=headers, catch_response=True) as response:
            if response.ok:
                print("delete_account_reason Response:", response.json())
            else:
                response.failure("delete_account_reason request failed")
                print(response.text)
        self.interrupt()


class APITestUser(HttpUser):
    wait_time = between(1, 5)
    api_key = 'hudle-api1798@prod'
    MAX_RESPONSE_TIME_MS = 2000

    tasks = [UserBehavior]