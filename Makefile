.PHONY: format check-format

format:
	black src/ tests/

check-format:
	black --check src/ tests/
