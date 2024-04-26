import pytest
import requests

# Base URL of your Flask application
BASE_URL = "http://localhost:1204"

def test_unauthenticated_access_to_protected_route():
    """ Test access to a protected route without authentication """
    response = requests.get(f"{BASE_URL}/home")
    assert response.status_code == 401, "Unauthorized access allowed to home"

def test_login_with_wrong_credentials():
    """ Test login with incorrect credentials """
    wrong_credentials = {
        "w": "x",
        "w": "x"
    }
    response = requests.post(f"{BASE_URL}/login/user", json=wrong_credentials)
    assert response.status_code == 401, "Logged in with incorrect credentials"

def test_successful_login():
    """ Test login with correct credentials """
    correct_credentials = {
        "w": "w",  
        "w": "w" 
    }
    response = requests.post(f"{BASE_URL}/login/user", json=correct_credentials)
    assert response.status_code == 200, "Failed to login with correct credentials"
    assert 'login' in response.json() and response.json()['login'] == True, "Login not successful"
