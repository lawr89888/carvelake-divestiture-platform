# CarveLake — Databricks Platform Constraints

## Validation Results

### Gate 1 — Persona Identities

**Status: PASS**

Additional workspace identities are available and can be used to represent the Corporate Executive, BU Executive, and Business Group personas.

**Decision:** Use separate Databricks identities for multi-user security and dashboard testing.

**Evidence:** Workspace user-management test completed successfully.

---

### Gate 2 — Account Groups and Service Principals

**Status: PASS**

Account groups and service principals are available in the workspace.

**Decision:** Use account groups for Unity Catalog authorization and service principals where machine identities are required.

**Evidence:** Creation/availability successfully verified in the workspace.

---

### Gate 3 — Local CLI Authentication

**Status: PASS**

The local development environment can authenticate to the Databricks workspace using the Databricks CLI.

**Decision:** Use OAuth U2M for local development authentication.

**Evidence:** CLI authentication and workspace access successfully tested.

Do not store authentication credentials in Git.

---

### Gate 4 — Unattended CI Authentication

**Status: PASS**

GitHub Actions can authenticate to Databricks using service-principal OAuth M2M.

The following GitHub Actions secrets are configured:

* `DATABRICKS_HOST`
* `DATABRICKS_CLIENT_ID`
* `DATABRICKS_CLIENT_SECRET`

**Decision:** Use service-principal OAuth M2M for CarveLake CI/CD.

**Evidence:** Unattended authentication successfully tested.

---

### Gate 5 — Dashboard Security

**Status: PASS**

Databricks AI/BI Dashboard individual data permissions are available, and separate user identities can produce different row-filtered results.

**Decision:** Publish the CarveLake dashboard using individual data permissions so Unity Catalog authorization is evaluated using the viewer's identity.

**Evidence:** Multi-identity dashboard security successfully tested.

---

### Gate 6 — Buyer Handover

**Status: PASS**

OpenSharing functionality required for the buyer-handover demonstration is available.

**Decision:** Use OpenSharing as the preferred buyer-handover mechanism during the `bu_06` divestiture drill.

The `buyer_bu_06` same-metastore catalog remains available as a validation/fallback mechanism if required during implementation.

**Evidence:** OpenSharing availability successfully verified.

---

### Gate 7 — Free Edition Quota Behavior

**Status: DEFERRED**

The complete Bronze → Silver → Gold pipeline does not exist yet, so quota behavior cannot be meaningfully validated.

After implementation, run:

```text
Local ingestion
      ↓
Bronze
      ↓
bu_01
      ↓
bu_02
      ↓
bu_03
      ↓
bu_04
      ↓
bu_05
      ↓
bu_06
      ↓
Enterprise
```

Record execution time, quota warnings, quota-related failures or pauses, and relevant daily/monthly quota behavior.

The daily schedule must not be enabled until this test succeeds.

---

## Validation Summary

| Gate | Capability                           | Result   |
| ---- | ------------------------------------ | -------- |
| 1    | Multiple persona identities          | PASS     |
| 2    | Account groups & service principals  | PASS     |
| 3    | Local CLI authentication             | PASS     |
| 4    | Unattended CI authentication         | PASS     |
| 5    | Dashboard individual permissions/RLS | PASS     |
| 6    | OpenSharing buyer handover           | PASS     |
| 7    | Free Edition quota behavior          | DEFERRED |

## Conclusion

The workspace currently supports the identity, governance, authentication, CI/CD, dashboard-security, and buyer-handover capabilities required by the CarveLake design.

Gate 7 will be completed after the end-to-end pipelines and orchestration exist and before daily scheduling is enabled.

No credentials, OAuth secrets, PATs, API keys, or other secret values may be committed to the repository.
