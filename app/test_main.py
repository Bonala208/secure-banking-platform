from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import pytest
from main import app

client = TestClient(app)

def test_health_check():
    """Verify that the health check endpoint returns 200 OK for ALB."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "HEALTHY", "service": "banking-api"}

@patch("main.get_db")
def test_get_balance_success(mock_get_db):
    """Test retrieving balance for an existing account."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    mock_cur.fetchone.return_value = {
        "id": 1,
        "account_number": "ACC-1001",
        "holder_name": "Praveen Bonala",
        "balance": 1000.00
    }

    response = client.get("/accounts/1/balance")
    assert response.status_code == 200
    data = response.json()
    assert data["account_number"] == "ACC-1001"
    assert data["balance"] == 1000.00

@patch("main.get_db")
def test_get_balance_not_found(mock_get_db):
    """Test retrieving balance for a non-existent account returns 404."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchone.return_value = None

    response = client.get("/accounts/999/balance")
    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"

@patch("main.get_db")
def test_deposit_success(mock_get_db):
    """Test depositing money successfully updates the account."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    mock_cur.fetchone.return_value = {
        "id": 1,
        "account_number": "ACC-1001",
        "balance": 1250.00
    }

    response = client.post("/accounts/1/deposit", json={"amount": 250.00})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Deposit successful"
    assert data["new_balance"] == 1250.00

def test_deposit_negative_amount_fails():
    """Test that depositing negative or zero amount is rejected by validation."""
    response = client.post("/accounts/1/deposit", json={"amount": -50.00})
    assert response.status_code == 422 # Unprocessable Entity (Pydantic validation)

@patch("main.get_db")
def test_withdraw_success(mock_get_db):
    """Test withdrawing money when balance is sufficient."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    # First query fetches current balance (1000)
    # Second query returns updated row (750)
    mock_cur.fetchone.side_effect = [
        {"balance": 1000.00},
        {"id": 1, "account_number": "ACC-1001", "balance": 750.00}
    ]

    response = client.post("/accounts/1/withdraw", json={"amount": 250.00})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Withdrawal successful"
    assert data["new_balance"] == 750.00

@patch("main.get_db")
def test_withdraw_insufficient_funds(mock_get_db):
    """Test withdrawal fails with 400 when amount exceeds balance."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchone.return_value = {"balance": 100.00}

    response = client.post("/accounts/1/withdraw", json={"amount": 500.00})
    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]
