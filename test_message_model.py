"""Message model tests"""

from datetime import datetime
from email import message
import os
from unittest import TestCase
from models import db, User, Message, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app


class MessageModelTestCase(TestCase):
    """Test the Message model"""

    def setUp(self):
        """Create test client and sample data"""
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

        self.m1 = Message(
            user_id=1,
            text="Testing testing"
        )

        db.session.add(self.m1)
        db.session.commit()

    def tearDown(self) -> None:
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        self.assertIsNotNone(self.m1.id)
        self.assertEqual(datetime.utcnow().year, self.m1.timestamp.year)
        self.assertEqual(self.m1.text, "Testing testing")
        self.assertEqual(self.m1.user_id, 1)
        self.assertEqual(self.m1.user, self.u1)
        self.assertEqual(self.u1.messages[0], self.m1)

    def test_message_likes(self):
        like = Likes(
            user_id=self.u2.id,
            message_id=self.m1.id
        )
        db.session.add(like)
        db.session.commit()

        self.assertEqual(len(Likes.query.all()), 1)
        self.assertEqual(self.u2.liked_messages[0].id, like.message_id)
