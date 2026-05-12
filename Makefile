.PHONY: setup test test-live test-all run clean

# First-time setup: generates your .env from your Base64 secret key
setup:
	uv run python env_setup.py

# Offline unit tests — no server needed, no keys needed
test:
	uv run pytest tests/test_primitives.py tests/test_handshake.py -v

# Live integration tests against csc4026z.link — requires .env to be set up first
test-live:
	@test -f .env || (echo "No .env found. Run: make setup" && exit 1)
	bash -c 'source .env && uv run pytest tests/test_live.py -v -s'

# Run all tests (offline first, then live)
test-all: test test-live

# TODO: start the chat client
run:
	# to be filled in by the client team

# Remove Python cache files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
