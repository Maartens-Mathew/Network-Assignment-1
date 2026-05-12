"""
Run this once to set up your .env file with your WireGuard keys.

Your keys are on the assignment website. You need:
  - Your Secret Key   (Base64)
  - The Server Public Key is already hardcoded — you don't need to enter it.

Usage:
    uv run python env_setup.py
"""

import base64
import sys

try:
    import nacl.public
except ImportError:
    print("Error: pynacl is not installed. Run: uv sync")
    sys.exit(1)


def decode_key(label: str, b64: str) -> bytes:
    try:
        raw = base64.b64decode(b64.strip())
    except Exception:
        print(f"Error: could not decode {label} — make sure you copied the full Base64 string.")
        sys.exit(1)
    if len(raw) != 32:
        print(f"Error: {label} should be 32 bytes after decoding, got {len(raw)}.")
        sys.exit(1)
    return raw


def main():
    print("WireGuard .env setup")
    print("--------------------")
    print("Paste your keys from the assignment website (https://csc4026z.link/keys).\n")

    priv_b64 = input("Your Secret Key (Base64): ").strip()
    priv_bytes = decode_key("Secret Key", priv_b64)

    # Derive the public key from the private key
    try:
        pub_bytes = bytes(nacl.public.PrivateKey(priv_bytes).public_key)
    except Exception as e:
        print(f"Error: could not derive public key from secret key — {e}")
        sys.exit(1)

    env_content = (
        f"export WG_STATIC_PRIVATE={priv_bytes.hex()}\n"
        f"export WG_STATIC_PUBLIC={pub_bytes.hex()}\n"
    )

    with open(".env", "w") as f:
        f.write(env_content)

    print("\n.env written successfully.")
    print(f"  Private key : {priv_bytes.hex()[:16]}...  ({len(priv_bytes)} bytes)")
    print(f"  Public key  : {pub_bytes.hex()[:16]}...  ({len(pub_bytes)} bytes)")
    print("\nTo load your keys before running live tests:")
    print("  source .env")


if __name__ == "__main__":
    main()
