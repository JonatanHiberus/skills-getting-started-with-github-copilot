"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    global activities
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert len(data["Chess Club"]["participants"]) == 2
        assert data["Chess Club"]["max_participants"] == 12

    def test_get_activities_returns_correct_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=new.student@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "new.student@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "test.student@mergington.edu"
        client.post(f"/activities/Programming%20Class/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data["Programming Class"]["participants"]

    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signup is rejected"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self, client):
        """Test signup for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_missing_email(self, client):
        """Test signup without email parameter"""
        response = client.post("/activities/Chess%20Club/signup")
        assert response.status_code == 422  # Unprocessable Entity


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]

    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering a participant who is not signed up"""
        email = "notregistered@mergington.edu"
        response = client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"].lower()

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_unregister_missing_email(self, client):
        """Test unregister without email parameter"""
        response = client.delete("/activities/Chess%20Club/unregister")
        assert response.status_code == 422  # Unprocessable Entity


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_signup_and_unregister_flow(self, client):
        """Test complete flow of signing up and then unregistering"""
        email = "flow.test@mergington.edu"
        activity = "Gym Class"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        get_response = client.get("/activities")
        assert email in get_response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        final_response = client.get("/activities")
        assert email not in final_response.json()[activity]["participants"]

    def test_multiple_signups_different_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multi.activity@mergington.edu"
        
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        client.post(f"/activities/Programming%20Class/signup?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary Redirect
        assert response.headers["location"] == "/static/index.html"
