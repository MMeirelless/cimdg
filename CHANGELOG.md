# Changelog

All notable changes to the CIM Data Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Core generation engine with template-driven CIM field generation
- 7 CIM data model generators (MVP): Authentication, Network Traffic, Web, Endpoint (Processes), Malware, Intrusion Detection, DNS
- Modular input for continuous event streaming
- Custom search command (`| cimgenerate`) for on-demand batch generation
- REST handler for dashboard integration
- Generator Configuration dashboard (SimpleXML)
- Full CIM compliance chain: props.conf, eventtypes.conf, tags.conf
- Cross-model entity pools for consistent IPs, users, and hostnames
- Business-hours timestamp distribution with realistic patterns
- Bundled Splunk Python SDK (splunklib v1.6.16)
- AppInspect CI/CD workflow
- Release packaging workflow
