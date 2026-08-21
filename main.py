from ics import Calendar, Event
from pathlib import Path
import requests

session = requests.Session()


def send_post(url, payload, headers=None):
    r = session.post(url, json=payload, headers=headers)
    return r.json()


def send_get(url, params=None):
    r = session.get(url, params=params)

    print("GET URL:", r.url)
    print("Status:", r.status_code)
    print("Content-Type:", r.headers.get("content-type"))
    print("First 500 chars:")
    print(r.text[:500])

    return r.json()


def signin(email: str, password: str):
    login_payload = {"email": email, "password": password}

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://learn.zybooks.com",
        "user-agent": "Mozilla/5.0",
    }

    login_data = send_post(
        "https://zyserver.zybooks.com/v1/signin",
        login_payload,
        headers=headers,
    )

    if not login_data.get("success"):
        print("Login failed")
        print(login_data)
        return None

    auth_token = login_data["session"]["auth_token"]
    session.headers.update({"Authorization": f"Bearer {auth_token}"})

    print("Login Success")
    return auth_token


def build_ical(email: str, password: str):
    auth_token = signin(email, password)

    if auth_token is None:
        return

    calendar = Calendar()
    event_count = 0

    zybook_codes = [
        "ASUCHE211TaylorFall2026"
    ]

    for zybook_code in zybook_codes:
        course_number = zybook_code

        class_assignments_url = f"https://zyserver.zybooks.com/v1/zybook/{zybook_code}/assignments"

        class_assignments_data = send_get(class_assignments_url)

        if not class_assignments_data.get("success", True):
            print("Could not fetch assignments.")
            print(class_assignments_data)
            continue

        print(f"## START {zybook_code} ##")

        for assignment in class_assignments_data["assignments"]:
            assignment_name = assignment["title"]
            due_date = assignment["due_dates"][0]["date"]

            total_points = 0
            sections = ""

            for section in assignment["sections"]:
                total_points += section["total_points"]
                sections += f"{section['chapter_number']}.{section['section_number']} - {section['title']}\n"

            event = Event()
            event.name = f"{course_number} - {assignment_name}"
            event.begin = due_date
            event.description = f"Total Points: {total_points}\nSections:\n----\n{sections}----"
            event.url = f"https://learn.zybooks.com/zybook/{zybook_code}?selectedPanel=assignments-panel"

            calendar.events.add(event)
            event_count += 1

        print(f"## END {zybook_code} ##")

    output_path = Path(__file__).resolve().parent / "ZyBooks.ics"
    with output_path.open("w", encoding="utf-8") as f:
        f.writelines(calendar.serialize_iter())

    print(f"Wrote {event_count} events to {output_path}")


import os

if __name__ == "__main__":
    build_ical(
        email=os.environ["ZYBOOKS_EMAIL"],
        password=os.environ["ZYBOOKS_PASSWORD"],
    )