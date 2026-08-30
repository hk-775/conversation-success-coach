.PHONY: demo test validate smoke sync-site

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

