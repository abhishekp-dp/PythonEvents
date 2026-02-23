import pymysql
import requests
import json
import re

# ================= DB CONNECTION ================= #

try:
    connection = pymysql.connect(
        host="172.16.7.86",
        user="qa_write",
        passwd="cWFfd3JpdGVfcGFzc3dvcmQ=",
        db="dpws_qa_04"
    )
except Exception as e:
    print("❌ DB Connection failed:", e)
    exit(1)

cursor = connection.cursor()

# ================= CONSTANTS ================= #

API_URL = "http://172.16.4.112:10031/api/event"

STATION_TYPE = "11"
RESP_CODE = "11187"

# ================= FUNCTIONS ================= #

def get_station_id(drawer):
    row = drawer[0]
    number = int(drawer[1:])

    base = {
        "A": 0,
        "B": 10,
        "C": 20,
        "D": 30
    }

    if row not in base:
        raise Exception("Invalid drawer")

    return base[row] + number


def get_electronics_location(drawer, slot_number):
    if slot_number < 1 or slot_number > 8:
        raise Exception("Slot number must be between 1 and 8")

    drawer_number = int(drawer[1:])

    # ODD drawer
    if drawer_number % 2 != 0:
        return 8 - slot_number

    # EVEN drawer
    return slot_number - 1


def hit_event_api(station_id, electronics_location, value):
    args_payload = {
        "station_type": STATION_TYPE,
        "station_id": str(station_id),
        "resp_code": RESP_CODE,
        "data": {
            str(electronics_location): str(value)
        }
    }

    print("\nEvent payload sent to backend:")
    print(json.dumps(args_payload, indent=2))

    response = requests.get(
        API_URL,
        params={"args": json.dumps(args_payload)},
        timeout=10
    )

    if response.status_code != 200:
        raise Exception(f"API Error [{response.status_code}]: {response.text}")

    return response.text


# ================= MAIN FLOW (EMPTY LOCATION) ================= #

try:
    while True:
        drawer_input = input("Enter Drawer & Slot to EMPTY (e.g. A10-5): ")

        match = re.match(r"([A-D]\d+)\s*-\s*(\d)", drawer_input)
        if not match:
            raise Exception("Invalid input format. Use A10-5")

        drawer, slot = match.groups()
        slot = int(slot)

        station_id = get_station_id(drawer)
        electronics_location = get_electronics_location(drawer, slot)

        print("\nResolved values:")
        print("Drawer           :", drawer)
        print("Slot (Human)     :", slot)
        print("Station ID       :", station_id)
        print("Electronics Loc  :", electronics_location)

        print("\nTriggering EEPROM REMOVE event...")
        response = hit_event_api(station_id, electronics_location, "0")

        print("\n✅ Location emptied successfully")
        print("API Response:", response)

except Exception as e:
    print("❌ Error:", e)

finally:
    cursor.close()
    connection.close()