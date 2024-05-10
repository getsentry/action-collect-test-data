# \_send-to-devinfra-metrics

This action collects test output data and metadata from the GitHub Actions
environment and uploads it to a Google Cloud Storage bucket.

This action is an implementation-detail of the various specific metric
collections supported by definfra-metrics (e.g. [../pytest]).
