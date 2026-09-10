from faker import Faker
from datetime import timezone
import random
import json

fake = Faker()

LIFECYCLE_STAGES = [
    "lead",
    "mql",
    "sql",
    "customer"
]


with open("sources/companies.json", "r", encoding="utf-8") as f:
    companies = json.load(f)


def generate_contact(contact_number, company):
    created_at = fake.date_time_between(
        start_date="-5y",
        end_date="now",
        tzinfo=timezone.utc
    )

    updated_at = fake.date_time_between(
        start_date=created_at,
        end_date="now",
        tzinfo=timezone.utc
    )

    return {
        "contact_id": f"P-{contact_number:07d}",

        "company_id": company["company_id"],

        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "job_title": fake.job(),

        "lifecycle_stage": random.choice(LIFECYCLE_STAGES),

        "bu_id": company["bu_id"],

        "is_deleted": 1 if random.random() < 0.03 else 0,
        "created_at": created_at.isoformat(),
        "updated_at": updated_at.isoformat()
    }


contacts = []
contact_number = 1

for company in companies:
    for _ in range(3):
        contacts.append(
            generate_contact(contact_number, company)
        )

    contact_number += 1


with open("sources/contacts.json", "w", encoding="utf-8") as f:
    json.dump(
        contacts,
        f,
        indent=2,
        ensure_ascii=False
    )
