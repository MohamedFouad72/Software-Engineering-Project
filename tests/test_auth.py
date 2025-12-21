import pytest
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src import create_app, db
from src.models import User

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(
            name='Test User',
            email='test@campus.edu',
            role='staff'
        )
        user.set_password('test123')
        db.session.add(user)
        db.session.commit()
        return user

def test_login_page_loads(client):
    """Test that login page loads successfully"""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Sign in' in response.data

def test_valid_login(client, test_user):
    """Test login with valid credentials"""
    response = client.post('/auth/login', data={
        'email': 'test@campus.edu',
        'password': 'test123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Welcome back' in response.data

def test_invalid_login(client, test_user):
    """Test login with invalid credentials"""
    response = client.post('/auth/login', data={
        'email': 'test@campus.edu',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    
    assert b'Invalid email or password' in response.data

def test_logout(client, test_user):
    """Test logout functionality"""
    # Login first
    client.post('/auth/login', data={
        'email': 'test@campus.edu',
        'password': 'test123'
    })
    
    # Then logout
    response = client.get('/auth/logout', follow_redirects=True)
    assert b'logged out successfully' in response.data

def test_password_hashing(app, test_user):
    """Test that passwords are hashed correctly"""
    with app.app_context():
        user = User.query.filter_by(email='test@campus.edu').first()
        assert user.password_hash != 'test123'
        assert user.check_password('test123') == True
        assert user.check_password('wrongpass') == False

def test_protected_route_redirect(client):
    """Test that protected routes redirect to login"""
    response = client.get('/dashboard')
    assert response.status_code == 302  # Redirect
    assert '/auth/login' in response.location