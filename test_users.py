def test_empty(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert response.json() == []

def test_createuser(client, user_factory):
    created = user_factory("Alice", "alice@example.com")
    assert created["id"] == 1
    assert created["name"] == "Alice"
    assert created["email"] == "alice@example.com"
    list_response = client.get("/users")
    assert list_response.status_code == 200
    users = list_response.json()
    assert isinstance(users, list)
    assert len(users) == 1
    assert users[0]["name"] == "Alice"
    assert users[0]["email"] == "alice@example.com"

def test_duplicateemail(client, user_factory):
    user_factory("Bob", "bob@example.com")
    second = client.post("/users", json={"name": "Bob", "email": "bob@example.com"})
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already exists"

def test_deleteuser(client, user_factory):
    created = user_factory("Charlie", "charlie@example.com")
    user_id = created["id"]
    delete_response = client.delete(f"/users/{user_id}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    missing_response = client.delete(f"/users/{user_id}")
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "User not found"

def test_createuser_commitfailure(monkeypatch, client, session_maker):
    from main import get_db
    calls = {}
    def override_get_db():
        db = session_maker()
        original_commit = db.commit
        def failing_commit():
            calls["commit"] = True
            raise RuntimeError("Simulated commit failure")
        monkeypatch.setattr(db, "commit", failing_commit)
        try:
            yield db
        finally:
            monkeypatch.setattr(db, "commit", original_commit)
            db.close()
    client.app.dependency_overrides[get_db] = override_get_db
    response = client.post("/users", json={"name": "Dana", "email": "dana@example.com"})
    assert response.status_code == 500
    assert calls.get("commit") is True
    client.app.dependency_overrides.pop(get_db, None)