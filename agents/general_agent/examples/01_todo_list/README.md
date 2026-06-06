# 📝 Example 01: TODO List Application

**Difficulty**: ⭐ Beginner
**Time**: 5-10 minutes
**Goal**: Build your first AI-generated command-line TODO app

---

## 🎯 What You'll Learn

This is the perfect starting point for General Agent! In this example, you'll learn:

- ✅ How the **Plan-Execute-Summary (PES)** workflow works
- ✅ How General Agent evolves code through iterations
- ✅ How to run a task and find your generated code
- ✅ Basic task configuration in `task_config.yaml`

---

## 🚀 Quick Start (3 Commands)

```bash
# 1. Navigate to LoongFlow root
cd /path/to/LoongFlow

# 2. Set your API keys (if not already set)
export ANTHROPIC_API_KEY="your-key"
export ANTHROPIC_BASE_URL="your-endpoint"

# 3. Run the example
./run_general.sh 01_todo_list
```

That's it! The agent will now:
1. **Plan** how to build a TODO app
2. **Execute** the implementation
3. **Evaluate** the solution
4. **Summarize** what it learned
5. Repeat until it creates a working app!

---

## 📂 What This Example Generates

The General Agent will create a command-line TODO application with:

- ✅ **Add TODOs**: Add new tasks with descriptions
- ✅ **Mark Complete**: Mark tasks as done
- ✅ **List TODOs**: View all tasks with status
- ✅ **Persistent Storage**: Saves to JSON file
- ✅ **Clean Interface**: User-friendly command-line interaction

---

## 🔍 Where to Find Your Code

After running, check the output directory:

```bash
# The output uses UUID-based task directories, not "task_<timestamp>"
ls output-todo-list/
# You'll see: logs/  database/  <uuid>/  ...

# Navigate to an iteration
cd output-todo-list/<uuid>/1/executor/work_dir/
```

You'll find files like:
- `todo_app.py` - Main application
- `todos.json` - Data storage file (created on first run)

> 💡 **Tip**: Use the visualizer to browse results easily:
> ```bash
> python agents/general_agent/visualizer/visualizer.py --workspace ./output-todo-list --port 8080
> ```

---

## 🧪 Test Your Generated App

```bash
# Navigate to the generated code (replace <uuid> with actual directory name)
cd output-todo-list/<uuid>/1/executor/work_dir/

# Run the TODO app
python todo_app.py

# Try these commands:
# - Add a todo: "Buy groceries"
# - Add another: "Write documentation"
# - List all todos
# - Mark one as complete
# - List again to see the change
# - Exit and restart to verify persistence works!
```

