---
name: gcp-iam-troubleshooter
description: Advanced diagnostics playbook for complex GCP authorization errors, cross-project lookups, and token impersonations.
---
# Advanced IAM Troubleshooting Skill

Use this skill when you encounter complex, nested, or cross-project authorization failures (`HTTP 403 Permission Denied`), token impersonation failures, or Service Account ActAs delegation issues.

### 1. Identify the Active Principal & Workspace Scope
Execute these commands to identify precisely which service account or developer identity is executing the commands:
```bash
# Print current active account and configured project
gcloud config list --format="json(core.account,core.project)"
```

### 2. Audit Active Service Account Roles & Bindings
Fetch the current IAM policy bindings for the project to verify if the executing account actually holds the required predefined permissions:
```bash
# Filter and print all roles bound to the active service account
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --filter="bindings.members:$(gcloud config get-value account)" \
  --format="table(bindings.role)"
```

### 3. Diagnose Service Account Impersonation Issues
If the setup relies on local impersonation (running commands *on behalf of* another high-privilege service account), verify that your active identity holds the Token Creator role on the target account:
```bash
# List accounts you have permission to impersonate or act as
gcloud iam service-accounts get-iam-policy target-service-account@project.iam.gserviceaccount.com \
  --filter="bindings.role:roles/iam.serviceAccountTokenCreator"
```

### 4. Apply Least-Privilege Remediation
Construct a clear Markdown table of findings and propose specific, predefined role mappings. **Never suggest wildcard owner or editor bindings.**
