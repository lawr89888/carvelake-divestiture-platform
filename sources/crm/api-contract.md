# CarveLake CRM REST API Contract

## 1. Overview

The CRM source exposes company, contact, and deal data through a REST API.

Base URL:

http://<host>:8000/api/v1

Content-Type:

application/json

Authentication:

Bearer token

Example:

Authorization: Bearer <CRM_API_KEY>


## 2. Authentication

All `/api/v1/*` endpoints require an API key.

Request header:

Authorization: Bearer <CRM_API_KEY>

If the header is missing:

HTTP 401

Response:

{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authorization header is required."
  }
}

If the key is invalid:

HTTP 403

Response:

{
  "error": {
    "code": "INVALID_API_KEY",
    "message": "The provided API key is invalid."
  }
}


## 3. Endpoints

### GET /companies

Returns CRM companies.

Example:

GET /api/v1/companies

Supported query parameters:

| Parameter | Type | Required | Description |
|---|---|---|---|
| bu_id | string | No | Filter by business unit |
| updated_since | timestamp | No | Return records updated after timestamp |
| limit | integer | No | Page size, default 100, max 500 |
| offset | integer | No | Number of records to skip |

Example:

GET /api/v1/companies?bu_id=bu_01&limit=100&offset=0


### GET /contacts

Returns CRM contacts.

Example:

GET /api/v1/contacts?bu_id=bu_01


### GET /deals

Returns CRM deals.

Example:

GET /api/v1/deals?updated_since=2026-08-01T00:00:00Z


## 4. Pagination

Pagination uses `limit` and `offset`.

Example request:

GET /api/v1/deals?limit=100&offset=0

Example response:

{
  "data": [
    {
      "deal_id": "D-0000001",
      "company_id": "C-0000001",
      "amount": 15000,
      "currency": "USD",
      "bu_id": "bu_01",
      "updated_at": "2026-08-20T10:30:00+00:00"
    }
  ],
  "paging": {
    "limit": 100,
    "offset": 0,
    "returned": 100,
    "total": 480,
    "next_offset": 100
  }
}

When there are no more pages:

"next_offset": null


## 5. Incremental Filtering

The API supports incremental extraction using:

updated_since

Example:

GET /api/v1/deals?updated_since=2026-08-20T00:00:00Z

Only records where:

updated_at > updated_since

are returned.

Timestamp format:

ISO-8601 UTC

Example:

2026-08-20T14:30:00Z


## 6. Company Schema

{
  "company_id": "C-0000001",
  "name": "Example Ltd",
  "domain": "example.com",
  "industry": "Technology",
  "country": "Germany",
  "employee_count": 500,
  "annual_revenue": 5000000,
  "owner_rep": "John Smith",
  "is_active": true,
  "business_group": "bg_direct",
  "bu_id": "bu_01",
  "is_deleted": 0,
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-08-01T10:00:00Z"
}


## 7. Contact Schema

{
  "contact_id": "P-0000001",
  "company_id": "C-0000001",
  "first_name": "Anna",
  "last_name": "Smith",
  "email": "anna@example.com",
  "phone": "+1-555-1234",
  "job_title": "Data Manager",
  "lifecycle_stage": "customer",
  "bu_id": "bu_01",
  "is_deleted": 0,
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-08-01T10:00:00Z"
}


## 8. Deal Schema

{
  "deal_id": "D-0000001",
  "company_id": "C-0000001",
  "name": "Enterprise Contract",
  "amount": 45000,
  "currency": "USD",
  "stage": "proposal",
  "probability": 70,
  "close_date": "2026-10-01",
  "owner_rep": "John Smith",
  "business_group": "bg_direct",
  "bu_id": "bu_01",
  "is_deleted": 0,
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-08-01T10:00:00Z"
}


## 9. Error Responses

### 400 Bad Request

Used for invalid parameters.

Example:

{
  "error": {
    "code": "INVALID_LIMIT",
    "message": "limit must be between 1 and 500."
  }
}

### 401 Unauthorized

Missing authentication.

### 403 Forbidden

Invalid API key.

### 404 Not Found

Requested resource does not exist.

Example:

{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Resource D-9999999 was not found."
  }
}

### 405 Method Not Allowed

Unsupported HTTP method.

### 500 Internal Server Error

Unexpected application failure.


## 10. Databricks Ingestion Behavior

Initial load:

GET /api/v1/deals?limit=100&offset=0

Continue requesting pages using `next_offset`.

Incremental load:

GET /api/v1/deals?updated_since=<last_successful_watermark>&limit=100&offset=0

Databricks stores the maximum `updated_at` value from the successful ingestion as the next watermark.


## 11. Soft Deletes

Records are not physically removed.

Deleted records are returned with:

"is_deleted": 1

This allows downstream Databricks pipelines to propagate deletions into Silver and Gold tables.