import os
import unittest
import app
from datetime import date
from books_app.extensions import app, db, bcrypt
from books_app.models import Book, Author, User, Audience, Genre

"""
Run these tests with the command:
python3 -m unittest books_app.main.tests
"""

#################################################
# Setup
#################################################

def login(client, username, password):
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)

def create_books():
    a1 = Author(name='J.R.R. Tolkien')
    b1 = Book(
        title='The Hobbit',
        publish_date=date(1937, 9, 21),
        author=a1
    )
    db.session.add(b1)

    a2 = Author(name='F. Scott Fitzgerald')
    b2 = Book(title='The Great Gatsby', author=a2)
    db.session.add(b2)
    db.session.commit()

def create_user():
    # Creates a user with username 'johndoe' and password of 'mypassword'
    password_hash = bcrypt.generate_password_hash('mypassword').decode('utf-8')
    user = User(username='johndoe', password=password_hash)
    db.session.add(user)
    db.session.commit()


#################################################
# Tests
#################################################

class MainTests(unittest.TestCase):
 
    def setUp(self):
        """Executed prior to each test."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.drop_all()
        db.create_all()
 
    def test_homepage_logged_out(self):
        create_books()
        create_user()

        with self.app:
            self.app.get('/logout', follow_redirects=True)

        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        response_text = response.get_data(as_text=True)
        self.assertIn('Log In', response_text)

    def test_homepage_logged_in(self):
        """Test that the books show up on the homepage."""
        create_books()
        create_user()
        login(self.app, 'johndoe', 'mypassword')

        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response_text = response.get_data(as_text=True)
        self.assertIn('The Hobbit', response_text)
        self.assertIn('The Great Gatsby', response_text)
        self.assertIn('johndoe', response_text)
        self.assertIn('Create Book', response_text)
        self.assertIn('Create Author', response_text)
        self.assertIn('Create Genre', response_text)

        self.assertNotIn('Log In', response_text)
        self.assertNotIn('Sign Up', response_text)

    def test_book_detail_logged_out(self):
        """Test that the book appears on its detail page."""
        create_books()
        create_user()

        with self.app:
            self.app.get('/logout', follow_redirects=True)

        response = self.app.get('/book/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response_text = response.get_data(as_text=True)
        self.assertIn("<h1>The Hobbit</h1>", response_text)
        self.assertIn("J.R.R. Tolkien", response_text)
        self.assertNotIn("Favorite This Book", response_text)

    def test_book_detail_logged_in(self):
        """Test that the book appears on its detail page."""
        create_books()
        create_user()
        login(self.app, 'johndoe', 'mypassword')

        response = self.app.get('/book/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response_text = response.get_data(as_text=True)
        self.assertIn("<h1>The Hobbit</h1>", response_text)
        self.assertIn("J.R.R. Tolkien", response_text)
        self.assertIn("Favorite This Book", response_text)

    def test_update_book(self):
        """Test updating a book."""
        create_books()
        create_user()
        login(self.app, 'johndoe', 'mypassword')

        post_data = {
            'title': 'The Silmarillion',
            'publish_date': '1977-09-15',
            'author': 1,
            'audience': 'ADULT',
            'genres': []
        }
        self.app.post('/book/1', data=post_data)
        
        book = Book.query.get(1)
        self.assertEqual(book.title, 'The Silmarillion')
        self.assertEqual(book.publish_date, date(1977, 9, 15))
        self.assertEqual(book.audience, Audience.ADULT)

    def test_create_book(self):
        """Test creating a book."""
        create_books()
        create_user()
        login(self.app, 'johndoe', 'mypassword')

        post_data = {
            'title': 'Brave New World',
            'publish_date': '1932-08-31',
            'author': 1,
            'audience': 'ADULT',
            'genres': []
        }
        self.app.post('/create_book', data=post_data)

        created_book = Book.query.filter_by(title='Brave New World').one()
        self.assertIsNotNone(created_book)
        self.assertEqual(created_book.author.name, 'J.R.R. Tolkien')

    def test_create_book_logged_out(self):
        create_books()
        create_user()

        with self.app:
            self.app.get('/logout', follow_redirects=True)

        response = self.app.get('/create_book', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        response_text = response.get_data(as_text=True)
        self.assertIn("Log In", response_text)

    def test_create_author(self):
        """Test creating an author."""
        create_user()
        login(self.app, 'johndoe', 'mypassword')

        post_data = {
            'name': 'Agatha Christie',
            'biography': 'Agatha Christie Bio',
        }
        self.app.post('/create_author', data=post_data)

        created_author = Author.query.filter_by(name='Agatha Christie').one()
        self.assertIsNotNone(created_author)
        self.assertEqual(created_author.biography, 'Agatha Christie Bio')

    def test_create_genre(self):
        create_user()
        login(self.app, 'johndoe', 'mypassword')

        post_data = {
            'name': 'mystery',
        }
        self.app.post('/create_genre', data=post_data)

        created_genre = Genre.query.filter_by(name='mystery').one()
        self.assertIsNotNone(created_genre)
        self.assertEqual(created_genre.name, 'mystery')

    def test_profile_page(self):
        create_user()
        login(self.app, 'johndoe', 'mypassword')
        
        response = self.app.get('/profile/johndoe', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response_text = response.get_data(as_text=True)
        self.assertIn('johndoe', response_text)
        self.assertIn('Create Book', response_text)
        self.assertIn('Create Author', response_text)
        self.assertIn('Create Genre', response_text)
        self.assertIn('Log Out', response_text)

    def test_favorite_book(self):
        create_user()
        create_books()
        login(self.app, 'johndoe', 'mypassword')

        post_data = {
            'book_id': 1,
        } 
        self.app.post('/favorite/1', data=post_data)
        
        user = User.query.filter_by(username='johndoe').first()
        book = Book.query.get(1)
        self.assertIn(book, user.favorite_books)

    def test_unfavorite_book(self):
        create_user()
        create_books()
        login(self.app, 'johndoe', 'mypassword')

        post_data = {
            'book_id': 1,
        } 
        self.app.post('/unfavorite/1', data=post_data)

        user = User.query.filter_by(username='johndoe').first()
        book = Book.query.get(1)
        self.assertNotIn(book, user.favorite_books)
