"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from email import message
import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data


# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.user = User.signup(username="testuser",
                                email="test@test.com",
                                password="testuser",
                                image_url=None)

        db.session.commit()

        self.message = Message(
            text="Test test test",
            user_id=self.user.id
        )

        db.session.add(self.message)
        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_add_message_valid_user(self):
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user.id

            resp = client.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = (Message
                   .query
                   .filter(Message.id != self.message.id)
                   .one()
                   )
            self.assertEqual(msg.text, "Hello")
            self.assertEqual(msg.user_id, self.user.id)

    def test_add_message_invalid_user(self):
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = 23456789098767

            resp = client.post(
                "/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_message_no_session(self):
        with self.client as client:
            resp = client.post(
                "/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_view_message(self):
        with self.client as client:
            resp = client.get(f"/messages/{self.message.id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.message.text, str(resp.data))

    def test_delete_message(self):
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user.id

            resp = client.post(
                f"/messages/{self.message.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(Message.query.first(), None)

    def test_delete_message_no_session(self):
        with self.client as client:
            resp = client.post(
                f"/messages/{self.message.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            self.assertEqual(Message.query.first(), self.message)

    def test_delete_message_invalid_user(self):
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = 234567890987654

            resp = client.post(
                f"/messages/{self.message.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            self.assertEqual(Message.query.first(), self.message)
