import os
import datetime
import logging
from locust import HttpUser, task, between, SequentialTaskSet
from faker import Faker

fake = Faker()

BASE_URL = os.environ.get("BASE_URL", "https://testing.api.hudle.in/api/v1")


class UserBehavior(SequentialTaskSet):
    def __init__(self, parent):
        super().__init__(parent)
        self.email = None
        self.password = None

    @task
    def register_and_login(self):
        # Call the post_data task and get the email and password
        self.email, self.password = self.post_data()

        # Check if email and password are set
        if self.email is not None and self.password is not None:
            # Call the login task with the email and password
            self.login()
        else:
            # Log an error message
            logger.error("Email and password not set")

    def post_data(self):
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
