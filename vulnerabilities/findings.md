# Security Findings — CSC4026Z Chat Server

**Target:** `csc4026z.link` (cleartext port 51825, WireGuard port 51820)  
**Protocol:** UDP/msgpack custom chat protocol  
**Findings:** 4 confirmed vulnerabilities  
**Scope:** Authorised security research per assignment brief. DoS excluded.

---

## VULN-01 — CHANNEL_INFO Exposes Non-Member Data

**Severity:** Low  
**Category:** Broken Access Control  
**PoC:** `poc_01_channel_info_disclosure.py`

### What it is
Any authenticated user can call `CHANNEL_INFO` (request type 6) on any channel and receive the full member list and description — without ever joining that channel. The server does not check membership before responding.

### Impact
Read-only access control bypass. A single user can enumerate the membership of every channel on the server, exposing the complete social graph: who is in which channel, what those channels are for, and who is talking to whom. Cannot write, manipulate, or take over anything on its own.

### Reproduction
1. User A creates a channel.
2. User B (never joined) sends `CHANNEL_INFO` with that channel name.
3. Server returns `response_type 27` with the full member list and description.

### Evidence
```
Request:  {request_type: 6, session: <B's session>, channel: "private-91710"}
Response: {response_type: 27, channel: "private-91710",
           description: "confidential — members only",
           members: ["cleartext_user_22075748"]}
```

### Expected behaviour
Return an error ("not a member" or "not found") for users who have not joined the channel.

---

## VULN-02 — Username Accepts Control Characters and Injection Strings

**Severity:** Low  
**Category:** Input Validation  
**PoC:** `poc_02_username_injection.py`

### What it is
The server validates that cleartext usernames start with `clear-` and are under 20 characters, but applies no validation to the content after the prefix. Control characters, null bytes, and Unicode direction-override characters are accepted and stored verbatim.

### Impact
Log injection is blind — the attacker cannot read the logs they corrupt. The null byte is cosmetic. The RTL override (U+202E) causes text after it to render right-to-left in terminals, making a crafted name visually resemble another user's name, but by itself this is just a display oddity.

### Chain (Low likelihood)
Combined with VULN-04: an attacker waits for a known user to disconnect, immediately claims their username (VULN-04 releases it instantly), and sets it with an RTL override so it visually matches the original. Everyone still in the channel sees what appears to be the same user. Requires knowing when the target will disconnect and winning the race to claim the name — low likelihood, but worth noting.

| Payload | Attack |
|---|---|
| `clear-a\nb` | Log injection — inserts fake entries into server logs (blind) |
| `clear-test\x00end` | Null byte — C-string systems see a truncated name |
| `clear-a\r\nb` | CRLF injection — corrupts HTTP-adjacent log systems |
| `clear-‮admin` | RTL override — U+202E causes the suffix to render right-to-left in terminals |

### Reproduction
1. Connect as a cleartext user.
2. Send `SET_USERNAME` with `username = 'clear-\nFAKE LOG ENTRY'`.
3. Server responds with `response_type 34` (success).

### Evidence
```
Input:   username = 'clear-\n'
Stored:  b'clear-\n'           ← newline accepted

Input:   username = 'clear-\x00shadow'
Stored:  b'clear-\x00shadow'   ← null byte accepted

Input:   username = 'clear-‮admin'
Stored:  b'clear-\xe2\x80\xaeadmin'   ← RTL override accepted
```

### Expected behaviour
Reject any username containing characters outside `[a-zA-Z0-9_\-]` after the prefix.

---

## VULN-03 — Server Leaks Raw Python Exception Messages

**Severity:** Informational  
**Category:** Information Disclosure  
**PoC:** `poc_03_error_disclosure.py`

### What it is
Sending unexpected types for certain fields causes the server to return raw Python `TypeError` and `AttributeError` messages in the `error` response field, exposing internal code patterns.

### Impact
Purely informational. The server being Python is stated in the assignment brief, so that is not a finding. What the exceptions do reveal is five specific internal code patterns — pagination slicing, session integer casting, channel null handling — which map internal implementation details. These patterns informed the discovery of other vulnerabilities in this report but do not constitute an exploitable path on their own.

| Input | Python error returned | What it reveals |
|---|---|---|
| `offset = 1.5` | `"slice indices must be integers or None..."` | Pagination code: `data[offset : offset + PAGE_SIZE]` |
| `offset = "x"` | `"can only concatenate str (not 'int') to str"` | String concatenation without type check |
| `session = [list]` | `"int() argument must be a string..."` | Session lookup: `int(session)` called directly |
| `channel = None` | `"object of type 'NoneType' has no len()"` | Channel validation: `len(channel)` without null check |
| `username = b'\xc0\x80'` | `"startswith first arg must be bytes or a tuple..."` | Prefix check: bytes/str mismatch |

### Expected behaviour
Return a generic error message ("Invalid parameter") and handle all type errors internally without exposing exception details.

---

## VULN-04 — DISCONNECT Bypasses the 60-Second Username Hold Period

**Severity:** Low  
**Category:** Logic Error / Spec Violation  
**PoC:** `poc_04_username_reclaim.py`

### What it is
The spec requires cleartext usernames to be held for 60 seconds after a session ends, preventing immediate impersonation. The hold is only enforced when a session is abandoned (socket closed without sending DISCONNECT). When a user sends an explicit `DISCONNECT` (request type 2), the server releases the username immediately — the hold window is skipped entirely.

### Impact
A second user can claim the vacated username before the 60-second protection window has elapsed. The impersonation protection is effectively opt-out: any client that sends DISCONNECT bypasses it.

### Chain (Low likelihood)
Combined with VULN-02: see VULN-02 chain description. VULN-04 is the enabler — without it, the 60-second hold would close the window before an attacker could act.

### Reproduction
1. User A sets username to `clear-target`.
2. User A sends `DISCONNECT` (request type 2) and closes the socket.
3. User B immediately sends `SET_USERNAME` with `clear-target`.
4. Server accepts — username reclaimed in under 1 second.

### Evidence
```
[User A] Claimed: clear-usr1178
[User A] Sent DISCONNECT and closed socket
[User B] Immediate reclaim: SUCCESS — clear-usr1178

Control (no DISCONNECT, 5s wait):
[User B] Reclaim attempt: FAILED (Username already in use)
```

### Expected behaviour
The 60-second hold period should apply regardless of whether the session ended via explicit DISCONNECT or socket abandonment.

---

## Summary

| ID | Vulnerability | Severity | PoC |
|---|---|---|---|
| VULN-01 | CHANNEL_INFO exposes non-member data | Low | `poc_01_channel_info_disclosure.py` |
| VULN-02 | Username accepts control/injection chars | Low | `poc_02_username_injection.py` |
| VULN-03 | Python exceptions exposed in responses | Informational | `poc_03_error_disclosure.py` |
| VULN-04 | DISCONNECT bypasses username hold period | Low | `poc_04_username_reclaim.py` |

All four vulnerabilities are reproducible on demand by running the corresponding PoC script.
