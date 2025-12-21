"""
Unit Tests for Room Search & Filter - Phase 5
File: tests/test_search.py
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src import create_app, db
from src.models import User, Room


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
        user = User(name='Test User', email='test@test.com', role='staff')
        user.set_password('test123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_rooms(app):
    """Create multiple test rooms"""
    with app.app_context():
        rooms = [
            Room(building='AB', number='101', status='Available', capacity=30),
            Room(building='AB', number='102', status='Occupied', capacity=50),
            Room(building='CD', number='201', status='Available', capacity=40),
            Room(building='EF', number='301', status='Available', capacity=100),
            Room(building='EF', number='302', status='Occupied', capacity=80),
        ]
        for room in rooms:
            db.session.add(room)
        db.session.commit()
        return rooms


def login(client):
    """Helper to login"""
    client.post('/auth/login', data={
        'email': 'test@test.com',
        'password': 'test123'
    })


# ============= Test 1: Search Page Loads =============
def test_search_page_loads(app, client, test_user, test_rooms):
    """Test that search page loads successfully"""
    with app.app_context():
        login(client)
        
        response = client.get('/rooms/search')
        assert response.status_code == 200
        assert b'Search & Filter Rooms' in response.data


# ============= Test 2: Keyword Search =============
def test_keyword_search(app, client, test_user, test_rooms):
    """Test searching by keyword"""
    with app.app_context():
        login(client)
        
        # Search for "AB"
        response = client.get('/rooms/search?q=AB')
        assert response.status_code == 200
        assert b'AB 101' in response.data
        assert b'AB 102' in response.data
        assert b'CD 201' not in response.data  # Should not appear


# ============= Test 3: Building Filter =============
def test_building_filter(app, client, test_user, test_rooms):
    """Test filtering by building"""
    with app.app_context():
        login(client)
        
        # Filter by building "EF"
        response = client.get('/rooms/search?building=EF')
        assert response.status_code == 200
        assert b'EF 301' in response.data
        assert b'EF 302' in response.data
        assert b'AB' not in response.data  # AB rooms should not appear


# ============= Test 4: Status Filter =============
def test_status_filter(app, client, test_user, test_rooms):
    """Test filtering by status"""
    with app.app_context():
        login(client)
        
        # Filter by "Available"
        response = client.get('/rooms/search?status=Available')
        assert response.status_code == 200
        
        # Should show available rooms
        assert b'AB 101' in response.data
        assert b'CD 201' in response.data
        
        # Should not show occupied rooms
        assert b'AB 102' not in response.data


# ============= Test 5: Capacity Range Filter =============
def test_capacity_filter(app, client, test_user, test_rooms):
    """Test filtering by capacity range"""
    with app.app_context():
        login(client)
        
        # Filter: capacity between 40 and 60
        response = client.get('/rooms/search?capacity_min=40&capacity_max=60')
        assert response.status_code == 200
        
        # Should show rooms with capacity 40, 50
        assert b'AB 102' in response.data  # 50
        assert b'CD 201' in response.data  # 40
        
        # Should not show rooms with capacity 30, 80, 100
        assert b'AB 101' not in response.data  # 30
        assert b'EF 302' not in response.data  # 80


# ============= Test 6: Combined Filters =============
def test_combined_filters(app, client, test_user, test_rooms):
    """Test using multiple filters together"""
    with app.app_context():
        login(client)
        
        # Filter: building=EF AND status=Available
        response = client.get('/rooms/search?building=EF&status=Available')
        assert response.status_code == 200
        
        # Should only show EF 301 (Available)
        assert b'EF 301' in response.data
        
        # Should not show EF 302 (Occupied) or other buildings
        assert b'EF 302' not in response.data
        assert b'AB' not in response.data


# ============= Test 7: JSON Response =============
def test_json_response(app, client, test_user, test_rooms):
    """Test JSON format response"""
    with app.app_context():
        login(client)
        
        # Request JSON format
        response = client.get('/rooms/search?building=AB&format=json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'count' in data
        assert 'rooms' in data
        assert data['count'] == 2  # AB has 2 rooms
        assert len(data['rooms']) == 2


# ============= Test 8: No Results =============
def test_no_results(app, client, test_user, test_rooms):
    """Test search with no matching results"""
    with app.app_context():
        login(client)
        
        # Search for non-existent building
        response = client.get('/rooms/search?building=XYZ')
        assert response.status_code == 200
        assert b'No rooms match your search criteria' in response.data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])