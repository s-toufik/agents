from dataclasses import dataclass


@dataclass(slots=True)
class ClientSettings:
    base_url: str = ""
