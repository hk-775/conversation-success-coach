.PHONY: demo test validate smoke sync-site public-site build

demo:
	./scripts/demo.sh

test:
	./scripts/test.sh

validate:
	./scripts/validate.sh

smoke:
	./scripts/smoke.sh

sync-site:
	./scripts/sync-site.sh

public-site:
	node scripts/test_public_site.mjs

build:
	uv build
