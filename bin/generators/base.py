"""
Base generator for CIM-compliant synthetic events.

Provides entity pools (IPs, users, hosts), field generation by type dispatch,
template loading, and the GeneratorFactory for model routing.
"""

import hashlib
import ipaddress
import json
import math
import os
import random
import string
import time
import uuid


# ---------------------------------------------------------------------------
# Entity pools  -  shared across all generators for cross-model correlation
# ---------------------------------------------------------------------------

class EntityPool:
    """Pre-generated pools of realistic entity values."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._seed = int(time.time())
        self._rng = random.Random(self._seed)
        self.external_ratio = 0.2  # Configurable: fraction of external IPs in src
        self._build_pools()

    def _build_pools(self):
        """Build all entity pools."""
        self.internal_ips = self._generate_ips("10.0.0.0/16", 50)
        self.server_ips = self._generate_ips("172.16.0.0/24", 20)
        self.external_ips = self._generate_ips("203.0.113.0/24", 50) + \
                            self._generate_ips("198.51.100.0/24", 50)
        self.usernames = self._generate_usernames(50)
        self.hostnames = self._generate_hostnames(30)
        self.service_accounts = [
            "svc_backup", "svc_monitor", "svc_deploy", "svc_scanner",
            "svc_reporting", "svc_api", "svc_scheduler", "svc_sync"
        ]
        self.domains = [
            "corp.local", "internal.net", "example.com", "acme.org",
            "globex.com", "initech.net", "contoso.com", "fabrikam.com"
        ]
        self.external_domains = [
            "google.com", "github.com", "microsoft.com", "aws.amazon.com",
            "cloudflare.com", "akamai.com", "office365.com", "slack.com",
            "zoom.us", "salesforce.com", "okta.com", "duo.com",
            "example.com", "example.org", "example.net",
            "cdn.jsdelivr.net", "fonts.googleapis.com", "api.stripe.com"
        ]
        self.mac_addresses = [
            ":".join(f"{self._rng.randint(0, 255):02x}" for _ in range(6))
            for _ in range(30)
        ]
        self.email_subjects = [
            "Meeting agenda for Monday", "Q4 Budget Review",
            "Action Required: Password Expiry", "Invoice #INV-2026-0042",
            "Weekly Status Report", "Urgent: System Maintenance",
            "Re: Project Timeline Update", "FW: Customer Feedback",
            "Quarterly Compliance Report", "New Hire Onboarding",
            "Security Alert: Suspicious Activity", "IT Ticket Update",
            "Reminder: All-Hands Meeting", "Document Shared With You",
            "Purchase Order Confirmation", "Shipping Notification",
        ]
        self.certificate_issuers = [
            "DigiCert Inc", "Let's Encrypt", "Sectigo Limited",
            "GlobalSign", "GoDaddy", "Comodo CA", "Entrust",
        ]

    def _generate_ips(self, cidr, count):
        network = ipaddress.ip_network(cidr, strict=False)
        hosts = list(network.hosts())
        return [str(ip) for ip in self._rng.sample(hosts, min(count, len(hosts)))]

    def _generate_usernames(self, count):
        first_names = [
            "james", "mary", "john", "patricia", "robert", "jennifer",
            "michael", "linda", "david", "elizabeth", "william", "barbara",
            "richard", "susan", "joseph", "jessica", "thomas", "sarah",
            "charles", "karen", "daniel", "lisa", "matthew", "nancy",
            "anthony", "betty", "mark", "margaret", "donald", "sandra"
        ]
        last_names = [
            "smith", "johnson", "williams", "brown", "jones", "garcia",
            "miller", "davis", "rodriguez", "martinez", "hernandez", "lopez",
            "gonzalez", "wilson", "anderson", "thomas", "taylor", "moore",
            "jackson", "martin", "lee", "perez", "thompson", "white",
            "harris", "sanchez", "clark", "ramirez", "lewis", "robinson"
        ]
        combos = []
        for fn in first_names:
            for ln in last_names:
                combos.append(f"{fn}.{ln}")
        self._rng.shuffle(combos)
        return combos[:count]

    def _generate_hostnames(self, count):
        types = ["ws", "srv", "dc", "db", "web", "app", "fw", "proxy", "mail", "dns"]
        depts = ["it", "hr", "fin", "eng", "sec", "ops", "dev", "qa", "mkt", "sales"]
        hosts = []
        for _ in range(count):
            t = self._rng.choice(types)
            d = self._rng.choice(depts)
            n = self._rng.randint(1, 99)
            hosts.append(f"{t}-{d}-{n:02d}")
        return hosts

    def random_internal_ip(self):
        return random.choice(self.internal_ips)

    def random_server_ip(self):
        return random.choice(self.server_ips)

    def random_external_ip(self):
        return random.choice(self.external_ips)

    def random_src_ip(self):
        """Internal vs external based on external_ratio (default 20% external)."""
        if random.random() >= self.external_ratio:
            return self.random_internal_ip()
        return self.random_external_ip()

    def random_dest_ip(self):
        """70% server, 30% external."""
        if random.random() < 0.7:
            return self.random_server_ip()
        return self.random_external_ip()

    def random_username(self):
        return random.choice(self.usernames)

    def random_hostname(self):
        return random.choice(self.hostnames)

    def random_service_account(self):
        return random.choice(self.service_accounts)

    def random_domain(self):
        return random.choice(self.domains)

    def random_external_domain(self):
        return random.choice(self.external_domains)

    def random_mac_address(self):
        return random.choice(self.mac_addresses)

    def random_email_subject(self):
        return random.choice(self.email_subjects)

    def random_certificate_issuer(self):
        return random.choice(self.certificate_issuers)


# ---------------------------------------------------------------------------
# Timestamp generation  -  business-hours Gaussian distribution
# ---------------------------------------------------------------------------

def generate_timestamp(base_time=None, timerange_seconds=3600):
    """
    Generate a timestamp with business-hours weighting.

    Peak hours: 10 AM and 2 PM local time.
    Weekend volume: 30% of weekday.
    Returns epoch float with microsecond precision.
    """
    if base_time is None:
        base_time = time.time()

    offset = random.uniform(-timerange_seconds, 0)
    ts = base_time + offset

    lt = time.localtime(ts)
    hour = lt.tm_hour
    wday = lt.tm_wday  # 0=Monday, 6=Sunday

    # Business-hours weighting via acceptance-rejection
    if wday >= 5:  # Weekend
        if random.random() > 0.3:
            # Shift to weekday
            shift_days = wday - 4  # Saturday→Friday, Sunday→Friday
            ts -= shift_days * 86400
    else:
        # Gaussian peaks at 10 AM and 2 PM
        peak = random.choice([10, 14])
        gaussian_hour = random.gauss(peak, 3)
        gaussian_hour = max(6, min(22, gaussian_hour))
        hour_diff = gaussian_hour - hour
        ts += hour_diff * 3600

    return round(ts, 6)


# ---------------------------------------------------------------------------
# Base generator
# ---------------------------------------------------------------------------

class BaseGenerator:
    """
    Template-driven generator for CIM-compliant synthetic events.

    Subclasses override generate_event() for model-specific logic.
    """

    def __init__(self, model_name=None):
        self.model_name = model_name or self._default_model_name()
        self.pool = EntityPool()
        self.template = self._load_template()

    def _default_model_name(self):
        return self.__class__.__name__.replace("Generator", "").lower()

    def _load_template(self):
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "templates"
        )
        template_path = os.path.join(template_dir, f"{self.model_name}.json")
        if os.path.exists(template_path):
            with open(template_path, "r") as f:
                return json.load(f)
        return {}

    def get_sourcetype(self):
        return self.template.get("sourcetype", f"cimdg:synthetic:{self.model_name}")

    def generate_field(self, field_def):
        """Dispatch field generation based on type."""
        field_type = field_def.get("type", "static")

        dispatch = {
            "weighted_choice": self._gen_weighted_choice,
            "src_ip": lambda fd: self.pool.random_src_ip(),
            "dest_ip": lambda fd: self.pool.random_dest_ip(),
            "internal_ip": lambda fd: self.pool.random_internal_ip(),
            "server_ip": lambda fd: self.pool.random_server_ip(),
            "external_ip": lambda fd: self.pool.random_external_ip(),
            "username": lambda fd: self.pool.random_username(),
            "hostname": lambda fd: self.pool.random_hostname(),
            "service_account": lambda fd: self.pool.random_service_account(),
            "domain": lambda fd: self.pool.random_domain(),
            "external_domain": lambda fd: self.pool.random_external_domain(),
            "port": self._gen_port,
            "high_port": lambda fd: random.randint(1024, 65535),
            "number": self._gen_number,
            "lognormal": self._gen_lognormal,
            "static": lambda fd: fd.get("value", ""),
            "choice": lambda fd: random.choice(fd.get("values", [""])),
            "md5_hash": lambda fd: hashlib.md5(
                random.randbytes(32)
            ).hexdigest(),
            "sha256_hash": lambda fd: hashlib.sha256(
                random.randbytes(32)
            ).hexdigest(),
            "process_id": lambda fd: random.randint(100, 65535),
            "url": self._gen_url,
            "email_address": self._gen_email,
            "file_path": self._gen_file_path,
            "file_name": self._gen_file_name,
            "mac_address": lambda fd: self.pool.random_mac_address(),
            "session_id": lambda fd: uuid.uuid4().hex,
            "cve_id": self._gen_cve_id,
            "certificate_serial": lambda fd: uuid.uuid4().hex[:16].upper(),
            "certificate_subject": self._gen_certificate_subject,
            "email_subject": lambda fd: self.pool.random_email_subject(),
            "message_id": self._gen_message_id,
            "registry_path": self._gen_registry_path,
            "registry_value": self._gen_registry_value,
            "service_name": self._gen_service_name,
            "ticket_id": self._gen_ticket_id,
            "timestamp_future": self._gen_timestamp_future,
            "file_size": lambda fd: random.randint(
                fd.get("min", 100), fd.get("max", 10000000)),
        }

        gen_func = dispatch.get(field_type)
        if gen_func:
            return gen_func(field_def)
        return field_def.get("value", "")

    def _gen_weighted_choice(self, field_def):
        values = field_def.get("values", [])
        if not values:
            return ""
        choices = [v["value"] for v in values]
        weights = [v.get("weight", 1) for v in values]
        return random.choices(choices, weights=weights, k=1)[0]

    def _gen_port(self, field_def):
        common_ports = field_def.get("common_ports", [80, 443, 22, 53, 8080, 3389, 25, 110, 993, 8443])
        if random.random() < 0.8:
            return random.choice(common_ports)
        return random.randint(1024, 65535)

    def _gen_number(self, field_def):
        min_val = field_def.get("min", 0)
        max_val = field_def.get("max", 1000)
        precision = field_def.get("precision", 0)
        val = random.uniform(min_val, max_val)
        if precision == 0:
            return int(val)
        return round(val, precision)

    def _gen_lognormal(self, field_def):
        mu = field_def.get("mu", 6)
        sigma = field_def.get("sigma", 2)
        val = random.lognormvariate(mu, sigma)
        max_val = field_def.get("max", 1000000)
        val = min(val, max_val)
        precision = field_def.get("precision", 0)
        if precision == 0:
            return int(val)
        return round(val, precision)

    def _gen_url(self, field_def):
        domain = self.pool.random_external_domain()
        paths = ["/", "/index.html", "/api/v1/users", "/login", "/dashboard",
                 "/search", "/api/data", "/static/main.js", "/images/logo.png",
                 "/docs/guide", "/admin/settings", "/auth/callback"]
        path = random.choice(paths)
        scheme = random.choice(["https", "http"]) if random.random() < 0.3 else "https"
        return f"{scheme}://{domain}{path}"

    def _gen_email(self, field_def):
        user = self.pool.random_username()
        domain = random.choice(["corp.local", "company.com", "example.com"])
        return f"{user}@{domain}"

    def _gen_file_path(self, field_def):
        os_type = field_def.get("os", random.choice(["windows", "linux"]))
        if os_type == "windows":
            roots = ["C:\\Windows\\System32", "C:\\Program Files", "C:\\Users\\Public",
                     "C:\\Windows\\Temp", "C:\\ProgramData"]
            return random.choice(roots) + "\\" + self._gen_file_name(field_def)
        else:
            roots = ["/usr/bin", "/tmp", "/var/log", "/etc", "/opt", "/home"]
            return random.choice(roots) + "/" + self._gen_file_name(field_def)

    def _gen_file_name(self, field_def):
        extensions = field_def.get("extensions", [".exe", ".dll", ".py", ".sh", ".conf", ".log", ".tmp"])
        names = ["svchost", "update", "config", "data", "report", "backup",
                 "agent", "service", "monitor", "worker", "task", "process"]
        return random.choice(names) + random.choice(extensions)

    def _gen_cve_id(self, field_def):
        year = random.randint(2019, 2026)
        num = random.randint(1000, 50000)
        return f"CVE-{year}-{num}"

    def _gen_certificate_subject(self, field_def):
        domain = self.pool.random_external_domain()
        org = random.choice([
            "Acme Corp", "Globex Inc", "Initech LLC", "Contoso Ltd",
            "Example Org", "TechCorp", "CloudServices Inc",
        ])
        country = random.choice(["US", "GB", "DE", "FR", "JP", "CA", "AU"])
        return f"CN={domain},O={org},C={country}"

    def _gen_message_id(self, field_def):
        rand_part = uuid.uuid4().hex[:12]
        domain = random.choice(["mail.corp.local", "smtp.company.com", "mx.example.com"])
        return f"<{rand_part}@{domain}>"

    def _gen_registry_path(self, field_def):
        hives = ["HKLM", "HKCU", "HKU"]
        paths = [
            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\App",
            "SOFTWARE\\Policies\\Microsoft\\Windows\\System",
            "SYSTEM\\CurrentControlSet\\Services\\SomeService",
            "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon",
            "SOFTWARE\\Classes\\CLSID\\{random}",
            "SYSTEM\\CurrentControlSet\\Control\\SecurityProviders",
            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders",
        ]
        return f"{random.choice(hives)}\\{random.choice(paths)}"

    def _gen_registry_value(self, field_def):
        names = [
            "ImagePath", "Start", "Type", "DisplayName", "Description",
            "ObjectName", "ErrorControl", "DependOnService", "FailureActions",
        ]
        return random.choice(names)

    def _gen_service_name(self, field_def):
        services = [
            "wuauserv", "WinDefend", "Spooler", "BITS", "W32Time",
            "Dhcp", "Dnscache", "EventLog", "LanmanServer", "LanmanWorkstation",
            "sshd", "nginx", "httpd", "mysqld", "postgresql",
            "cron", "docker", "kubelet", "splunkd", "rsyslog",
        ]
        return random.choice(services)

    def _gen_ticket_id(self, field_def):
        prefix = field_def.get("prefix", random.choice(["INC", "CHG", "PRB", "REQ"]))
        num = random.randint(100000, 999999)
        return f"{prefix}-{num}"

    def _gen_timestamp_future(self, field_def):
        """Generate a future timestamp (e.g., for certificate expiry)."""
        days_ahead = random.randint(
            field_def.get("min_days", -30),
            field_def.get("max_days", 365),
        )
        return time.time() + (days_ahead * 86400)

    def apply_dependencies(self, event, dependencies):
        """Apply conditional field overrides based on event values."""
        if not dependencies:
            return

        for condition, overrides in dependencies.items():
            field_name, expected_value = condition.split("=", 1)
            if event.get(field_name) == expected_value:
                for override_field, override_def in overrides.items():
                    event[override_field] = self.generate_field(override_def)

    def generate_event(self, timestamp=None, timerange_seconds=3600):
        """
        Generate a single CIM-compliant event as a dict.

        Override in subclasses for model-specific behavior.
        """
        if timestamp is None:
            timestamp = generate_timestamp(timerange_seconds=timerange_seconds)

        event = {"_time": timestamp}

        # Generate fields from template
        fields = self.template.get("fields", {})
        for field_name, field_def in fields.items():
            event[field_name] = self.generate_field(field_def)

        # Apply dependency overrides
        dependencies = self.template.get("dependencies", {})
        self.apply_dependencies(event, dependencies)

        return event

    def generate_batch(self, count=100, base_time=None, timerange_seconds=3600):
        """Generate a batch of events."""
        if base_time is None:
            base_time = time.time()

        events = []
        for _ in range(count):
            ts = generate_timestamp(base_time=base_time, timerange_seconds=timerange_seconds)
            event = self.generate_event(timestamp=ts, timerange_seconds=timerange_seconds)
            events.append(event)

        events.sort(key=lambda e: e.get("_time", 0))
        return events

    def format_event(self, event):
        """Format event as JSON string for Splunk ingestion."""
        return json.dumps(event, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Generator factory
# ---------------------------------------------------------------------------

_GENERATOR_REGISTRY = {}


def register_generator(model_name):
    """Decorator to register a generator class for a model name."""
    def decorator(cls):
        _GENERATOR_REGISTRY[model_name] = cls
        return cls
    return decorator


class GeneratorFactory:
    """Factory for creating model-specific generators."""

    @classmethod
    def create(cls, model_name):
        """Create a generator for the given model name."""
        model_name = model_name.lower().strip()
        generator_cls = _GENERATOR_REGISTRY.get(model_name)
        if generator_cls is None:
            raise ValueError(
                f"Unknown model: {model_name}. "
                f"Supported models: {', '.join(cls.list_models())}"
            )
        return generator_cls()

    @classmethod
    def list_models(cls):
        """Return list of registered model names."""
        return sorted(_GENERATOR_REGISTRY.keys())
