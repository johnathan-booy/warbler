"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from models import db, connect_db, Message, User

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY


# Don't have WTForms use CSRF at all, since it's a pain to test
app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.u1 = User.signup(
            username="test1",
            password="password",
            email="test1@test.com",
            image_url=""
        )

        self.u2 = User.signup(
            username="test2",
            password="password",
            email="test2@test.com",
            image_url=""
        )

        self.u2.bio = "Test test test"
        db.session.commit()

        self.m1 = Message(
            user_id=1,
            text="Testing testing"
        )

        self.m2 = Message(
            user_id=2,
            text="Message about testing"
        )

        db.session.add_all([self.m1, self.m2])
        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_user_list(self):
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.u1.id

            resp = client.get(f"/users")

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"@{self.u1.username}", str(resp.data))
            self.assertIn(f"@{self.u1.image_url}", str(resp.data))
            self.assertIn(f"@{self.u2.username}", str(resp.data))
            self.assertIn(f"@{self.u2.image_url}", str(resp.data))
            self.assertIn("Follow</button>", str(resp.data))

    def test_user_list_unauthenticated(self):
        with self.client as client:

            resp = client.get(f"/users")

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("Follow</button>", str(resp.data))

    def test_user_search(self):
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.u1.id

            resp = client.get(f"/users?q={self.u1.username}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"@{self.u1.username}", str(resp.data))
            self.assertIn(f"@{self.u1.image_url}", str(resp.data))
            self.assertNotIn(f"@{self.u2.username}", str(resp.data))

    def test_user_show(self):
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.u1.id

            resp = client.get(f"/users/{self.u2.id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"@{self.u2.username}", str(resp.data))
            self.assertIn(self.u2.bio, str(resp.data))
            self.assertIn(self.u2.messages[0].text, str(resp.data))
