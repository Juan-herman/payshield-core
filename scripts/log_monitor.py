"""
PayShield Core - Security Log Monitor & Incident Trigger
Objetivo: Parsear logs de telemetria, correlacionar eventos y disparar alertas defensivas ante anomalias.
"""

import sys
import re
from collections import defaultdict
from datetime import datetime

# Expresiones regulares para clasificar eventos forenses
PATTERN_404 = re.compile(r'\[SRC_IP:([\d\.]+)\] CONSULTA FALLIDA: Usuario \'(.*?)\' no existe')
PATTERN_LIMIT = re.compile(r'limiting requests, excess: .* client: ([\d\.]+), .* request: "(.*?)"')
PATTERN_UNAUTH = re.compile(r'172\.19\.0\.1 .* "(GET|POST) .* HTTP/.*" 401')

def parse_logs():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando analisis forense de telemetria...")
    
    ip_enum_attempts = defaultdict(list)
    ip_rate_violations = defaultdict(int)
    unauthorized_requests = 0

    # Lectura de flujo de entrada (stdin) proveniente de docker compose logs
    for line in sys.stdin:
        # Detectar barrido / enumeracion (404)
        m_404 = PATTERN_404.search(line)
        if m_404:
            src_ip, user = m_404.groups()
            ip_enum_attempts[src_ip].append(user)

        # Detectar activacion de Rate Limiting (429)
        m_limit = PATTERN_LIMIT.search(line)
        if m_limit:
            src_ip, path = m_limit.groups()
            ip_rate_violations[src_ip] += 1

        # Detectar consultas no autenticadas (401)
        if PATTERN_UNAUTH.search(line):
            unauthorized_requests += 1

    print("\n" + "="*60)
    print("           REPORTE AUTOMATIZADO DE AMENAZAS DETECTADAS")
    print("="*60)

    # Evaluacion de Vectores de Ataque
    threats_found = False

    # 1. Regla de Deteccion: Barrido de Cuentas (User Enumeration)
    for ip, users in ip_enum_attempts.items():
        if len(users) >= 3:
            threats_found = True
            print(f"[ALERTA CRITICA - MITRE T1087] Barrido de usuarios desde IP: {ip}")
            print(f"  -> Cuentas sondeadas ({len(users)}): {', '.join(users)}")

    # 2. Regla de Deteccion: Fuerza Bruta / Abuso de Tasa
    for ip, count in ip_rate_violations.items():
        if count > 0:
            threats_found = True
            print(f"[ALERTA MEDIA - T1110] Tasa de peticiones excedida desde IP: {ip}")
            print(f"  -> {count} solicitudes bloqueadas por politica HTTP 429")

    # 3. Regla de Deteccion: Peticiones No Autenticadas
    if unauthorized_requests > 0:
        threats_found = True
        print(f"[ALERTA BAJA - T1078] Peticiones no autenticadas rechazadas (HTTP 401): {unauthorized_requests}")

    if not threats_found:
        print("[INFO] No se registraron patrones anomalos ni umbrales excedidos.")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    parse_logs()
