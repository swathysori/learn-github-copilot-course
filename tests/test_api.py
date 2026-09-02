"""Comprehensive test suite for the Mergington High School API

Tests cover all endpoints: GET /activities, POST /signup, and DELETE /unregister
"""

from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


# ============================================================================
# GET /activities Tests
# ============================================================================

def test_get_activities_returns_all_activities():
    """Test that GET /activities returns all activities"""
    response = client.get("/activities")
    
    assert response.status_code == 200
    activities = response.json()
    
    # Verify we have all 9 activities
    assert len(activities) == 9
    assert "Chess Club" in activities
    assert "Programming Class" in activities
    assert "Gym Class" in activities
    assert "Basketball Team" in activities
    assert "Tennis Club" in activities
    assert "Art Studio" in activities
    assert "Drama Club" in activities
    assert "Debate Team" in activities
    assert "Science Club" in activities


def test_get_activities_returns_correct_structure():
    """Test that each activity has the required fields"""
    response = client.get("/activities")
    activities = response.json()
    
    # Check structure of Chess Club as an example
    chess_club = activities["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    
    # Verify types
    assert isinstance(chess_club["description"], str)
    assert isinstance(chess_club["schedule"], str)
    assert isinstance(chess_club["max_participants"], int)
    assert isinstance(chess_club["participants"], list)


# ============================================================================
# POST /activities/{activity_name}/signup Tests
# ============================================================================

def test_signup_successful():
    """Test successful signup to an activity"""
    response = client.post(
        "/activities/Science Club/signup",
        params={"email": "newstudent@mergington.edu"}
    )
    
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]
    assert "newstudent@mergington.edu" in response.json()["message"]
    
    # Verify student was actually added
    activities = client.get("/activities").json()
    assert "newstudent@mergington.edu" in activities["Science Club"]["participants"]


def test_signup_duplicate_email_returns_400():
    """Test that duplicate email signup returns 400 error"""
    # Michael is already signed up for Chess Club
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_invalid_activity_returns_404():
    """Test that signup for non-existent activity returns 404"""
    response = client.post(
        "/activities/Non-Existent Activity/signup",
        params={"email": "student@mergington.edu"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_at_capacity_returns_400():
    """Test that signup fails when activity is at full capacity"""
    # First, fill up an activity (use one with small capacity)
    # Get current participants
    activities = client.get("/activities").json()
    capacity_test_activity = "Tennis Club"
    current_participants = activities[capacity_test_activity]["participants"]
    max_participants = activities[capacity_test_activity]["max_participants"]
    
    # Fill up the activity if not already full
    spots_needed = max_participants - len(current_participants)
    for i in range(spots_needed):
        email = f"filler{i}@mergington.edu"
        response = client.post(
            f"/activities/{capacity_test_activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Now try to sign up when at capacity
    response = client.post(
        f"/activities/{capacity_test_activity}/signup",
        params={"email": "overcapacity@mergington.edu"}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is at full capacity"


def test_signup_missing_email_parameter_returns_422():
    """Test that missing email parameter returns validation error"""
    response = client.post("/activities/Chess Club/signup")
    
    assert response.status_code == 422  # FastAPI validation error


# ============================================================================
# DELETE /activities/{activity_name}/participants/{email} Tests
# ============================================================================

def test_unregister_participant_removes_email_from_activity():
    """Test that unregister removes participant from activity"""
    # First, sign someone up
    signup_response = client.post(
        "/activities/Art Studio/signup",
        params={"email": "artist@mergington.edu"}
    )
    assert signup_response.status_code == 200
    
    # Verify they were added
    activities = client.get("/activities").json()
    assert "artist@mergington.edu" in activities["Art Studio"]["participants"]
    
    # Now unregister
    response = client.delete(
        "/activities/Art Studio/participants/artist@mergington.edu"
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Unregistered artist@mergington.edu from Art Studio"
    
    # Verify they were removed
    activities = client.get("/activities").json()
    assert "artist@mergington.edu" not in activities["Art Studio"]["participants"]


def test_unregister_from_invalid_activity_returns_404():
    """Test that unregister from non-existent activity returns 404"""
    response = client.delete(
        "/activities/Non-Existent Activity/participants/student@mergington.edu"
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_non_existent_participant_returns_404():
    """Test that unregister of non-existent participant returns 404"""
    response = client.delete(
        "/activities/Chess Club/participants/notamember@mergington.edu"
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_unregister_already_unregistered_participant_returns_404():
    """Test that unregistering an already-removed participant returns 404"""
    # Sign up and unregister
    email = "temporarystudent@mergington.edu"
    
    signup_response = client.post(
        "/activities/Drama Club/signup",
        params={"email": email}
    )
    assert signup_response.status_code == 200
    
    unregister1 = client.delete(
        f"/activities/Drama Club/participants/{email}"
    )
    assert unregister1.status_code == 200
    
    # Try to unregister again
    unregister2 = client.delete(
        f"/activities/Drama Club/participants/{email}"
    )
    assert unregister2.status_code == 404
    assert unregister2.json()["detail"] == "Participant not found"


# ============================================================================
# Integration Tests
# ============================================================================

def test_signup_and_unregister_flow():
    """Test complete flow: signup followed by unregister"""
    email = "integration@mergington.edu"
    activity = "Debate Team"
    
    # Sign up
    signup = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    assert signup.status_code == 200
    
    # Verify in participants
    activities = client.get("/activities").json()
    assert email in activities[activity]["participants"]
    
    # Unregister
    unregister = client.delete(
        f"/activities/{activity}/participants/{email}"
    )
    assert unregister.status_code == 200
    
    # Verify removed from participants
    activities = client.get("/activities").json()
    assert email not in activities[activity]["participants"]


def test_signup_multiple_activities():
    """Test that a student can signup for multiple activities"""
    email = "multiactivity@mergington.edu"
    activities_to_join = ["Chess Club", "Programming Class", "Science Club"]
    
    for activity in activities_to_join:
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Verify student is in all activities
    activities = client.get("/activities").json()
    for activity in activities_to_join:
        assert email in activities[activity]["participants"]
