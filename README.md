action-collect-test-data
=========================

This action collects test output data and metadata from the GitHub Actions
environment and uploads it to a Google Cloud Storage bucket.

### Inputs

- `path` (required): Path to the test output file.
- `gcs_path` (required): Path to the GCS bucket where the test data will be uploaded.
- `gcp_project_id` (required): GCP project ID.
- `workload_identity_provider` (required): Workload Identity Provider.
- `service_account_email` (required): Service Account Email.

### Outputs

- `uploaded`: The list of files uploaded to GCS.

### Usage

```yaml
steps:
- name: Checkout
  uses: actions/checkout@v4

- name: Run tests
  run: echo "Run tests and generate an output file"

- name: Collect test data
  if: '!cancelled()' # Always run this step, unless the workflow was cancelled
  uses: getsentry/action-collect-test-data@v0.1.0
  with:
    path: <path to test output file>
    gcs_path: <path to GCS bucket> # Can include an optional prefix
    gcp_project_id: <GCP project ID>
    workload_identity_provider: <Workload Identity Provider>
    service_account_email: <Service Account Email>
```
