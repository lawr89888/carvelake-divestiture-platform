from faker import Faker
from datetime import timezone
import random

fake = Faker()

BU_IDS = [
    "bu_01",
    "bu_02",
    "bu_03",
    "bu_04",
    "bu_05",
    "bu_06"
]

BUSINESS_GROUPS = [
    "bg_direct",
    "bg_partner",
    "bg_online"
]


def generate_company(company_number, bu_id):
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
        "company_id": f"C-{company_number:07d}",
        "name": fake.company(),
        "domain": fake.domain_name(),
        "industry": random.choice([
            "Technology",
            "Financial Services",
            "Healthcare",
            "Retail",
            "Manufacturing",
            "Telecommunications"
        ]),
        "country": fake.country(),
        "employee_count": random.randint(10, 50_000),
        "annual_revenue": round(random.uniform(100_000, 500_000_000), 2),
        "owner_rep": fake.name(),
        "is_active": random.random() < 0.90,
        "business_group": random.choice(BUSINESS_GROUPS),

        "bu_id": bu_id,

        "is_deleted": 1 if random.random() < 0.03 else 0,
        "created_at": created_at.isoformat(),
        "updated_at": updated_at.isoformat()
    }


companies = []

company_number = 1

for bu_id in BU_IDS:
    for _ in range(40):
        companies.append(
            generate_company(company_number, bu_id)
        )
        company_number += 1

import json

with open("sources/companies.json", "w", encoding="utf-8") as f:
    json.dump(companies, f, indent=2, ensure_ascii=False)

