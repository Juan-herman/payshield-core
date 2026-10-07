import logging
import os
import psycopg2
from fastapi import FastAPI, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# TELEMETRÍA Y LOGGING ESTRUCTURADO PARA AUDITORÍA FORENSE
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [SRC_IP:%(client_ip)s] %(message)s'
)
logger = logging.getLogger("payshield")

app = FastAPI(title="PayShield Core API", version="1.0.0")

# Esquema de autenticación interna
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
VALID_API_KEY = os.getenv("INTERNAL_API_KEY", "PayShieldSecretKey2026!")

def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial invalida o ausente"
        )
    return api_key

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("POSTGRES_DB", "payshield_db"),
        user=os.getenv("POSTGRES_USER", "payshield_admin"),
        password=os.getenv("POSTGRES_PASSWORD", "SuperSecureFintechPass2026!"),
        port=os.getenv("DB_PORT", "5432")
    )

class TransferRequest(BaseModel):
    sender: str = Field(..., min_length=3, max_length=50)
    receiver: str = Field(..., min_length=3, max_length=50)
    amount: float = Field(..., gt=0)

@app.get("/health")
def health_check():
    return {"status": "operational", "service": "payshield-core"}

@app.get("/api/v1/balance/{username}")
def get_balance(username: str, request: Request, api_key: str = Security(verify_api_key)):
    client_ip = request.headers.get("x-real-ip", request.client.host)
    extra = {"client_ip": client_ip}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE username = %s;", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        logger.warning(f"CONSULTA FALLIDA: Usuario '{username}' no existe", extra=extra)
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    logger.info(f"CONSULTA EXITOSA: Saldo consultado para '{username}'", extra=extra)
    return {"username": username, "balance": float(row[0])}

@app.post("/api/v1/transfer")
def make_transfer(transfer: TransferRequest, request: Request, api_key: str = Security(verify_api_key)):
    client_ip = request.headers.get("x-real-ip", request.client.host)
    extra = {"client_ip": client_ip}

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, balance FROM accounts WHERE username = %s FOR UPDATE;", (transfer.sender,))
        sender_data = cursor.fetchone()

        cursor.execute("SELECT id FROM accounts WHERE username = %s FOR UPDATE;", (transfer.receiver,))
        receiver_data = cursor.fetchone()

        if not sender_data or not receiver_data:
            logger.warning("TRANSFERENCIA RECHAZADA: Cuentas invalidas", extra=extra)
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")

        sender_id, balance = sender_data[0], float(sender_data[1])
        receiver_id = receiver_data[0]

        if balance < transfer.amount:
            logger.warning(f"TRANSFERENCIA RECHAZADA: Fondos insuficientes en '{transfer.sender}'", extra=extra)
            raise HTTPException(status_code=400, detail="Fondos insuficientes")

        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s;", (transfer.amount, sender_id))
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s;", (transfer.amount, receiver_id))

        cursor.execute(
            "INSERT INTO transactions (sender_id, receiver_id, amount, status) VALUES (%s, %s, %s, %s);",
            (sender_id, receiver_id, transfer.amount, "SUCCESS")
        )

        conn.commit()
        logger.info(f"TRANSACCION APROBADA: '{transfer.sender}' -> '{transfer.receiver}' por ${transfer.amount}", extra=extra)
        return {
            "status": "success",
            "sender": transfer.sender,
            "receiver": transfer.receiver,
            "amount": transfer.amount
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"ERROR CRITICO EN TRANSACCION: {str(e)}", extra=extra)
        raise HTTPException(status_code=500, detail="Error interno")
    finally:
        cursor.close()
        conn.close()
