"""
PROBE 17 — Username Race Condition
Hypothesis: Two clients simultaneously trying to claim the same username —
does the server handle this atomically, or can both succeed?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import random
import threading
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    target_username = f"clear-race-{random.randint(1000, 9999)}"
    print(f"Racing to claim username: {target_username}")
    results = []
    lock = threading.Lock()

    def try_claim():
        try:
            sock, session, _ = connect_cleartext()
            response = send_recv(sock, {
                'request_type': 13, 'session': session,
                'request_handle': make_handle(),
                'username': target_username
            })
            with lock:
                results.append(response)
            sock.close()
        except Exception as e:
            with lock:
                results.append({b'error': str(e).encode()})

    # Launch simultaneous attempts
    threads = [threading.Thread(target=try_claim) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"Race results ({len(results)} responses):")
    for r in results:
        print(f"  {r}")

    successes = [r for r in results if r and r.get(b'response_type') == 34]
    print(f"Successful claims: {len(successes)}")

    vulnerable = len(successes) > 1
    report(
        'PROBE 17 — Username Race Condition',
        "More than one client simultaneously claims the same username",
        {'successful_claims': len(successes), 'all_results': results},
        vulnerable,
        evidence=f"{len(successes)} clients claimed '{target_username}' simultaneously" if vulnerable else "Only one claim succeeded — race condition handled correctly"
    )

if __name__ == '__main__':
    run()
