"""DNS (Network Resolution) CIM data model generator."""

import random

from generators.base import BaseGenerator, register_generator


# Realistic domain generation pools
SUBDOMAINS = ["www", "mail", "api", "cdn", "static", "auth", "login", "app", "docs", "dev"]
TLDS = [".com", ".org", ".net", ".io", ".co", ".us", ".edu"]
WORDS = [
    "cloud", "secure", "fast", "data", "smart", "tech", "web", "net",
    "info", "global", "cyber", "digital", "edge", "core", "hub",
]

# DGA-style domains for suspicious DNS queries
DGA_CONSONANTS = "bcdfghjklmnpqrstvwxyz"
DGA_VOWELS = "aeiou"


@register_generator("dns")
class DNSGenerator(BaseGenerator):
    """
    Generates CIM-compliant DNS events.

    Special behaviors:
    - Realistic domain generation with subdomain variety
    - Query/Response pairing logic
    - DGA-style domains for suspicious queries (5% of traffic)
    - NXDOMAIN responses for non-existent domains
    """

    def __init__(self):
        super().__init__("dns")

    def _generate_domain(self):
        """Generate a realistic domain name."""
        word1 = random.choice(WORDS)
        word2 = random.choice(WORDS)
        tld = random.choice(TLDS)
        base = f"{word1}{word2}{tld}"

        if random.random() < 0.6:
            sub = random.choice(SUBDOMAINS)
            return f"{sub}.{base}"
        return base

    def _generate_dga_domain(self):
        """Generate a DGA-style suspicious domain."""
        length = random.randint(8, 16)
        name = ""
        for i in range(length):
            if i % 2 == 0:
                name += random.choice(DGA_CONSONANTS)
            else:
                name += random.choice(DGA_VOWELS)
        tld = random.choice([".xyz", ".top", ".cc", ".ru", ".cn", ".tk"])
        return f"{name}{tld}"

    def generate_event(self, timestamp=None, timerange_seconds=3600):
        event = super().generate_event(timestamp=timestamp, timerange_seconds=timerange_seconds)

        # Generate realistic query domains
        if random.random() < 0.05:
            # 5% DGA/suspicious domains
            event["query"] = self._generate_dga_domain()
            if random.random() < 0.7:
                event["reply_code"] = "NXDOMAIN"
                event["answer"] = ""
        elif random.random() < 0.5:
            # Use pool domains
            event["query"] = self.pool.random_external_domain()
        else:
            # Generate random domains
            event["query"] = self._generate_domain()

        # DNS servers are typically specific IPs
        dns_servers = ["10.0.0.2", "10.0.0.3", "172.16.0.2", "172.16.0.3"]
        event["dest"] = random.choice(dns_servers)

        # Query/Response consistency
        if event.get("message_type") == "Query":
            event["answer"] = ""
            event.pop("reply_code", None)
            event.pop("ttl", None)

        # NXDOMAIN means no answer
        if event.get("reply_code") == "NXDOMAIN":
            event["answer"] = ""

        return event
