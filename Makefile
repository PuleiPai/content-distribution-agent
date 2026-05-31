PYTHON ?= python
COMPOSE ?= docker compose
ARTICLE ?=
VIDEO ?=
THUMBNAIL ?=

.PHONY: docker-build docker-shell docker-test docker-video-dry-run

docker-build:
	COMPOSE_DISABLE_ENV_FILE=1 $(COMPOSE) build agent

docker-shell:
	COMPOSE_DISABLE_ENV_FILE=1 $(COMPOSE) run --rm agent bash

docker-test:
	COMPOSE_DISABLE_ENV_FILE=1 $(COMPOSE) run --rm agent $(PYTHON) -m py_compile distribute.py video.py platforms/*.py video/*.py video_platforms/*.py

docker-video-dry-run:
	@if [ -z "$(ARTICLE)" ]; then echo "Usage: make docker-video-dry-run ARTICLE=<article_id> VIDEO=<path> THUMBNAIL=<path>"; exit 2; fi
	COMPOSE_DISABLE_ENV_FILE=1 $(COMPOSE) run --rm agent $(PYTHON) video.py distribute --article $(ARTICLE) --platform youtube --video "$(VIDEO)" --thumbnail "$(THUMBNAIL)" --dry-run
