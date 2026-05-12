# Security Findings — CSC4026Z Chat Server

**Target:** `csc4026z.link` (cleartext port 51825, WireGuard port 51820)  
**Protocol:** UDP/msgpack custom chat protocol  
**Findings:** 6 confirmed vulnerabilities  
**Scope:** Authorised security research per assignment brief. DoS excluded.

---

## VULN-01 — CHANNEL_INFO Exposes Non-Member Data

**Severity:** Medium  
**Category:** Broken Access Control  
**PoC:** `poc_01_channel_info_disclosure.py`

### What it is
Any authenticated user can call `CHANNEL_INFO` (request type 6) on any channel and receive the full member list and description — without ever joining that channel. The server does not check membership before responding.

### Impact
A single user can enumerate the membership of every channel on the server. Combined with `CHANNEL_LIST` (which is also unauthenticated per channel), this exposes the complete social graph: who is in which channel, what those channels are for, and who is talking to whom.

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

**Severity:** Medium  
**Category:** Input Validation  
**PoC:** `poc_02_username_injection.py`

### What it is
The server validates that cleartext usernames start with `clear-` and are under 20 characters, but applies no validation to the content after the prefix. Control characters, null bytes, and Unicode direction-override characters are accepted and stored verbatim.

### Impact

| Payload | Attack |
|---|---|
| `clear-line1\nINJECTED` | Log injection — inserts fake entries into server logs |
| `clear-test\x00shadow` | Null byte injection — systems treating strings as C-style see only `clear-test` |
| `clear-\r\nHTTP/1.1 200` | CRLF injection — can corrupt HTTP-adjacent log systems |
| `clear-‮admin` | Display spoofing — the RTL override U+202E causes the text after it to render right-to-left in most terminals, making the name visually misleading |

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

**Severity:** Medium  
**Category:** Information Disclosure  
**PoC:** `poc_03_error_disclosure.py`

### What it is
Sending unexpected types for certain fields causes the server to return raw Python `TypeError` and `AttributeError` messages in the `error` response field. These messages expose the server's programming language, specific built-in function calls, and internal code patterns.

### Impact
Each error is a window into the server's source code:

| Input | Python error returned | What it reveals |
|---|---|---|
| `offset = 1.5` | `"slice indices must be integers or None..."` | Pagination code: `data[offset : offset + PAGE_SIZE]` |
| `offset = "x"` | `"can only concatenate str (not 'int') to str"` | String concatenation used without type check |
| `session = [list]` | `"int() argument must be a string..."` | Session lookup: `int(session)` called directly on raw field |
| `channel = None` | `"object of type 'NoneType' has no len()"` | Channel validation: `len(channel)` without null check |
| `username = b'\xc0\x80'` | `"startswith first arg must be bytes or a tuple..."` | Prefix check: `username.startswith('clear-')` with bytes/str mismatch |

Combined, these confirm the server is Python, reveal five internal code patterns, and provide a roadmap for crafting targeted follow-up attacks.

### Expected behaviour
Return a generic error message ("Invalid parameter") and handle all type errors internally without exposing exception details.

---

## VULN-04 — Negative Request Handles Accepted; Zero Incorrectly Rejected

**Severity:** Low  
**Category:** Input Validation  
**PoC:** `poc_04_negative_handle.py`

### What it is
`request_handle` is defined as a u32 (unsigned 32-bit integer: 0 to 4,294,967,295). The server uses a Python falsy check (`if not handle`) rather than `if handle is None`, producing two symmetric bugs:

- `handle = 0` → **rejected** as "Handle is required" — but 0 is a valid u32
- `handle = -1` → **accepted** and echoed back — but -1 is not a valid u32

### Evidence
```
handle = 0          → error: "Handle is required"       ← BUG: 0 is valid
handle = -1         → response_type 24 (PONG)            ← BUG: -1 is invalid
handle = -1000      → response_type 24 (PONG)            ← BUG: -1000 is invalid
handle = 2^32 - 1   → response_type 24 (PONG)            ← correctly accepted
handle = 2^32       → error: "Handle must be an integer < 2^32"  ← correctly rejected
```

### Root cause
```python
# Current (wrong):
if not handle:          # treats 0 as missing
    raise "Handle is required"

# Correct:
if handle is None:      # only catches truly absent field
    raise "Handle is required"
if not (0 <= handle < 2**32):
    raise "Handle out of range"
```

---

## VULN-05 — Duplicate Packets Are Processed Twice

**Severity:** Medium  
**Category:** Logic Error / Missing Idempotency  
**PoC:** `poc_05_duplicate_processing.py`

### What it is
The server has no deduplication on `(session, request_handle)` pairs. Sending the same packet twice in rapid succession causes both to be processed independently, generating two responses and two side-effects.

### Impact
For read-only operations (PING, WHOAMI) this is harmless. For state-changing operations:

| Operation | Effect of sending twice |
|---|---|
| Channel message | Message delivered twice to all members |
| DM | Recipient receives two copies |
| SET_USERNAME | Two rename notifications sent to channel members |
| CHANNEL_JOIN | Two join notifications sent to members |

### Reproduction
```python
packet = msgpack.packb({
    'request_type': 9, 'session': sess_a,
    'request_handle': handle, 'channel': channel,
    'message': 'this was sent once'
})
sock.send(packet)
sock.send(packet)   # identical bytes, same handle
# recipient receives the message twice
```

### Evidence
```
Sent:     1 unique message packet (handle=X), transmitted twice
Received: 2 message deliveries on recipient socket, both handle=X
```

### Expected behaviour
Cache the last N `(session, request_handle)` pairs per session. On a duplicate, return the cached response without re-processing.

---

## VULN-06 — Negative Offset Wraps to End of User List

**Severity:** Low  
**Category:** Input Validation  
**PoC:** `poc_06_negative_offset.py`

### What it is
`USER_LIST` (request type 14) accepts a negative `offset` value and returns results from the end of the user list. This is a direct consequence of Python's list slicing semantics — `users[-1:]` returns the last element — being applied to user-supplied input without a non-negative check.

### Impact
An attacker can retrieve the last page of users (typically the most recently registered) with `offset = -1` without needing to know the total user count or paginate through the full list. This bypasses the intended sequential access pattern.

### Evidence
```
offset = 0    → users from the beginning of the list (expected)
offset = -1   → users from the END of the list       (unexpected)
offset = -5   → last 5 users                         (unexpected)
```

### Root cause
```python
# Current (wrong):
return users[offset : offset + PAGE_SIZE]   # Python wraps negative indices

# Correct:
if offset < 0:
    raise "Invalid offset"
return users[offset : offset + PAGE_SIZE]
```

---

## Summary

| ID | Vulnerability | Severity | PoC |
|---|---|---|---|
| VULN-01 | CHANNEL_INFO exposes non-member data | **Medium** | `poc_01_channel_info_disclosure.py` |
| VULN-02 | Username accepts control/injection chars | **Medium** | `poc_02_username_injection.py` |
| VULN-03 | Python exceptions exposed in responses | **Medium** | `poc_03_error_disclosure.py` |
| VULN-04 | Negative handle accepted; zero rejected | Low | `poc_04_negative_handle.py` |
| VULN-05 | Duplicate packets double-processed | **Medium** | `poc_05_duplicate_processing.py` |
| VULN-06 | Negative offset wraps on USER_LIST | Low | `poc_06_negative_offset.py` |

All six vulnerabilities are reproducible on demand by running the corresponding PoC script.
