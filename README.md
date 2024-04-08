action-collect-test-data
=========================

This action collects test output data and metadata from the GitHub Actions
environment and uploads it to a Google Cloud Storage bucket.

### Inputs

- `path` (required): Path to the test output file.
- `gcs_path` (required): The path to the GCS bucket where the test data and metadata will be uploaded. This can include an optional prefix. The format is `bucket-name[/prefix]`. You don't need to include the `gs://` prefix.
- `gcp_project_id` (required): The ID of the GCP Project where the GCS bucket is located.
- `workload_identity_provider` (required): The identifier of the Workload Identity Provider that will be used to authenticate the action to GCP.
- `service_account_email` (required): The email address of the service account that will be used to authenticate the action to GCP.

### Outputs

- `uploaded`: A list of the files that were uploaded to the GCS bucket.

### Usage

```yaml
steps:
- name: Checkout
  uses: actions/checkout@v4

- name: Run tests
  run: echo "Run tests and generate an output file"

- name: Collect test data
  if: '!cancelled()' # Always run this step, unless the workflow was cancelled
  uses: getsentry/action-collect-test-data@v0.3.0
  with:
    path: ./test-output.xml
    gcs_path: my-gs-bucket/prefix/test-data
    gcp_project_id: my-gcp-project
    workload_identity_provider: projects/my-gcp-project/locations/global/workloadIdentityPools/my-pool/providers/my-provider
    service_account_email: my-service-account@my-gcp-project.iam.gserviceaccount.com
```
