# Confirmed Vulnerabilities — CSC4026Z Chat Server

_All findings are reproducible. Run the corresponding probe to verify._

---

### VULN-01: CHANNEL_INFO Exposes Member Lists to Non-Members

**Severity:** Medium  
**Category:** Authorisation / Information Disclosure  
**Probe:** `probes/08_channel_info_nonexistent.py`  
**PoC:** `pocs/poc_channel_info_disclosure.py`

**Description:**  
Any authenticated user can call `CHANNEL_INFO` (request_type 6) on any channel, regardless of whether they are a member of that channel. The server returns the full member list and channel description to non-members, allowing enumeration of every channel's membership.

**Steps to Reproduce:**
1. Connect as user A and create a private channel.
2. Connect as user B (who has NOT joined the channel).
3. User B calls `CHANNEL_INFO` with the channel name.
4. Server returns `response_type 27` with the member list and description.

**Evidence:**
```
Non-member CHANNEL_INFO:
{b'session': 2836482194, b'response_handle': 4215565915, b'response_type': 27,
 b'channel': b'private-9440', b'description': b'secret stuff',
 b'members': [b'cleartext_user_39562134']}
```

**Impact:**  
Any user can enumerate the membership of any channel on the server without joining it. Combined with `USER_LIST`, this allows building a complete social graph of all users and their channel memberships.

**Expected Behaviour:**  
`CHANNEL_INFO` should return an error (e.g. "Not in channel" or "Not found") for users who are not members of the channel.

---

### VULN-02: Username Accepts Control Characters and Injection Strings

**Severity:** Medium  
**Category:** Input Validation  
**Probe:** `probes/04_username_special_chars.py`  
**PoC:** `pocs/poc_username_injection.py`

**Description:**  
The server accepts usernames containing control characters (`\n`, `\r`, `\t`), null bytes (`\x00`), HTML tags, and Unicode direction-override characters after the `clear-` prefix. Only the length limit (≤ 20 characters) and the `clear-` prefix are validated; the content of the suffix is not.

**Steps to Reproduce:**
1. Connect as a cleartext user.
2. Call SET_USERNAME (request_type 13) with `username = 'clear-\nINJECTED'`.
3. Server responds with response_type 34 (success).

**Evidence:**
```
Accepted usernames:
  'clear-\n'       → response_type 34 (success)
  'clear-\t'       → response_type 34 (success)
  'clear-\r'       → response_type 34 (success)
  'clear-test\x00end' → response_type 34 (success)
  'clear-<script>' → response_type 34 (success)
  "clear-'; DROP TABLE" → response_type 34 (success)
  'clear-‮'  (RTL override) → response_type 34 (success)
```

**Impact:**  
- Log injection via newline characters
- Display spoofing via right-to-left override characters (e.g. a username that appears as a different name in a terminal)
- Potential XSS in any web-based client displaying usernames
- Null byte injection: `clear-test\x00end` — systems that treat strings as null-terminated would see this as `clear-test`

**Expected Behaviour:**  
Usernames should be validated against a strict allowlist (e.g. `[a-zA-Z0-9_\-]`) after the `clear-` prefix. Control characters, null bytes, and format-override characters should be rejected.

---

### VULN-03: Internal Python Error Messages Exposed

**Severity:** Medium  
**Category:** Information Disclosure  
**Probe:** `probes/10_negative_offset_pagination.py`, `probes/14_wrong_types.py`, `probes/22_unicode_username.py`  
**PoC:** `pocs/poc_error_disclosure.py`

**Description:**  
Multiple request fields, when given unexpected types or values, cause the server to return raw Python exception messages in the `error` field. This reveals that the server is implemented in Python and exposes internal code structure.

**Steps to Reproduce:**
1. Connect as any user.
2. Send `CHANNEL_LIST` (request_type 5) with `offset = 1.5` (a float).
3. Server returns the raw Python error: `"slice indices must be integers or None or have an __index__ method"`.

More examples:

| Request | Value sent | Python error returned |
|---|---|---|
| CHANNEL_LIST | `offset = 1.5` | `"slice indices must be integers or None or have an __index__ method"` |
| CHANNEL_LIST | `offset = "ten"` | `"can only concatenate str (not 'int') to str"` |
| PING | `session = [123]` | `"int() argument must be a string, a bytes-like object or a real number, not 'list'"` |
| CHANNEL_CREATE | `channel = None` | `"object of type 'NoneType' has no len()"` |
| SET_USERNAME | raw bytes `b'clear-\xc0\x80'` | `"startswith first arg must be bytes or a tuple of bytes, not str"` |

**Evidence:**
```
offset=1.5 → {b'error': b'slice indices must be integers or None or have an __index__ method'}
session=[1] → {b'error': b"int() argument must be a string, a bytes-like object or a real number, not 'list'"}
channel=None → {b'error': b"object of type 'NoneType' has no len()"}
```

