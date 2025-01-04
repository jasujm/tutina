import fastapi
import jwt

from tutina.app.app import app

ENDPOINT = "/auth/endpoint"


@app.get(ENDPOINT)
def get_endpoint():
    return {}


def test_auth_success(client, auth_token):
    response = client.get(ENDPOINT, headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == fastapi.status.HTTP_200_OK


def test_auth_incorrect_type(client):
    response = client.get(
        ENDPOINT, headers={"Authorization": "Basic dXNlcjpwYXNzd29yZA=="}
    )
    assert response.status_code == fastapi.status.HTTP_403_FORBIDDEN


def test_auth_invalid_token(client):
    invalid_token = jwt.encode({}, "wrong-secret", algorithm="HS256")
    response = client.get(
        ENDPOINT, headers={"Authorization": f"Bearer {invalid_token}"}
    )
    assert response.status_code == fastapi.status.HTTP_401_UNAUTHORIZED
