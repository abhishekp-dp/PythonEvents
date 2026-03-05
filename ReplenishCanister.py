import pymysql
import requests
import sys

# ================= CONFIGURATION ================= #

DB_CONFIG = {
    "host": "172.16.7.86",
    "user": "qa_write",
    "passwd": "cWFfd3JpdGVfcGFzc3dvcmQ=",
    "db": "dpws_qa_04"
}

LOGIN_URL = "https://qa-auth.dosepack.com/api/login"
API_URL = "https://qa-ws.dosepack.com/canisterreplenish"
STORE_USRE_ACTION = "http://172.16.4.112:10031/api/store_user_action"

USERNAME = "nancyr@pcp"          # <-- put inside quotes
PASSWORD = "SGVsbG9AMTIz"       # <-- put inside quotes
CLIENT_ID = "dp-web-app"
SCOPE = "dp-full-scope"
RESPONSE_TYPE = "token"
STATE = "zPnjejysaOjniTFwOXKo"

# ================= TOKEN MANAGEMENT ================= #

def get_new_token():
    print("🔐 Fetching new token...")

    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "client_id":CLIENT_ID,
        "scope":SCOPE,
        "response_type":RESPONSE_TYPE,
        "state":STATE
    }

    response = requests.post(
        LOGIN_URL,
        data=payload,  # <-- IMPORTANT
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        print("❌ Login failed:", response.text)
        sys.exit()

    response_json = response.json()

    if response_json.get("status") != "success":
        print("❌ Login unsuccessful:", response.text)
        sys.exit()

    token = response_json["data"]["access_token"]
    expires_at = response_json["data"]["expires_at"]

    print("✅ Token acquired")
    print("🕒 Expires at:", expires_at)

    return token


# ================= DATABASE FUNCTION ================= #

def get_ndc_from_db(canister_id):
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = """
        SELECT dm.ndc 
        FROM canister_master c
        JOIN drug_master dm ON c.drug_id_id = dm.id
        WHERE c.id = %s
        """

        cursor.execute(query, (canister_id,))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if not result:
            print("❌ No NDC found for given canister ID")
            sys.exit()

        return result[0]

    except Exception as e:
        print("❌ DB Error:", e)
        sys.exit()


# ================= API CALL WITH AUTO REFRESH ================= #

import json

def hit_replenish_api(payload, token):

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    form_data = {
        "args": json.dumps(payload)   # 🔥 IMPORTANT
    }

    response = requests.post(
        API_URL,
        headers=headers,
        data=form_data
    )

    # Auto refresh if expired
    if response.status_code == 401:
        print("⚠ Token expired. Refreshing...")
        token = get_new_token()

        headers["Authorization"] = f"Bearer {token}"

        response = requests.post(
            API_URL,
            headers=headers,
            data=form_data
        )

    return response


def hit_store_user_action(canister_id,token):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "action": 2,
        "canister_id": canister_id,
        "module": 30
    }

    response = requests.get(
        STORE_USRE_ACTION,
        headers=headers,
        params=params
    )
    print("\n--- Store User Action API ---")
    print("Status:", response.status_code)
    print("Response:", response.text)

    return response


# ================= MAIN ================= #

def main():

    canister_id = int(input("Enter Canister ID: "))
    filled_quantity = int(input("Enter Filled Quantity: "))

    # Fetch NDC
    scanned_ndc = get_ndc_from_db(canister_id)

    # Build payload
    payload = {
        "canister_id": canister_id,
        "available_quantity": 0,
        "filled_quantity": filled_quantity,
        "user_id": 306,
        "company_id": 4,
        "max_canister_capacity": 331,
        "module_id": 51,
        "robot_device_id": 100,
        "request_origin": "Robot Utility",
        "device_id": 100,
        "replenishment_mode": 81,
        "replenish_data": [
            {
                "scanned_ndc": scanned_ndc,
                "lot_number": "B2505094",
                "expiration_date": "04-2027",
                "drug_scan_type": 77,
                "replenish_qty": filled_quantity
            }
        ]
    }


    # Get token
    token = get_new_token()

    # Call API
    response = hit_replenish_api(payload, token)

    resp = hit_store_user_action(canister_id,token)

    print("\n=========== RESPONSE ===========")
    print("Status Code:", response.status_code)
    print("Response:", response.text)


if __name__ == "__main__":
    main()