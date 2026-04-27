# Model IDs for OpenRouter smoke tests and experiments.
#
# NOTE: openrouter/free was removed after proving unreliable during smoke testing
# due to frequent timeout and connection errors. It is not recommended for use.
#
# deepseek/deepseek-chat is now used as the default pinned smoke-test model.
# It is low-cost, consistently available on OpenRouter, and stable enough for
# connectivity and integration checks.
#
# IMPORTANT: This is still NOT a controlled AOSL experiment.
# For results to be meaningful, all of the following must be locked:
#   - exact model ID and version
#   - temperature
#   - prompt text
#   - judge model and scoring prompt
# Until those are pinned and documented, treat all output as exploratory only.
#
# To find other available models, visit: https://openrouter.ai/models

FREE_GENERATOR_MODELS = [
    "deepseek/deepseek-chat",
]

FREE_JUDGE_MODELS = [
    "deepseek/deepseek-chat",
]
