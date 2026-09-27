import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from contextlib import asynccontextmanager

# Database connection details from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "banking_db")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db():
    """Helper to establish a PostgreSQL connection."""
    return psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME,
        port=DB_PORT,
        cursor_factory=RealDictCursor,
        connect_timeout=5
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes tables and seeds initial account on startup."""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id SERIAL PRIMARY KEY,
                    account_number VARCHAR(50) UNIQUE NOT NULL,
                    holder_name VARCHAR(100) NOT NULL,
                    balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00
                );
                INSERT INTO accounts (id, account_number, holder_name, balance)
                VALUES (1, 'ACC-1001', 'Praveen Bonala', 1000.00)
                ON CONFLICT (id) DO UPDATE SET holder_name = EXCLUDED.holder_name;
            """)
            conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database connection deferred or pending: {e}")
    yield

app = FastAPI(
    title="Core Banking REST API",
    description="Secure, resilient REST API performing CRUD banking operations.",
    version="1.0.0",
    lifespan=lifespan
)

# Request payload validation schema
class AmountPayload(BaseModel):
    amount: float = Field(..., gt=0, description="Transaction amount must be strictly positive")

# Root endpoint with welcome information
@app.get("/")
def root():
    return {
        "message": "Welcome to the Core Banking REST API",
        "documentation": "/docs",
        "health_check": "/health"
    }

# 0. Health check endpoint for AWS Load Balancer target group
@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    return {"status": "HEALTHY", "service": "banking-api"}

# 1. REQUIRED: GET endpoint to get current balance of an account
@app.get("/accounts/{account_id}/balance")
def get_balance(account_id: int):
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT id, account_number, holder_name, balance FROM accounts WHERE id = %s", (account_id,))
            account = cur.fetchone()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {
        "id": account["id"],
        "account_number": account["account_number"],
        "holder_name": account["holder_name"],
        "balance": float(account["balance"])
    }

# 2. REQUIRED: POST endpoint to deposit money to an account
@app.post("/accounts/{account_id}/deposit")
def deposit(account_id: int, payload: AmountPayload):
    try:
        conn = get_db()
        with conn.cursor() as cur:
            # Atomic update using row-level locking
            cur.execute("""
                UPDATE accounts 
                SET balance = balance + %s 
                WHERE id = %s 
                RETURNING id, account_number, balance;
            """, (payload.amount, account_id))
            updated = cur.fetchone()
            conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not updated:
        raise HTTPException(status_code=404, detail="Account not found")

    return {
        "message": "Deposit successful",
        "account_id": updated["id"],
        "account_number": updated["account_number"],
        "new_balance": float(updated["balance"])
    }

# 3. REQUIRED: POST endpoint to withdraw money from an account
@app.post("/accounts/{account_id}/withdraw")
def withdraw(account_id: int, payload: AmountPayload):
    try:
        conn = get_db()
        with conn.cursor() as cur:
            # Lock the row for update to prevent concurrent race condition updates
            cur.execute("SELECT balance FROM accounts WHERE id = %s FOR UPDATE", (account_id,))
            account = cur.fetchone()

            if not account:
                conn.close()
                raise HTTPException(status_code=404, detail="Account not found")

            current_balance = float(account["balance"])
            if current_balance < payload.amount:
                conn.close()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient funds. Current balance: {current_balance}, Requested: {payload.amount}"
                )

            # Deduct balance
            cur.execute("""
                UPDATE accounts 
                SET balance = balance - %s 
                WHERE id = %s 
                RETURNING id, account_number, balance;
            """, (payload.amount, account_id))
            updated = cur.fetchone()
            conn.commit()
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "message": "Withdrawal successful",
        "account_id": updated["id"],
        "account_number": updated["account_number"],
        "new_balance": float(updated["balance"])
    }
