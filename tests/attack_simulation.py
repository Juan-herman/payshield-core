"""
PayShield Core - Security Validation & Attack Simulation Suite
Objetivo: Generar patrones de ataque conocidos para evaluar telemetria y respuesta defensiva.
"""

import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://localhost"

def log_test(name, status, details):
    print(f"[*] {name.upper()}: [{status}] - {details}")

def test_user_enumeration():
    """Vector 1: Reconocimiento y Enumeracion de Usuarios (T1087 - MITRE ATT&CK)"""
    print("\n--- Iniciando Vector 1: Enumeracion de Usuarios ---")
    targets = ["admin", "root", "usuario_demo", "tesoreria", "soporte", "comercio_central"]
    for user in targets:
        url = f"{BASE_URL}/api/v1/balance/{user}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                log_test("Enumeracion", "HIT 200", f"Usuario expuesto: '{user}' | Saldo: ${data.get('balance')}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                log_test("Enumeracion", "MISS 404", f"Usuario inexistente: '{user}'")
            else:
                log_test("Enumeracion", f"ERR {e.code}", f"Respuesta inesperada para '{user}'")
        time.sleep(0.1)

def test_negative_amount_injection():
    """Vector 2: Manipulacion de Logica de Negocio - Montos Negativos"""
    print("\n--- Iniciando Vector 2: Inyeccion de Monto Invalido / Negativo ---")
    url = f"{BASE_URL}/api/v1/transfer"
    payload = json.dumps({
        "sender": "usuario_demo",
        "receiver": "comercio_central",
        "amount": -5000.00
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            log_test("Manipulacion", "FALLA CRITICA", "La API permitio un monto negativo")
    except urllib.error.HTTPError as e:
        if e.code == 422:
            log_test("Manipulacion", "BLOQUEADO 422", "Pydantic rechazo el esquema con monto negativo")
        else:
            log_test("Manipulacion", f"HTTP {e.code}", "Rechazado por control de servidor")

def test_overdraft_abuse():
    """Vector 3: Abuso de Saldo / Intento de Descubierto"""
    print("\n--- Iniciando Vector 3: Transferencia Excediendo Saldo Disponible ---")
    url = f"{BASE_URL}/api/v1/transfer"
    payload = json.dumps({
        "sender": "usuario_demo",
        "receiver": "comercio_central",
        "amount": 99999999.00
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            log_test("Sobregiro", "FALLA CRITICA", "Se transfirieron fondos inexistentes")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            log_test("Sobregiro", "BLOQUEADO 400", "Control logico de saldo rechazo la transaccion")
        else:
            log_test("Sobregiro", f"HTTP {e.code}", "Rechazado con otro codigo de error")

def test_endpoint_scanning():
    """Vector 4: Escaneo de Rutas Ocultas / Reconocimiento Web"""
    print("\n--- Iniciando Vector 4: Reconocimiento de Endpoints No Publicos ---")
    probes = ["/admin", "/wp-login.php", "/.env", "/metrics", "/api/v1/debug"]
    for path in probes:
        url = f"{BASE_URL}{path}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                log_test("Reconocimiento", f"EXPUESTO {resp.status}", f"Ruta accesible: {path}")
        except urllib.error.HTTPError as e:
            log_test("Reconocimiento", f"FILTRADO {e.code}", f"Ruta denegada o inexistente: {path}")
        time.sleep(0.05)

if __name__ == "__main__":
    print("=== EJECUTANDO BATERIA DE PRUEBAS DE SEGURIDAD EN PAYSHIELD CORE ===")
    test_user_enumeration()
    test_negative_amount_injection()
    test_overdraft_abuse()
    test_endpoint_scanning()
    print("\n[+] Bateria de pruebas finalizada. Logs listos para analisis forense.")
