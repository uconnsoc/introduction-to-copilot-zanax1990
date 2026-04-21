"""
Test suite for Mergington High School Activities API.
"""
import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        """Root endpoint should redirect to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_dict(self, client):
        """GET /activities should return a dictionary of activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_contains_all_activities(self, client):
        """GET /activities should return all activities."""
        response = client.get("/activities")
        data = response.json()
        
        # Check for expected activities
        expected_activities = ["Chess Club", "Programming Class", "Gym Class", 
                             "Basketball", "Tennis Club", "Drama Club", 
                             "Art Studio", "Robotics Club", "Debate Team"]
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_structure(self, client):
        """Each activity should have required fields."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_participants_are_strings(self, client):
        """Participants should be stored as email strings."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            for participant in activity_details["participants"]:
                assert isinstance(participant, str)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_successful(self, client):
        """Successful signup should return 200 with success message."""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu",
            follow_redirects=False
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client):
        """Signup should add participant to activity's participants list."""
        # Get initial state
        response = client.get("/activities")
        initial_data = response.json()
        initial_count = len(initial_data["Chess Club"]["participants"])
        
        # Sign up
        new_email = "newstudent@mergington.edu"
        client.post(
            f"/activities/Chess Club/signup?email={new_email}",
            follow_redirects=False
        )
        
        # Verify participant added
        response = client.get("/activities")
        updated_data = response.json()
        assert new_email in updated_data["Chess Club"]["participants"]
        assert len(updated_data["Chess Club"]["participants"]) == initial_count + 1
    
    def test_signup_duplicate_email_returns_400(self, client):
        """Signing up with duplicate email should return 400."""
        # Try to sign up with an existing participant
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu",
            follow_redirects=False
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]
    
    def test_signup_invalid_activity_returns_404(self, client):
        """Signing up for non-existent activity should return 404."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu",
            follow_redirects=False
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
    
    def test_signup_new_email_to_multiple_activities(self, client):
        """Student can sign up for multiple different activities."""
        new_email = "multi@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            f"/activities/Chess Club/signup?email={new_email}",
            follow_redirects=False
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            f"/activities/Programming Class/signup?email={new_email}",
            follow_redirects=False
        )
        assert response2.status_code == 200
        
        # Verify in both
        response = client.get("/activities")
        data = response.json()
        assert new_email in data["Chess Club"]["participants"]
        assert new_email in data["Programming Class"]["participants"]


class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_missing_email_parameter(self, client):
        """Missing email parameter should return error."""
        response = client.post("/activities/Chess Club/signup")
        # FastAPI returns 422 for missing query parameter
        assert response.status_code == 422
    
    def test_activity_name_case_sensitive(self, client):
        """Activity names should be case-sensitive."""
        response = client.post(
            "/activities/chess club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
    
    def test_special_characters_in_email(self, client):
        """Email parameter accepts special characters (URL encoded)."""
        # Use import urllib for proper URL encoding of + in query params
        from urllib.parse import urlencode
        special_email = "test+special@mergington.edu"
        params = urlencode({"email": special_email})
        response = client.post(
            f"/activities/Chess Club/signup?{params}"
        )
        assert response.status_code == 200
        
        # Verify it was added
        response = client.get("/activities")
        data = response.json()
        assert special_email in data["Chess Club"]["participants"]
    
    def test_empty_email_parameter(self, client):
        """Empty email should still be accepted (no validation)."""
        response = client.post(
            "/activities/Chess Club/signup?email="
        )
        # API accepts empty string as no validation exists
        if response.status_code == 200:
            response = client.get("/activities")
            data = response.json()
            assert "" in data["Chess Club"]["participants"]
