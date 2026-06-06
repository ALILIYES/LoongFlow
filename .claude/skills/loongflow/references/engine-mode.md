# LoongFlow Engine Mode

Follow these instructions to set up and run the LoongFlow evolutionary optimization engine.

**Model format:** Model names must use the `anthropic/` prefix (e.g., `anthropic/claude-sonnet-4-20250514`, `anthropic/deepseek-v3.2`). The actual model can be any model accessible via the configured endpoint. Requires `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`.

## Step 1: Check Prerequisites and Install

### Quick check: already installed?

If `.loongflow/engine/.venv` exists, LoongFlow is already set up. Just activate and skip to Step 2:

```bash
LOONGFLOW_DIR=".loongflow/engine"
if [ -d "$LOONGFLOW_DIR/.venv" ]; then
    source "$LOONGFLOW_DIR/.venv/bin/activate"
    echo "LoongFlow venv activated: $(python --version)"
fi
```

If the venv exists and activates successfully, **skip directly to Step 2 (Configure the Task)**.

### Fresh install

Only run this if `.loongflow/engine/.venv` does NOT exist:

1. **ANTHROPIC_API_KEY** is set:
   ```bash
   echo $ANTHROPIC_API_KEY | head -c 10
   ```
   If empty, tell the user:
   > LoongFlow requires an API key. Please set it:
   > `export ANTHROPIC_API_KEY="your-key-here"`

2. **ANTHROPIC_BASE_URL** is set:
   ```bash
   echo $ANTHROPIC_BASE_URL
   ```
   If empty, tell the user:
   > LoongFlow requires a base URL for the API endpoint. Please set it:
   > `export ANTHROPIC_BASE_URL="https://api.anthropic.com"` (or your custom endpoint)

3. **Download and install:**

```bash
LOONGFLOW_DIR=".loongflow/engine"

# Clone if not already present
if [ ! -d "$LOONGFLOW_DIR" ]; then
    git clone https://github.com/baidu-baige/LoongFlow "$LOONGFLOW_DIR"
fi

cd "$LOONGFLOW_DIR"
git pull origin main

# Prefer uv (handles Python version automatically), fall back to pip
if command -v uv &> /dev/null; then
    uv venv .venv --python 3.12
    source .venv/bin/activate
    uv pip install -e .
else
    python3.12 -m venv .venv || python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .
fi
```

**Note:** `uv venv --python 3.12` will automatically download Python 3.12 if not available on the system. This is the preferred approach.

## Step 2: Configure the Task

Create a task directory and generate `task_config.yaml`:

```bash
TASK_SLUG="<task-slug>"  # kebab-case name from user's task
TASK_DIR=".loongflow/$TASK_SLUG"
mkdir -p "$TASK_DIR"
```

### Generate task_config.yaml

Adapt the following template based on the user's task. Key fields to customize:
- `evolve.task`: The user's detailed task description
- `evolve.max_iterations`: Higher for harder problems (default: 50)
- `evolve.target_score`: The target quality threshold (default: 0.9)
- `evolve.evaluator.timeout`: Longer for complex evaluations (default: 600s)

```yaml
workspace_path: ".loongflow/<task-slug>/output"

llm_config:
  model: "anthropic/deepseek-v3.2"    # Must use anthropic/ prefix. Any model name after the slash.
  # url and api_key can also be set via ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY env vars
  # url: "https://api.anthropic.com"
  # api_key: "your-key"

planners:
  general_planner:
    permission_mode: "acceptEdits"
    max_turns: 30

executors:
  general_executor:
    permission_mode: "acceptEdits"
    max_turns: 50

summarizers:
  general_summarizer:
    permission_mode: "acceptEdits"
    max_turns: 30

evolve:
  task: |
    <INSERT USER'S TASK DESCRIPTION HERE>
  planner_name: "general_planner"
  executor_name: "general_executor"
  summary_name: "general_summarizer"
  max_iterations: 50
  target_score: 0.9
  concurrency: 1
  evaluator:
    timeout: 600
    agent:
      permission_mode: "acceptEdits"
      max_turns: 30
  database:
    storage_type: "in_memory"
    num_islands: 1
    population_size: 50
    checkpoint_interval: 5
    sampling_weight_power: 2
```

### Copy User Files

If the user has source code, data files, or evaluation scripts relevant to the task, copy them into the task directory:

```bash
# Copy user's files if provided
cp -r <user-files> "$TASK_DIR/"
```

If the user provides a custom evaluation script, save it as `eval_program.py` in the task directory. It must implement:

```python
def evaluate(solution_path: str) -> dict:
    return {
        "status": "success",
        "score": 0.0,  # 0.0 to 1.0
        "summary": "Description of evaluation result",
        "metrics": {},
        "artifacts": {}
    }
```

## Step 3: Launch Evolution

```bash
cd "$LOONGFLOW_DIR"
source .venv/bin/activate
./run_general.sh "../../$TASK_DIR" --background
```

Confirm launch by checking:
```bash
cat "$TASK_DIR/.run.pid"
tail -20 "$TASK_DIR/run.log"
```

Tell the user:
> LoongFlow evolution started in background for task `<task-slug>`.
> PID: `<pid>`, Log: `<log-path>`

## Step 4: Set Up Monitoring

Create a cron task that checks progress every 5 minutes. The monitoring script should:

1. **Check if the process is still running** via PID file
2. **Read the latest log entries** for progress updates
3. **Check checkpoints** for best score
4. **Report to user** when:
   - Evolution completes (process exits)
   - Target score is reached
   - A significant score improvement occurs (delta > 0.1)
   - An error occurs

### Monitoring Script Logic

```bash
TASK_SLUG="<task-slug>"
TASK_DIR=".loongflow/$TASK_SLUG"
PID_FILE="$TASK_DIR/.run.pid"
LOG_FILE="$TASK_DIR/run.log"

# Check if process is still running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "COMPLETED: Evolution process finished"
        # Read final results from log
        tail -50 "$LOG_FILE"
        exit 0
    fi
fi

# Check latest progress from log
tail -20 "$LOG_FILE" | grep -E "(best_score|iteration|completed|error)"
```

### On Completion

When evolution finishes, report to the user:
- **Best score** achieved
- **Solution location**: path to best solution files
- **Iteration count**: total iterations completed
- **Cost**: total token cost if available
- **How to view**: `tail -100 <log-path>` for full details

### Stopping a Task

If the user wants to stop the evolution:
```bash
cd .loongflow/engine
./run_general.sh stop "$TASK_SLUG"
```
