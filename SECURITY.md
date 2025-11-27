# Security Policies

## JWT Secret Rotation
- Rotate the JWT secret using `scripts/rotate_jwt_secret.py` at least once per quarter or immediately after any credential exposure.
- Roll out a new secret by updating the secret manager/`.env` value, redeploying the API, and invalidating old tokens. Previous secrets must be removed from the runtime configuration to prevent reuse.
- Users will be forced to re-authenticate after a rotation; communicate the maintenance window and expect active sessions to expire.

## Password Policy
- Minimum length: 12 characters. Passwords must include upper and lower-case letters, at least one digit, and at least one symbol.
- Passwords are hashed with **Argon2id**; reuse of previous passwords should be avoided for at least the last 5 rotations.
- If pwned password checks are enabled, newly chosen passwords that appear in breach databases must be rejected.

## XSS Handling
- Frontend rendering must sanitize any user-supplied HTML. Use trusted components and avoid raw HTML unless sanitized via a vetted utility.
- `dangerouslySetInnerHTML` (or similar APIs) are only allowed when the data is sanitized beforehand or originates from a trusted CMS pipeline.
- Inputs should be encoded on output in templates; UI code that must bypass encoding must include an inline comment explaining the sanitization step.
