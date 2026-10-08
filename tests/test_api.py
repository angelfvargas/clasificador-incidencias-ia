"""Pruebas de integración de la API con el modelo real y Mongo simulado."""
TICKET = {"asunto": "VPN not connecting",
          "descripcion": "Since this morning I cannot connect to the company VPN, it says authentication failed."}


def test_salud(cliente):
    r = cliente.get("/salud")
    assert r.status_code == 200 and r.json()["version_modelo"].startswith("v")


def test_registro_duplicado(cliente, operativo):
    r = cliente.post("/auth/registro", json={"nombre": "Ana", "email": "ANA@test.co", "clave": "clave12345"})
    assert r.status_code == 409


def test_registro_invalido(cliente):
    r = cliente.post("/auth/registro", json={"nombre": "A", "email": "no-es-correo", "clave": "123"})
    assert r.status_code == 422


def test_login_clave_mala(cliente, operativo):
    assert cliente.post("/auth/login", data={"username": "ana@test.co", "password": "mala"}).status_code == 401


def test_sin_token_no_entra(cliente):
    assert cliente.post("/tickets", json=TICKET).status_code == 401
    assert cliente.get("/tickets", headers={"Authorization": "Bearer basura"}).status_code == 401


def test_clasificar_no_guarda(cliente, operativo, base):
    r = cliente.post("/clasificar", json=TICKET, headers=operativo)
    assert r.status_code == 200
    p = r.json()["prediccion"]
    assert {"categoria", "prioridad", "equipo", "version_modelo"} <= p.keys()
    assert 0 <= p["categoria"]["puntaje"] <= 1
    assert base.tickets.count_documents({}) == 0


def test_descripcion_muy_corta(cliente, operativo):
    assert cliente.post("/tickets", json={"asunto": "x", "descripcion": "corta"}, headers=operativo).status_code == 422


def test_flujo_completo(cliente, operativo, admin):
    # 1. el usuario operativo crea el ticket y queda clasificado
    t = cliente.post("/tickets", json=TICKET, headers=operativo).json()
    assert t["estado"] == "abierto" and t["categoria"] and t["equipo"]
    assert t["ia"]["prediccion"]["version_modelo"].startswith("v")
    tid = t["id"]

    # 2. el operativo no puede cambiar estados
    assert cliente.patch(f"/tickets/{tid}/estado", json={"estado": "en_progreso"}, headers=operativo).status_code == 403

    # 3. el admin no puede saltarse estados
    assert cliente.patch(f"/tickets/{tid}/estado", json={"estado": "resuelto"}, headers=admin).status_code == 422

    # 4. reasigna, avanza y cierra
    r = cliente.patch(f"/tickets/{tid}/asignacion", json={"equipo": "IT Support"}, headers=admin)
    assert r.json()["reasignaciones"] == 1
    for e in ("en_progreso", "resuelto", "cerrado"):
        assert cliente.patch(f"/tickets/{tid}/estado", json={"estado": e}, headers=admin).status_code == 200

    final = cliente.get(f"/tickets/{tid}", headers=operativo).json()
    assert final["estado"] == "cerrado" and final["cerrado"]
    assert len(final["historial"]) == 5

    # 5. cerrado ya no se reasigna
    assert cliente.patch(f"/tickets/{tid}/asignacion", json={"equipo": "X Team"}, headers=admin).status_code == 422

    # 6. métricas
    m = cliente.get("/metricas", headers=admin).json()
    assert m["software"]["total_tickets"] == 1
    assert m["software"]["tasa_reasignacion"] == 1.0
    assert m["software"]["lead_time_horas_promedio"] is not None
    assert m["modelo"]["test"]["categoria"]["macro_f1"] > 0.5
    assert cliente.get("/metricas", headers=operativo).status_code == 403


def test_operativo_solo_ve_sus_tickets(cliente, operativo, admin):
    cliente.post("/tickets", json=TICKET, headers=admin)
    mio = cliente.post("/tickets", json=TICKET, headers=operativo).json()
    assert [t["id"] for t in cliente.get("/tickets", headers=operativo).json()] == [mio["id"]]
    assert len(cliente.get("/tickets", headers=admin).json()) == 2
    otro = cliente.get("/tickets", headers=admin).json()
    ajeno = next(t for t in otro if t["id"] != mio["id"])
    assert cliente.get(f"/tickets/{ajeno['id']}", headers=operativo).status_code == 403


def test_ticket_inexistente(cliente, admin):
    assert cliente.get("/tickets/no-es-un-id", headers=admin).status_code == 404
    assert cliente.get("/tickets/652f1c2b9b1e8a0000000000", headers=admin).status_code == 404


def test_cambio_de_rol(cliente, operativo, admin):
    assert cliente.patch("/usuarios/ana@test.co/rol", json={"rol": "analista"}, headers=admin).status_code == 200
    assert cliente.patch("/usuarios/ana@test.co/rol", json={"rol": "jefe"}, headers=admin).status_code == 422
    assert cliente.get("/usuarios", headers=operativo).status_code == 403
