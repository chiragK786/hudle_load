# import random
# from locust import HttpUser, task, between, SequentialTaskSet, events
# from faker import Faker
#
# fake = Faker('en_IN')
#
#
# def custom_phone_number():
#     first_digit = random.choice(['3', '4', '5'])
#     remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
#     return first_digit + remaining_digits
#
#
# class APITestUser(HttpUser):
#     wait_time = between(1, 5)
#     api_key = 'hudle-api1798@prod'  # Common API key for all APIs
#     MAX_RESPONSE_TIME_MS = 2000
#
#     class UserBehavior(SequentialTaskSet):
#
#         def on_start(self):
#             self.user_phone_number = custom_phone_number()
#
#         @task
#         def register_consumer(self):
#             headers = {
#                 'Api-Secret': self.user.api_key,
#                 'Accept': 'application/json',
#                 'x-app-id': self.user_phone_number
#             }
#             files = {
#                 'email': (None, fake.email()),
#                 'name': (None, fake.name()),
#                 'password': (None, fake.password()),
#                 'password_confirmation': (None, fake.password()),
#                 'address': (None, 'delhi'),
#                 'phone_number': (None, self.user_phone_number),
#                 'date_of_birth': (None, fake.date_of_birth().strftime('%Y-%m-%d')),
#                 'gender': (None, 1),
#                 'email_updates': (None, 1)
#             }
#             with self.client.post('/api/v1/register/consumer', files=files,
#                                   headers=headers, catch_response=True) as response:
#                 if response.ok:
#                     print("Registration Response:", response.json())
#                 else:
#                     print("Registration Failed:", response.text)
#                     response.failure("Registration request failed")
#
#         @task
#         def generate_otp(self):
#             headers = {
#                 'Api-Secret': self.user.api_key,
#                 'x-app-source': 'consumer',
#                 'x-Device-Source': '1',
#                 'x-app-id': self.user_phone_number
#             }
#             json_body = {
#                 'phone_number': self.user_phone_number,
#                 'type': 2
#             }
#             with self.client.post('/api/v1/otp/new', json=json_body,
#                                   headers=headers, catch_response=True) as response:
#                 if response.status_code == 204:
#                     print("OTP Generation Successful: Status code 204 received.")
#                 else:
#                     print("OTP Generation Failed:", response.text)
#                     response.failure("OTP generation request failed")
#
#             assert response.elapsed.total_seconds() * 1000 < 1000, "Cities API took too long!"
#
#         @task
#         def login_consumer(self):
#             headers = {
#                 'Api-Secret': self.user.api_key,
#                 'x-app-version': '3.2.9',
#                 'x-app-id': self.user_phone_number
#             }
#             json_body = {
#                 'code': '48353',
#                 'phone_number': self.user_phone_number,
#                 'type': 2
#             }
#             with self.client.post('/api/v1/otp/verify', json=json_body,
#                                   headers=headers, catch_response=True) as response:
#                 if response.ok:
#                     print("Login Response:", response.json())
#                 else:
#                     print("Login Failed:", response.text)
#                     response.failure("Login request failed")
#             # Stop the task set after the login task is executed
#
#             assert response.elapsed.total_seconds() * 1000 < 1000, "Login API took too long!"
#
#         @task
#         def get_cities(self):
#             headers = {
#                 'Api-Secret': self.user.api_key,
#                 'x-app-id': self.user_phone_number
#             }
#             with self.client.get('/api/v1/cities', headers=headers,
#                                  catch_response=True) as response:
#                 if response.ok:
#                     print("Cities Response:", response.json())
#                 else:
#                     print("Cities Request Failed:", response.text)
#                     response.failure("Cities request failed")
#                     assert response.elapsed.total_seconds() * 1000 < 1000, "Cities API took too long!"
#
#         @task
#         def delete_account_reason(self):
#             headers = {
#                 'Api-Secret': self.user.api_key,
#                 'x-app-id': self.user_phone_number
#             }
#             with self.client.get('/api/v1/get-deletion-token', headers=headers,
#                                  catch_response=True) as response:
#                 if response.ok:
#                     print("delete_account_reason Response:", response.json())
#                 else:
#                     response.failure("delete_account_reason request failed")
#                     print(response.text)
#
#             self.interrupt()
