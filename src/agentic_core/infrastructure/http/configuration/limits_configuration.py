from dataclasses import dataclass


@dataclass(slots=True)
class LimitsSettings:
    timeout: int = 30
    keep_alive_timeout: int = 60
    ttl_dns_cache: int = 600
    max_connections: int = 1000
    max_connections_per_host: int = 100
    max_keep_alive_connections: int = 50