**Impact:**  
- Confirms server is written in Python
- Reveals pagination uses Python list slicing (`data[offset:offset+n]`)
- Reveals session lookup uses `int()` conversion directly on the field value
- Reveals username prefix checking uses `.startswith()` which can be confused by bytes vs. str
- Provides a roadmap for crafting more targeted attacks

**Expected Behaviour:**  
Input fields should be validated and type-checked before use. Error messages returned to clients should be generic ("Invalid parameter") and not expose internal exceptions.

---

### VULN-04: Negative Request Handle Accepted

**Severity:** Low  
**Category:** Input Validation  
**Probe:** `probes/15_request_handle_zero.py`

**Description:**  
Two related issues with `request_handle` validation:

1. `handle = -1` is silently accepted and echoed back. Handles are defined as u32 (unsigned 32-bit integers, range 0–4294967295), so negative values should be rejected.
2. `handle = 0` is rejected with "Handle is required" — the server uses a Python falsy check (`if not handle`) rather than `if handle is None`, treating 0 as "not provided." This prevents clients from using 0 as a valid handle, even though 0 is a valid u32.

**Evidence:**
```
Handle=-1  → {b'response_handle': -1, b'response_type': 24}  ← ACCEPTED
Handle=0   → {b'error': b'Handle is required'}               ← REJECTED (but 0 is a valid u32)
Handle=max → {b'response_handle': 4294967295, b'response_type': 24}  ← accepted correctly
```

**Impact:**  
Negative handles violate the protocol spec. A client that uses a counter starting at -1 would work, which could cause confusion in implementations that strictly validate u32 handle values.

**Expected Behaviour:**  
Reject any handle value outside the range [1, 2³²−1]. The current "falsy" check rejects 0 but allows negatives, which is the wrong pair to reject/accept.

---

### VULN-05: Duplicate Packet Processing

**Severity:** Medium  
**Category:** Logic Error  
**Probe:** `probes/15_request_handle_zero.py`

**Description:**  
When two identical packets are sent in rapid succession (same `request_handle`, same `request_type`, same `session`), the server processes both and returns two responses. There is no deduplication or idempotency check on incoming requests.

**Steps to Reproduce:**
1. Connect as any user.
2. Send the same PING packet twice in immediate succession (same handle, same session).
3. Receive two separate PING responses, each with the same `response_handle`.

**Evidence:**
```python
sock.send(msgpack.packb({'request_type': 3, 'session': session, 'request_handle': handle}))
sock.send(msgpack.packb({'request_type': 3, 'session': session, 'request_handle': handle}))
# Result: two responses received, both with the same response_handle
responses = [{b'response_type': 24, b'response_handle': 3009613778},
             {b'response_type': 24, b'response_handle': 3009613778}]
```

**Impact:**  
For read-only operations (PING, WHOAMI) this is harmless. However, for state-mutating operations (SET_USERNAME, CHANNEL_CREATE, CHANNEL_JOIN, DM) submitting the same request twice may:
- Trigger the same side-effects twice (e.g. two join notifications sent to channel members)
- Cause double-delivery of DMs
- Exploit any per-operation rate-limit counters

**Expected Behaviour:**  
The server should deduplicate requests by `(session, request_handle)` pair within a short time window and return the cached response to the second identical packet.

---

### VULN-06: Negative Offset Wraps on USER_LIST (Python List Slicing)

**Severity:** Low  
**Category:** Input Validation  
**Probe:** `probes/10_negative_offset_pagination.py`

**Description:**  
Sending `offset = -1` with USER_LIST (request_type 14) is accepted and returns results — specifically, users from the end of the list (Python negative indexing). This is because the server uses Python list slicing for pagination without validating that the offset is non-negative.

**Evidence:**
```
USER_LIST offset=0  → {b'users': [b'cleartext_user_31704385'], b'next_page': False}
USER_LIST offset=-1 → {b'users': [b'cleartext_user_31704385'], b'next_page': False}
```
Both return the same result because only one user was present, but with more users `offset=-1` would return the last page of results regardless of how many users exist.

**Impact:**  
Clients can access the last page of the user list using offset=-1 without knowing the total user count. This bypasses pagination and can be used to quickly find "recently registered" or "last-sorted" users.

**Expected Behaviour:**  
Offset should be validated as `>= 0` before being used in list slicing.

---

## Summary Table

| ID | Finding | Severity | Category |
|---|---|---|---|
| VULN-01 | CHANNEL_INFO exposes non-member data | Medium | Authorisation |
| VULN-02 | Username accepts control chars / injection strings | Medium | Input Validation |
| VULN-03 | Python internal errors exposed in responses | Medium | Information Disclosure |
| VULN-04 | Negative request handle accepted | Low | Input Validation |
| VULN-05 | Duplicate packet double-processed | Medium | Logic Error |
| VULN-06 | Negative offset wraps on USER_LIST | Low | Input Validation |
