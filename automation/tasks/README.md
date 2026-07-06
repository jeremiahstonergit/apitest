# Automation tasks

Place infrastructure management Python scripts in this directory and register them in
`automation/tasks.registry.json`. Scripts are executed by the FastAPI control-plane
through `python <script> --params-json '<json>'`.

Keep scripts idempotent and validate all parameters before making API calls.
