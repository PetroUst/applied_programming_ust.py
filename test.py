from unittest import TestCase
from base64 import b64encode
import unittest

from lab_7 import app, s
import json


app.testing = True

client = app.test_client()

class BaseTestCase(TestCase):
    client = app.test_client()

    def setUp(self):
        super().setUp()
        self.user_1_credentials = b64encode(b"PetroUst:12345").decode('utf-8')
        self.super_1_credentials = b64encode(b"Giga:12345").decode('utf-8')
        self.super_2_credentials = b64encode(b"Dzidzio:12345").decode('utf-8')
        self.ticket_1_data = {
            "TicketId": 100,
            "EventId": 1,
            "Price": 20,
            "Line": 1,
            "Place": 20,
            "IsBooked": 0,
            "IsPaid": 0,
        }
        self.ticket_wrong_data = {
            "TicketId": "ada",
            "EventId": 1,
            "Price": 20,
            "Line": 1,
            "Place": 20,
            "IsBooked": 0,
            "IsPaid": 0,
        }
        self.event_1_data = {
            "EventName": "test concert",
            "Time": "2022-11-20 19:00:00",
            "City": "Lviv",
            "Location" : "Opera",
            "MaxTickets" : 500,
        }
        self.event_2_data = {
            "EventName": "test 2 concert",
            "Time": "2022-11-20 19:00:00",
            "City": "Lviv",
            "Location": "Opera",
            "MaxTickets": 500,
        }
        self.user_1_data={
            "Username":"user_test",
            "Name":"test",
            "Surname":"sur_test",
            "Email":"test@mail.com",
            "Password":"test_password",
        }
        # self.super_1_data = {
        #     "Username": "super_test",
        #     "Name": "supertest",
        #     "Surname": "super_test",
        #     "Email": "super@mail.com",
        #     "Password": "super_test_password",
        # }

    def tearDown(self):
        self.close_session()

    def close_session(self):
        s.close()

    def create_app(self):
        app.config['TESTING'] = True
        return app

    def get_auth_headers(self, credentials):
        return {"Authorization": f"Basic {credentials}"}

class Test(BaseTestCase):
    def test_add_user(self):
        response = self.client.post("/User", json=self.user_1_data)
        self.assertEqual(response.status_code, 200)
    def test_add_event(self):
        response = self.client.post("/Event", json=self.event_1_data,
        headers=self.get_auth_headers(self.super_1_credentials))
        self.assertEqual(response.status_code, 200)

    def test_get_ticket_by_id(self):
        response = self.client.get("/Ticket/1")
        self.assertEqual(response.status_code, 200)

    def test_get_all_tickets_on_event(self):
        response = self.client.get("/Ticket/get-by-event-id/4")
        self.assertEqual(response.status_code, 200)

    def test_get_all_users_tickets(self):
        response = self.client.get("/Ticket/get-by-userid/PetroUst",headers=self.get_auth_headers(self.user_1_credentials))
        self.assertEqual(response.status_code, 200)

    def test_wrong_username(self):
        response = self.client.get("/Ticket/get-by-userid/NONAME",headers=self.get_auth_headers(self.user_1_credentials))
        self.assertEqual(response.status_code, 403)

    def test_wrong_auth(self):
        response = self.client.get("/Ticket/get-by-userid/PetroUst",headers=self.get_auth_headers(self.super_1_credentials))
        self.assertEqual(response.status_code, 403)

    def test_add_ticket(self):
        response = self.client.post("/Ticket", json=self.ticket_1_data,
        headers=self.get_auth_headers(self.super_1_credentials))
        self.assertEqual(response.status_code, 200)

    def test_wrong_auth_add_ticket(self):
        response = self.client.post("/Ticket", json=self.ticket_1_data,
        headers=self.get_auth_headers(self.user_1_credentials))
        self.assertEqual(response.status_code, 403)

    def test_wrong_data_add_ticket(self):
        response = self.client.post("/Ticket", json=self.ticket_wrong_data,
        headers=self.get_auth_headers(self.user_1_credentials))
        self.assertEqual(response.status_code, 403)


    def test_delete_ticket(self):
        response = self.client.delete("/Ticket/1",
        headers=self.get_auth_headers(self.super_1_credentials))
        self.assertEqual(response.status_code, 200)

    def test_update_event(self):
        response = self.client.put("/Event/1", data=json.dumps({
            "EventName": "Dzidzio CONCERT",
            "Time": "2022-11-20 19:00:00",
            "City": "Lutsk",
            "Location": "Staleva Gora",
            "MaxTickets": "200"
        }), content_type='application/json', headers=self.get_auth_headers(self.super_1_credentials))
        self.assertEqual(response.status_code, 200)
    def test_wrong_auth_update_event(self):
        response = self.client.post("/Event/1", json=self.event_1_data,
        headers=self.get_auth_headers(self.super_1_credentials))
        self.assertEqual(response.status_code, 405)



    def test_wrong_auth_add_event(self):
        response = self.client.post("/Event", json=self.event_1_data,
        headers=self.get_auth_headers(self.user_1_credentials))
        self.assertEqual(response.status_code, 403)


    def test_add_super_user(self):
        response = self.client.post("/SuperUser", json=self.user_1_data)
        self.assertEqual(response.status_code, 200)


    def test_booking(self):
        response = self.client.put("/User/booking/1", content_type='application/json', headers=self.get_auth_headers(self.user_1_credentials))
        self.assertEqual(response.status_code, 200)

    def test_booking_cancel(self):
        response = self.client.put("/User/cancel/1", content_type='application/json', headers=self.get_auth_headers(self.user_1_credentials))
        self.assertEqual(response.status_code, 200)


    def test_buying(self):
        response = self.client.put("/User/buying/1", content_type='application/json', headers=self.get_auth_headers(self.user_1_credentials))
        self.assertEqual(response.status_code, 200)


    def test_wrong_auth_delete_event(self):
        response = self.client.delete("/Event/4",
        headers=self.get_auth_headers(self.user_1_credentials))
        self.assertEqual(response.status_code, 403)

    def test_wrong_add_user(self):
        response = self.client.post("/User", json=self.user_1_data)
        self.assertEqual(response.status_code, 200)
    def test_get_all_tickets_on_event(self):
        response = self.client.get("/Event/get-all-events")
        self.assertEqual(response.status_code, 200)
    def test_delete_event(self):
        response = self.client.delete("/Event/4",
        headers=self.get_auth_headers(self.super_1_credentials))
        self.assertEqual(response.status_code, 200)