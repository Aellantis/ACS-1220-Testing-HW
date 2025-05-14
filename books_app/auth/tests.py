import os
from unittest import TestCase
import app
from datetime import date
from books_app.extensions import app, db, bcrypt
from books_app.models import Book, Author, User, Audience

def create_books():
    a1 = Author(name='Harper Lee')
    b1 = Book(
        title='To Kill a Mockingbird',
        publish_date=date(1960, 7, 11),
        author=a1
    )
    db.session.add(b1)

    a2 = Author(name='Sylvia Plath')
    b2 = Book(title='The Bell Jar', author=a2)
    db.session.add(b2)
    db.session.commit()

def create_user():
    password_hash = bcrypt.generate_password_hash('password').decode('utf-8')
    user = User(username='me1', password=password_hash)
    db.session.add(user)
    db.session.commit()

class AuthTests(TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.drop_all()
        db.create_all()

    def test_signup(self):
        post_data = {
            'username': 'Ashley Yung',
            'password': 'test'
        } 
        self.app.post('/signup', data=post_data)

        response = self.app.get('/profile/Ashley Yung')
        response_text = response.get_data(as_text=True)
        self.assertIn('Ashley Yung', response_text)

    def test_signup_existing_user(self):
        create_user()

        post_data = {
            'username': 'me1',
            'password': 'password',
        } 
        response = self.app.post('/signup', data=post_data)
        response_text = response.get_data(as_text=True)
        self.assertIn('That username is taken. Please choose a different one.', response_text)

    def test_login_correct_password(self):
        create_user()
        post_data = {
            'username': 'me1',
            'password': 'password',
        } 
        self.app.post('/login', data=post_data)
        response = self.app.get('/')
        response_text = response.get_data(as_text=True)
        self.assertNotIn('login', response_text)

    def test_login_nonexistent_user(self):
        post_data = {
            'username': 'Hallo',
            'password': 'World',
        }
        response = self.app.post('/login', data=post_data)
        response_text = response.get_data(as_text=True)
        self.assertIn('No user with that username. Please try again.', response_text)

    def test_login_incorrect_password(self):
        create_user()
        post_data = {
            'username': 'me1',
            'password': 'incorrect',
        }

        response = self.app.post('/login', data=post_data)
        response_text = response.get_data(as_text=True)
        self.assertIn('Password doesn&#39;t match. Please try again.', response_text)

    def test_logout(self):
        create_user()
        post_data = {
            'username': 'me1',
            'password': 'password',
        }

        self.app.post('/login', data=post_data)
        self.app.get('/logout')
        response = self.app.get('/')
        response_text = response.get_data(as_text=True)
        self.assertIn('login', response_text)
