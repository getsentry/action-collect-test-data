### Inputs

- `path` (required): Path to the test output file.
- `upload-type`: one of several values (currently just one)
  - pytest - expects a `*.json` file from the [pytest-json-report] plugin
- `workload_identity_provider` (required): The identifier of the Workload
  Identity Provider that will be used to authenticate the action to GCP.
- `service_account_email` (required): The email address of the service account
  that will be used to authenticate the action to GCP.

### Outputs

- `uploaded`: A list of the files that were uploaded to the GCS bucket.

### Usage

```yaml
steps:
  - name: Checkout
    uses: actions/checkout@v4

  - name: Run tests
    run: |
      echo "Run tests and generate an output file"
      pytest ... \
        --json-report \
        --json-report-file=".artifacts/pytest-report.json" \
        --json-report-omit=log \
      ;

  - name: Collect pytest data
    if: "!cancelled()" # Always run this step, unless the workflow was cancelled
    uses: getsentry/action-devinfra-metrics/pytest@v0.3.0
    with:
      path: .artifacts/pytest-report.json
```

[pytest-json-report]: https://github.com/numirias/pytest-json-report
