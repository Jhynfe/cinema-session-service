def test_full_session_flow(client, auth_headers):
    host_headers = auth_headers(1)
    guest_headers = auth_headers(2)

    # 1. El host crea la sala
    create_resp = client.post(
        "/api/v1/sessions",
        json={"movie_id": 42, "title": "Noche de Ciencia Ficción"},
        headers=host_headers,
    )
    assert create_resp.status_code == 201
    session = create_resp.json()
    session_id = session["id"]
    assert session["host_id"] == 1
    assert session["participant_count"] == 1

    # 2. Un invitado se une
    join_resp = client.post(f"/api/v1/sessions/{session_id}/members", headers=guest_headers)
    assert join_resp.status_code == 201
    assert join_resp.json()["participant_count"] == 2

    # 3. Un invitado no puede controlar el playback
    forbidden_resp = client.patch(
        f"/api/v1/sessions/{session_id}/playback",
        json={"is_playing": True, "position_seconds": 10},
        headers=guest_headers,
    )
    assert forbidden_resp.status_code == 403

    # 4. El host sí puede
    playback_resp = client.patch(
        f"/api/v1/sessions/{session_id}/playback",
        json={"is_playing": True, "position_seconds": 30.5},
        headers=host_headers,
    )
    assert playback_resp.status_code == 200
    assert playback_resp.json()["status"] == "PLAYING"

    # 5. Listar miembros
    members_resp = client.get(f"/api/v1/sessions/{session_id}/members")
    assert members_resp.status_code == 200
    assert len(members_resp.json()) == 2

    # 6. El invitado sale
    leave_resp = client.delete(f"/api/v1/sessions/{session_id}/members/me", headers=guest_headers)
    assert leave_resp.status_code == 204

    # 7. El host termina la sesión
    end_resp = client.delete(f"/api/v1/sessions/{session_id}", headers=host_headers)
    assert end_resp.status_code == 204

    # 8. La sesión ya no existe
    get_resp = client.get(f"/api/v1/sessions/{session_id}")
    assert get_resp.status_code == 404
