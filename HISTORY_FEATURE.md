# History Logging & Visualization Update

## Features Added

### 1. History Logging System
- Automatically logs completed tasks with:
  - Task name
  - Duration (in minutes)
  - Date and time of completion
  - Date only (for grouping)

- Data is stored in `task_stats.json` with structure:
  ```json
  {
    "history": [
      {
        "task": "Task Name",
        "duration_minutes": 25,
        "date": "2026-01-23 14:30:45",
        "date_only": "2026-01-23"
      }
    ],
    "task_totals": {
      "Task Name": 50
    }
  }
  ```

### 2. Graph Visualization
A new "View History" button opens a window with three tabs showing:

#### Timeline Tab
- Bar chart showing all completed tasks chronologically
- Each bar colored by task type
- Duration in minutes on the Y-axis
- Dates on the X-axis

#### Task Breakdown Tab
- Pie chart showing percentage of time spent on each task
- Visual comparison of task focus distribution
- Percentages and labels for each task

#### Daily Stats Tab
- Bar chart showing total focus time per day
- Green bars for easy visualization
- Helpful for tracking daily productivity trends

### 3. Data Storage
- History is automatically saved after each task completion
- Old format data is automatically migrated to new format
- Task totals are accumulated over time

## Installation

Make sure to install matplotlib if not already installed:
```bash
pip install -r requirements.txt
```

Or individually:
```bash
pip install matplotlib pygame
```

## Usage

1. Create and start tasks as usual
2. When a task cycle is completed, it's automatically logged
3. Click "View History" button to see your task history and graphs
4. Three different graph views help you understand your productivity patterns

## Technical Details

### Modified Files
- `init.py`: Added imports, new methods, and UI button

### New Methods in Pomodoro class
- `log_task_completion(task_name, duration_minutes)`: Logs a completed task
- `show_history_graph()`: Opens history visualization window
- `create_timeline_graph(parent)`: Creates bar chart timeline
- `create_task_breakdown_graph(parent)`: Creates pie chart of task distribution
- `create_daily_stats_graph(parent)`: Creates daily focus time chart

### Dependencies
- `matplotlib`: For creating interactive graphs
- `collections.defaultdict`: For grouping daily statistics
- `datetime`: For timestamps

## Example Workflow

1. Start with a task like "Pomodoro (25/5)"
2. Complete the full cycle (4 cycles with 25 min work + 5 min breaks)
3. The task is logged as 100 minutes (25 × 4)
4. Click "View History" to see:
   - Timeline showing your session
   - Pie chart (if multiple tasks completed)
   - Daily stats showing today's total focus time
