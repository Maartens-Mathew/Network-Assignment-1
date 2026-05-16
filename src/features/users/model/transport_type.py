from enum import Enum, StrEnum


class TransportType(StrEnum):
    WIREGUARD = "wireguard"
    WIREGUARD_EXTENDED = "wireguard_extended"
    CLEARTEXT = "cleartext"