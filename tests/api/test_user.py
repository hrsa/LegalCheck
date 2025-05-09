import pytest

from app.core.config import settings

@pytest.mark.asyncio(loop_scope="package")
async def test_ensures_fresh_db(fresh_db_session):
    pass


@pytest.mark.asyncio(loop_scope="package")
async def test_register_user(async_client):
    payload = {
        "email": "test@user.com",
        "password": "mysecurepassword123",
        "first_name": "Tester",
        "last_name": "De Test",
        "invite_code": "invitation"
    }
    response = await async_client.post(f"{settings.API_V1_STR}/register/", json=payload)
    assert response.status_code == 201, f"Unexpected status code: {response.status_code}"

    response_json = response.json()

    assert "id" in response_json, "Response missing user id"
    assert response_json["email"] == payload["email"]
    assert response_json["first_name"] == payload["first_name"]
    assert response_json["last_name"] == payload["last_name"]
    assert "password" not in response_json
    assert response_json["company_id"] == 1
    assert response_json["is_superuser"] == False
    assert response_json["is_active"] == True

@pytest.mark.asyncio(loop_scope="package")
async def test_login_user(async_client):

    correct_payload = {
        "username": "test@user.com",
        "password": "mysecurepassword123"
    }
    incorrect_payload = {
        "username": "test@user.com",
        "password": "wrongpassword"
    }

    response = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=incorrect_payload)
    assert response.status_code == 400, f"Unexpected status code: {response.status_code}"
    assert "detail" in response.json(), "Response missing error message"
    assert response.json()["detail"] == "LOGIN_BAD_CREDENTIALS"

    response = await async_client.post("/api/v1/auth/login", data=correct_payload)
    assert response.status_code == 204, f"Unexpected status code: {response.status_code}"
    assert "set-cookie" in response.headers, "Response missing cookies"
    assert "legalcheck_access_token=" in response.headers["set-cookie"], "Access token not found in cookies"

@pytest.mark.asyncio(loop_scope="package")
async def test_me_route(async_client):
    new_user_payload = {
        "email": "test2@user.com",
        "password": "test123",
        "first_name": "Second User",
        "last_name": "De Test",
        "invite_code": "invitation"
    }
    await async_client.post(f"{settings.API_V1_STR}/register/", json=new_user_payload)

    unauthorized_response = await async_client.get(f"{settings.API_V1_STR}/users/me", cookies=None)
    assert unauthorized_response.status_code == 401, f"Unexpected status code: {unauthorized_response.status_code}"
    assert "detail" in unauthorized_response.json(), "Response missing error message"
    assert unauthorized_response.json()["detail"] == "Unauthorized"

    await async_client.post(f"{settings.API_V1_STR}/auth/login",
                                    data={
                                        "username": new_user_payload["email"],
                                        "password": new_user_payload["password"]
                                    })
    response = await async_client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    assert "id" in response.json(), "Response missing user id"
    assert response.json()["id"] == 2
    assert response.json()["email"] == new_user_payload["email"]
    assert response.json()["first_name"] == new_user_payload["first_name"]
    assert response.json()["last_name"] == new_user_payload["last_name"]
    assert response.json()["company_id"] == 1
    assert response.json()["is_superuser"] == False

@pytest.mark.asyncio(loop_scope="package")
async def test_logout_user(async_client):
    response = await async_client.post(f"{settings.API_V1_STR}/auth/login",
                            data={
                                "username": "test2@user.com",
                                "password": "test123"
                            })

    assert response.status_code == 204, f"Unexpected status code: {response.status_code}"
    assert "set-cookie" in response.headers, "Response missing cookies"
    assert "legalcheck_access_token=" in response.headers["set-cookie"], "Access token not found in cookies"

    response = await async_client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    assert response.json()["email"] == "test2@user.com"

    response = await async_client.post(f"{settings.API_V1_STR}/auth/logout")
    assert response.status_code == 204, f"Unexpected status code: {response.status_code}"
    assert "set-cookie" in response.headers, "Response missing cookies"
    assert 'legalcheck_access_token=""' in response.headers["set-cookie"], "Access token found in cookies"

    unauthorized_response = await async_client.get(f"{settings.API_V1_STR}/users/me", cookies=None)
    assert unauthorized_response.status_code == 401, f"Unexpected status code: {unauthorized_response.status_code}"

