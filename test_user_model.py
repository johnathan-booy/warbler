"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

from email.mime import image
from lib2to3.pytree import type_repr
from multiprocessing.sharedctypes import Value
import os
from typing import Type
from unittest import TestCase
from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app
from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

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

        db.session.commit()

        self.client = app.test_client()

    def tearDown(self) -> None:
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        u = User(
            username="testuser",
            email="test@test.com",
            password="testing",
            image_url="https://www.test.com",
            header_image_url="https://www.test.com",
            bio="I am the ultimate test champion.",
            location="Testville"
        )

        # User should have no messages, followers, following or liked_messages
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.liked_messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.following), 0)

        # Test user representation
        self.assertEqual(repr(u), f"<User #None: testuser, test@test.com>")

        # Test other params
        self.assertEqual(u.image_url, "https://www.test.com")

    #################################
    # Test Authorization
    #################################

    def test_valid_authentication(self):
        u1 = User.authenticate(
            username=self.u1.username,
            password="password"
        )
        self.assertIsInstance(u1, User)
        self.assertEqual(u1.username, self.u1.username)
        self.assertEqual(u1.email, self.u1.email)

    def test_invalid_password_authentication(self):
        u1 = User.authenticate(
            username=self.u1.username,
            password="invalid"
        )
        self.assertFalse(u1)

    def test_invalid_username_authentication(self):
        u1 = User.authenticate(
            username="invalid",
            password="password"
        )
        self.assertFalse(u1)

    ###########################
    # Test Signup
    ###########################

    def test_valid_signup(self):
        u = User.signup(username="valid", email="valid@test.com",
                        password="password", image_url=None)
        self.assertIsInstance(u, User)
        self.assertEqual(u.username, "valid")
        self.assertEqual(u.email, "valid@test.com")
        self.assertNotEqual(u.password, "password")

    def test_invalid_username_signup(self):
        u = User.signup(username=None, email="valid@test.com",
                        password="password", image_url=None)
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_unavailable_username_signup(self):
        u = User.signup(username=self.u1.username, email="valid@test.com",
                        password="password", image_url=None)
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_unavailable_email_signup(self):
        u = User.signup(username="valid", email=self.u1.email,
                        password="password", image_url=None)
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_invalid_email_signup(self):
        u = User.signup(username="valid", email=None,
                        password="password", image_url=None)
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError):
            u = User.signup(username="valid", email="valid@test.com",
                            password=None, image_url=None)

    #########################
    # Test Following
    #########################

    def test_user_follows(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)

        self.assertEqual(self.u1.following[0].id, self.u2.id)
        self.assertEqual(self.u2.followers[0].id, self.u1.id)

    def test_is_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))
