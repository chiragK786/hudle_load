import os
import json
from locust import HttpUser, task, between
from faker import Faker

fake = Faker()

BASE_URL = os.environ.get("BASE_URL", "https://testing.api.hudle.in/api/v1")


class QuickstartUser(HttpUser):
    host = "https://testing.api.hudle.in/"
    wait_time = between(1, 2)

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

        response = self.client.post(f"{BASE_URL}/register/partner", data=data)

        if response.status_code == 200:
            print("Data sent successfully!")
        else:
            print("Error sending data:", response.text)