> 💡 **Tip**: Use the [visualizer](../../../README.md#visualization) to browse and view generated code with syntax highlighting:
> ```bash
> python agents/general_agent/visualizer/visualizer.py --workspace ./output-todo-list --port 8080
> ```

---

## 📊 Understanding the Output Structure

```
output-todo-list/
├── logs/                              # Log files
│   └── evolux.log
├── database/                          # Evolution database & checkpoints
└── <task-uuid>/                       # Unique run ID (UUID format)
    └── 1/                             # Iteration 1 (numeric)
        ├── planner/
        │   ├── best_plan.md           # The agent's plan
        │   └── meta.json              # Token usage & status
        ├── executor/
        │   ├── work_dir/              # 🎯 YOUR CODE IS HERE
        │   │   ├── todo_app.py
        │   │   └── todos.json
        │   └── evaluator_dir/
        │       └── best_evaluation.json
        └── summarizer/
            └── best_summary.md        # What the agent learned

    └── 2/                             # Iteration 2 (improved version)
    └── 3/                             # Iteration 3...
    └── ...
```

**Key Points**:
- Each run creates a **UUID-based** task directory (e.g., `6bb70103-27aa-49fd-862b-26a329500f15`)
- Each iteration is a **numeric** subdirectory (1, 2, 3, ...)
- Higher score in `best_evaluation.json` = better solution
- Agent stops when `score >= target_score` (default: 0.85)

---

## ⚙️ Configuration Explained

Let's look at [task_config.yaml](task_config.yaml):

```yaml
workspace_path: "./output-todo-list"     # Where to save output

llm_config:
  model: "anthropic/deepseek-v4-pro"     # Which model to use

evolve:
  task: |
    Create a command-line TODO list application...  # Task description

  max_iterations: 30                     # Max evolution cycles
  target_score: 0.85                     # Stop when score ≥ 0.85
  concurrency: 1                         # Number of parallel evolutions
```

**What Each Part Does**:
- `workspace_path`: Where General Agent saves all output
- `llm_config`: Which LLM to use (Anthropic-compatible models)
- `task`: Natural language description of what to build
- `max_iterations`: Safety limit (stops even if target not reached)
- `target_score`: Quality threshold (0.0 = bad, 1.0 = perfect)

---

## 🎓 What Happens Behind the Scenes

### Iteration 1:
1. **Planner**: "I need to create a TODO app with add, list, and mark functions"
2. **Executor**: Writes `todo_app.py` with basic structure
3. **Evaluator**: Runs the code, tests features, scores it (e.g., 0.6)
4. **Summarizer**: "The app works but needs better error handling and persistence"

### Iteration 2:
1. **Planner**: Uses feedback from iteration 1 to improve
2. **Executor**: Adds JSON storage and error handling
3. **Evaluator**: Tests again, scores it (e.g., 0.87) ✅
4. **Summary**: "Successfully implemented all features!"

**Evolution stops** because score (0.87) ≥ target (0.85)!

---

## 🎯 Expected Results

A successful run should produce:

1. **Scores improving** across iterations:
   - Iteration 1: 0.4-0.6 (basic functionality)
   - Iteration 2: 0.7-0.8 (added features)
   - Iteration 3: 0.85+ (complete solution) ✅

2. **Working TODO app** that:
   - Doesn't crash on invalid input
   - Saves data between sessions
   - Has clear user interface
   - Implements all required features

---

## 🛠️ Common Issues & Solutions

### Issue: "API Key Not Found"

Error in logs: `Missing required API key. Set ANTHROPIC_API_KEY environment variable or provide in llm_config`

```bash
# Solution: Set environment variables
export ANTHROPIC_API_KEY="your-key-here"
export ANTHROPIC_BASE_URL="your-endpoint"

# Or add to task_config.yaml:
llm_config:
  api_key: "your-key"
  url: "your-endpoint"
```

### Issue: "Model shows input_tokens=0, output_tokens=0, work_dir is empty"

**Symptoms**:
- Logs show `[Claude Usage]: input_tokens=0, output_tokens=0` for every step
- Every iteration gets `score=0.0000`
- `executor/work_dir/` is always empty (shows `(empty directory)`)
- All subprocesses (Planner, Executor, Evaluator, Summarizer) complete in ~2-3 seconds

**Root cause**: The model name you specified doesn't exist at your API endpoint. The bundled Claude Code CLI launches and connects, but the model returns nothing because it's not recognized.

**Solution**:
1. **Verify the model name** is valid at your endpoint. Check with your API provider what models are available.
   ```yaml
   # task_config.yaml - make sure the model actually exists!
   llm_config:
     model: "anthropic/deepseek-v4-pro"  # NOT deepseek-v3.2 (may not exist)
   ```
2. **Test connectivity** — ensure `ANTHROPIC_BASE_URL` points to the correct endpoint:
   ```bash
   echo $ANTHROPIC_BASE_URL
   # Should be something like: https://api.deepseek.com/v1
   # Or: https://api.anthropic.com
   ```
3. **Check the logs** for more details:
   ```bash
   tail -f output-todo-list/logs/evolux.log
   ```

### Issue: "No code generated / Plan file not found"

**Symptoms**:
- Logs show `⚠️ Plan file not found, extracting from response`
- `executor/work_dir/` is empty after execution

This is typically a side effect of the model returning no actual content (see above). If `input_tokens=0`, none of the components actually produced output.

**If tokens ARE non-zero** but files are still missing:
- Check `planner/best_plan.md` — did planning succeed?
- Increase `max_turns: 30` in config
- Check logs: `output-todo-list/logs/evolux.log`

### Issue: "Score always low / always 0.0"

- First check if `input_tokens=0` in the logs — if so, the model isn't working (see above)
- Check `executor/evaluator_dir/best_evaluation.json` to see evaluation details
- Task might be unclear — make description more specific
- Increase `max_iterations` to give more chances

### Issue: "Can't find output / wrong directory structure"

The actual output structure uses **UUID-based task directories** and **numeric iteration directories**, not the `task_<timestamp>/iteration_N` format shown in older docs:

```bash
# Find the actual output
ls output-todo-list/
# You'll see: logs/  database/  6bb70103-27aa-49fd-862b-26a329500f15/  ...

# Browse a specific iteration
cd output-todo-list/<uuid>/<iteration_number>/
# e.g., output-todo-list/6bb70103-27aa-49fd-862b-26a329500f15/1/

# Directory structure:
# 1/
# ├── planner/
# │   ├── best_plan.md        # The agent's plan
# │   └── meta.json           # Token usage & status
# ├── executor/
# │   ├── work_dir/           # 🎯 YOUR CODE IS HERE
# │   └── evaluator_dir/
# │       └── best_evaluation.json
# └── summarizer/
#     └── best_summary.md      # What the agent learned
```

### Issue: "Running on WSL - no output / hangs"

If you're running in WSL and the process seems stuck or produces no output:
1. Make sure the `.venv` is created inside WSL (not on Windows filesystem), or use `uv venv .venv --python 3.12` from WSL
2. Ensure `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` are exported in your WSL shell
3. The bundled Claude Code CLI binary must be compatible with Linux/WSL — it should work if installed via `uv pip install -e .` in WSL

### Issue: "How to visualize results?"

Use the built-in visualizer to monitor progress in real-time:
```bash
# Start the visualizer (in a separate WSL terminal)
python agents/general_agent/visualizer/visualizer.py \
    --workspace ./output-todo-list \
    --port 8080

# Then open in browser: http://127.0.0.1:8080
```

The visualizer shows score evolution charts, iteration details, generated files with syntax highlighting, and evaluation results.

---

## 🎉 Next Steps

Congratulations on running your first General Agent example! Now try:

1. **Modify the task**: Edit `task_config.yaml` and add new requirements
   ```yaml
   task: |
     Create a TODO app that also supports:
     - Priority levels (High, Medium, Low)
     - Due dates
     - Categories/tags
   ```

2. **Try the next example**: [02_file_processor](../02_file_processor/) - Learn about skills and multi-file projects

3. **Read the tutorial**: [TUTORIAL.md](../../TUTORIAL.md) - Comprehensive guide covering all examples

---

## 📚 Key Takeaways

- ✅ General Agent uses **Plan-Execute-Summary** cycles to evolve code
- ✅ Each iteration improves on previous attempts
- ✅ Generated code is in `executor/work_dir/`
- ✅ Evolution stops when `score >= target_score`
- ✅ You can customize behavior via `task_config.yaml`

**Ready to learn more?** Head to [Example 02: File Processor](../02_file_processor/) to discover the power of custom skills! 🚀
