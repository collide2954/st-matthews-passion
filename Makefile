# St Matthew Passion: build commands.
# Each target calls a command of the project. Run "make help" for the list.

.PHONY: help study fetch measure report check test lint format score parts audio video all

help: ## Show the targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/'

study: ## Build the full style study (download, measure, check, report)
	uv run stmatthew-study all

fetch: ## Download the open data files into the cache
	uv run stmatthew-study fetch

measure: ## Measure the data and write research/measured
	uv run stmatthew-study measure

report: ## Write docs/style-study.md from the tables
	uv run stmatthew-study report

check: ## Check the tables for errors
	uv run stmatthew-study check

test: ## Run the tests
	uv run pytest -q

lint: ## Check the code style
	uv run ruff check .
	uv run ruff format --check .

format: ## Format the code
	uv run ruff format .

score: ## Build the conductor score (build/score/score.pdf)
	uv run stmatthew score

parts: ## Build the two conductor scores and all parts (build/set)
	uv run stmatthew parts

audio: ## Render the audio master (build/audio)
	uv run stmatthew audio

video: ## Render the score video (build/video); the audio must exist
	uv run stmatthew video

all: ## Build the score, the parts, the audio, and the video
	uv run stmatthew all
