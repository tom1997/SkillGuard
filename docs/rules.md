# Rule Authoring

SkillGuard rules are YAML files under `skillguard/rules`.

Required fields:

- `id`: stable identifier, such as `SG-PY-003`
- `title`: short user-facing title
- `severity`: `info`, `low`, `medium`, `high`, or `critical`
- `category`: broad risk category
- `languages`: target language tags
- `match.regex`: high-confidence regular expression
- `message`: explanation shown in reports
- `remediation`: suggested fix

Optional `capabilities` entries add permission evidence to the scan result:

```yaml
capabilities:
  - kind: network
    access: connect
    resource: "$HOST"
```

Supported resource placeholders:

- `$HOST`: first HTTP(S) hostname found on the matched line
- `$ENV`: first environment variable name found on the matched line

Rules should prefer high confidence over broad coverage. A noisy rule is worse than a missing rule in v0.1 because users must be able to trust blocking findings.
