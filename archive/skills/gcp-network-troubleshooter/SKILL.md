---
name: gcp-network-troubleshooter
description: Advanced diagnostics playbook for private VPC connectivity, serverless network bridges, and firewall blocks.
---
# Advanced Network Troubleshooting Skill

Use this skill when you encounter connection timeouts, DNS resolution failures, private IP peering blocks, database connection resets, or Serverless VPC Access connector failures.

### 1. Enable the Network Management API
Before executing any network diagnostics, ensure the required management API is enabled on your project:
```bash
gcloud services enable networkmanagement.googleapis.com
```

### 2. Initiate an Automated Connectivity Test
Create and execute a Connectivity Test to trace the network path, packet routes, and firewall rules between your service and target IP:
```bash
# Example: Test reachability from a Cloud Run revision to a private Cloud SQL IP
gcloud network-management connectivity-tests create cloudrun-to-db-test \
  --source-cloud-run-revision=$(gcloud run services list --limit=1 --format="value(REVISION)") \
  --destination-ip-address=10.128.0.5 \
  --destination-port=5432 \
  --protocol=TCP \
  --global
```

### 3. Parse Test Diagnostics & Firewall Blocks
Poll and fetch the described results of the Connectivity Test to locate exact packet drop locations or blocked ports:
```bash
# Describe test outcomes to locate ingress/egress firewall blocks
gcloud network-management connectivity-tests describe cloudrun-to-db-test --global
```

### 4. Fetch Firewall Insights (Active Assist)
Check if native GCP recommender engines have detected overlapping or shadowed firewall rules blocking VPC traffic:
```bash
gcloud recommender recommendations list \
  --recommender=google.compute.firewall.PolicyRecommender \
  --location=global
```
