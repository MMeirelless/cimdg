# CIM Data Generator

**By MB2 Analytics**

The first CIM-native synthetic data generator for Splunk. Generate dynamic sample data mapped to Splunk CIM data models for testing searches, dashboards, correlation rules, and ES content — without production data.

## Supported CIM Data Models

Authentication, Network Traffic, Web, Endpoint (Processes), Malware, Intrusion Detection, DNS

## Installation

1. Download the latest `.spl` from [Releases](https://github.com/MMeirelless/cimdg/releases)
2. In Splunk Web: **Apps > Manage Apps > Install app from file**
3. Upload the `.spl` file and restart Splunk
4. Create a `synthetic_cim` index (recommended): **Settings > Indexes > New Index**

## Usage

### On-Demand Generation

```spl
| cimgenerate model="Authentication" count=100
| collect index=synthetic_cim
```

### Continuous Streaming

Enable modular inputs via **Settings > Data Inputs > CIM Data Generator** or the app's configuration dashboard.

### Verify CIM Compliance

```spl
| datamodel Authentication search | head 10
```

## Requirements

- Splunk Enterprise 9.1+
- Splunk CIM Add-on 5.0+ (optional, for data model acceleration)

## Support

- Issues: https://github.com/MMeirelless/cimdg/issues
- Email: matheus@mb2analytics.com

## License

Copyright (c) 2026 MB2 Analytics. All rights reserved.
