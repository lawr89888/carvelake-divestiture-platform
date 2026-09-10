from faker import Faker
from datetime import timezone
import random
import json

fake = Faker()

STAGES = [
    "prospect",
    "qualified",
    "proposal",
    "won",
    "lost"
]

CURRENCIES = [
    "USD",
    "EUR",
    "GBP"
]


with open("sources/companies.json", "r", encoding="utf-8") as f:
    companies = json.load(f)


def generate_deal(deal_number, company):
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

    stage = random.choice(STAGES)

    if stage == "won":
        probability = 100

    elif stage == "lost":
        probability = 0

    elif stage == "proposal":
        probability = random.randint(60, 90)

    elif stage == "qualified":
        probability = random.randint(30, 70)

    else:
        probability = random.randint(5, 40)


    if stage in ["won", "lost"]:
        close_date = fake.date_time_between(
            start_date=created_at,
            end_date="now",
            tzinfo=timezone.utc
        )

    else:
        close_date = fake.date_time_between(
            start_date="+1d",
            end_date="+1y",
            tzinfo=timezone.utc
        )


    return {
        "deal_id": f"D-{deal_number:07d}",

        "company_id": company["company_id"],

        "name": f"{company['name']} Deal",

        "amount": round(
            random.uniform(5_000, 2_000_000),
            2
        ),

        "currency": random.choice(CURRENCIES),

        "stage": stage,

        "probability": probability,

        "close_date": close_date.isoformat(),

        "owner_rep": fake.name(),

        "business_group": company["business_group"],

        "bu_id": company["bu_id"],

        "is_deleted": 1 if random.random() < 0.03 else 0,

        "created_at": created_at.isoformat(),

        "updated_at": updated_at.isoformat()
    }


deals = []
deal_number = 1

for company in companies:
    for _ in range(2):
        deals.append(
            generate_deal(deal_number, company)
        )

        deal_number += 1


with open("sources/deals.json", "w", encoding="utf-8") as f:
    json.dump(
        deals,
        f,
        indent=2,
        ensure_ascii=False
    )