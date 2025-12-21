"""
Unit Tests for Issue Management - Phase 5 (FIXED)
File: tests/test_issues.py
"""

import pytest
import sys
import os
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src import create_app, db
from src.models import User, Room, Issue, IssueComment


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
    """Create a test user - returns user ID"""
    with app.app_context():
        user = User(
            name='Test Staff',
            email='staff@test.com',
            role='staff'
        )
        user.set_password('test123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    return user_id


@pytest.fixture
def test_room(app):
    """Create a test room - returns room ID"""
    with app.app_context():
        room = Room(
            building='TEST',
            number='101',
            status='Available'
        )
        db.session.add(room)
        db.session.commit()
        room_id = room.id
    return room_id


@pytest.fixture
def test_issue(app, test_room, test_user):
    """Create a test issue - returns issue ID"""
    with app.app_context():
        issue = Issue(
            room_id=test_room,
            reporter_id='Test Reporter',
            description='Test issue description',
            status='New'
        )
        db.session.add(issue)
        db.session.commit()
        issue_id = issue.id
    return issue_id


def login(client, email='staff@test.com', password='test123'):
    """Helper function to login"""
    return client.post('/auth/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)


# ============= Test 1: Issue Assignment =============
def test_issue_assignment(app, client, test_user, test_room, test_issue):
    """Test assigning an issue to a user"""
    with app.app_context():
        # Login
        login(client)
        
        # Assign issue
        response = client.post(
            f'/issues/{test_issue}/assign',
            data={'assigned_to': test_user},
            follow_redirects=True
        )
        
        assert response.status_code == 200
        
        # Check database
        issue = Issue.query.get(test_issue)
        assert issue.assigned_to == test_user
        assert issue.status == 'In Progress'  # Should auto-change from New
        
        # Check timeline comment was created
        comment = IssueComment.query.filter_by(
            issue_id=test_issue,
            comment_type='assignment'
        ).first()
        assert comment is not None
        print("✅ Test 1 passed: Issue assignment works!")


# ============= Test 2: Status Transitions =============
def test_issue_status_transitions(app, client, test_user, test_room):
    """Test issue status lifecycle: New → In Progress → Resolved"""
    with app.app_context():
        # Create issue
        issue = Issue(
            room_id=test_room,
            reporter_id='Tester',
            description='Status transition test',
            status='New'
        )
        db.session.add(issue)
        db.session.commit()
        issue_id = issue.id
        
        # Login
        login(client)
        
        # Transition 1: New → In Progress
        response = client.post(
            f'/issues/{issue_id}/update-status',
            data={'status': 'In Progress'},
            follow_redirects=True
        )
        assert response.status_code == 200
        
        issue = Issue.query.get(issue_id)
        assert issue.status == 'In Progress'
        
        # Transition 2: In Progress → Resolved
        response = client.post(
            f'/issues/{issue_id}/update-status',
            data={'status': 'Resolved'},
            follow_redirects=True
        )
        assert response.status_code == 200
        
        issue = Issue.query.get(issue_id)
        assert issue.status == 'Resolved'
        assert issue.resolved_at is not None  # Should set timestamp
        
        # Check timeline comments created
        comments = IssueComment.query.filter_by(
            issue_id=issue_id,
            comment_type='status_change'
        ).all()
        assert len(comments) == 2  # Two status changes
        print("✅ Test 2 passed: Status transitions work!")


# ============= Test 3: Add Comment =============
def test_add_comment(app, client, test_user, test_issue):
    """Test adding a comment to an issue"""
    with app.app_context():
        # Login
        login(client)
        
        # Add comment
        comment_text = 'This is a test comment'
        response = client.post(
            f'/issues/{test_issue}/comment',
            data={'comment_text': comment_text},
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Comment added successfully' in response.data
        
        # Check database
        comment = IssueComment.query.filter_by(
            issue_id=test_issue,
            comment_type='comment'
        ).first()
        
        assert comment is not None
        assert comment.comment_text == comment_text
        assert comment.user_id == test_user
        print("✅ Test 3 passed: Add comment works!")


# ============= Test 4: Empty Comment Rejected =============
def test_empty_comment_rejected(app, client, test_user, test_issue):
    """Test that empty comments are rejected"""
    with app.app_context():
        login(client)
        
        # Try to add empty comment
        response = client.post(
            f'/issues/{test_issue}/comment',
            data={'comment_text': '   '},  # Only whitespace
            follow_redirects=True
        )
        
        assert b'Comment cannot be empty' in response.data
        
        # Check no comment was created
        count = IssueComment.query.filter_by(issue_id=test_issue).count()
        assert count == 0
        print("✅ Test 4 passed: Empty comments rejected!")


# ============= Test 5: Issue Detail Page Loads =============
def test_issue_detail_page(app, client, test_user, test_issue):
    """Test that issue detail page loads correctly"""
    with app.app_context():
        login(client)
        
        response = client.get(f'/issues/{test_issue}')
        
        assert response.status_code == 200
        assert b'Issue #' in response.data
        
        # Get issue to check description
        issue = Issue.query.get(test_issue)
        assert issue.description.encode() in response.data
        assert b'Timeline & Comments' in response.data
        print("✅ Test 5 passed: Issue detail page loads!")


# ============= Test 6: Invalid Status Rejected =============
def test_invalid_status_rejected(app, client, test_user, test_issue):
    """Test that invalid status values are rejected"""
    with app.app_context():
        login(client)
        
        response = client.post(
            f'/issues/{test_issue}/update-status',
            data={'status': 'InvalidStatus'},
            follow_redirects=True
        )
        
        assert b'Invalid status' in response.data
        
        # Status should remain unchanged
        issue = Issue.query.get(test_issue)
        assert issue.status == 'New'
        print("✅ Test 6 passed: Invalid status rejected!")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])