# Pitfalls

## TypeError: Object of type date is not JSON serializable
In `codememory.py`, when saving the index to `index.json`, the YAML parser parsed `2026-04-24` as a Python `datetime.date` object. The standard `json.dump` does not know how to serialize `datetime.date`.
