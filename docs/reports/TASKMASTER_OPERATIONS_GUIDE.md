# TaskMaster Operations Guide - ACGS-master Project

## 🎯 Overview

This guide provides practical instructions for working with TaskMaster AI in the ACGS-master project. TaskMaster is configured and has successfully managed 19 major tasks to completion.

## 📁 TaskMaster File Structure

```
.taskmaster/
├── config.json              # TaskMaster configuration
├── tasks/
│   ├── tasks.json           # Main task database
│   ├── tasks.json.bak       # Backup of task database
│   ├── task_001.txt         # Individual task files
│   ├── task_002.txt         # ...
│   └── task_019.txt         # Latest task
├── docs/
│   ├── alphaevolve-acgs-integration.prd  # Product Requirements Document
│   └── prd.txt              # PRD text version
└── templates/
    ├── debug_mab_template_selection.py
    ├── example_prd.txt
    └── seed_mab_prompt_templates.py
```

## 🔧 TaskMaster Commands & Operations

### **Basic Task Viewing**

```bash
# View all tasks summary
cat .taskmaster/tasks/tasks.json | jq '.tasks[] | {id, title, status, priority}' | head -20

# View specific task by ID
cat .taskmaster/tasks/tasks.json | jq '.tasks[] | select(.id == 1)'

# View task with subtasks
cat .taskmaster/tasks/tasks.json | jq '.tasks[] | select(.id == 2) | {id, title, status, subtasks}'

# Count tasks by status
echo "Total tasks: $(cat .taskmaster/tasks/tasks.json | jq '.tasks | length')"
echo "Completed: $(cat .taskmaster/tasks/tasks.json | jq '.tasks | map(select(.status == "done")) | length')"
echo "In Progress: $(cat .taskmaster/tasks/tasks.json | jq '.tasks | map(select(.status == "in-progress")) | length')"
echo "Pending: $(cat .taskmaster/tasks/tasks.json | jq '.tasks | map(select(.status == "pending")) | length')"
```

### **Task Analysis**

```bash
# View high priority tasks
cat .taskmaster/tasks/tasks.json | jq '.tasks[] | select(.priority == "high") | {id, title, status}'

# View tasks with dependencies
cat .taskmaster/tasks/tasks.json | jq '.tasks[] | select(.dependencies | length > 0) | {id, title, dependencies}'

# View tasks by completion status
cat .taskmaster/tasks/tasks.json | jq '.tasks | group_by(.status) | map({status: .[0].status, count: length})'

# Find tasks with subtasks
cat .taskmaster/tasks/tasks.json | jq '.tasks[] | select(.subtasks | length > 0) | {id, title, subtask_count: (.subtasks | length)}'
```

### **Project Metrics**

```bash
# View project metadata
cat .taskmaster/tasks/tasks.json | jq '.metadata'

# Calculate completion percentage
echo "Completion: $(echo "scale=1; $(cat .taskmaster/tasks/tasks.json | jq '.tasks | map(select(.status == "done")) | length') * 100 / $(cat .taskmaster/tasks/tasks.json | jq '.tasks | length')" | bc)%"

# View task distribution by priority
cat .taskmaster/tasks/tasks.json | jq '.tasks | group_by(.priority) | map({priority: .[0].priority, count: length})'
```

## 📊 TaskMaster Configuration

### **Current Configuration**
```json
{
  "models": {
    "main": "google/gemini-2.5-pro-preview-05-06",
    "research": "google/gemini-2.5-pro-preview-05-06", 
    "fallback": "google/gemini-2.5-flash-preview-05-20"
  },
  "global": {
    "projectName": "Task Master",
    "defaultSubtasks": 5,
    "defaultPriority": "medium"
  }
}
```

### **Modifying Configuration**
```bash
# Backup current config
cp .taskmaster/config.json .taskmaster/config.json.bak

# Edit configuration (use your preferred editor)
nano .taskmaster/config.json

# Validate JSON syntax
cat .taskmaster/config.json | jq '.' > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```

## 🔄 Task Management Operations

### **Creating New Tasks** (Manual Process)

Since the TaskMaster CLI isn't directly available, you can manually add tasks:

```bash
# Backup current tasks
cp .taskmaster/tasks/tasks.json .taskmaster/tasks/tasks.json.bak

# Add new task (example)
cat .taskmaster/tasks/tasks.json | jq '.tasks += [{
  "id": 20,
  "title": "New Task Title",
  "description": "Task description",
  "status": "pending",
  "priority": "medium",
  "dependencies": [],
  "details": "Detailed task information",
  "testStrategy": "Success criteria",
  "subtasks": []
}]' > .taskmaster/tasks/tasks_new.json

# Verify and replace
cat .taskmaster/tasks/tasks_new.json | jq '.' > /dev/null && mv .taskmaster/tasks/tasks_new.json .taskmaster/tasks/tasks.json
```

### **Updating Task Status**

```bash
# Update task status (example: mark task 20 as in-progress)
cat .taskmaster/tasks/tasks.json | jq '(.tasks[] | select(.id == 20) | .status) = "in-progress"' > .taskmaster/tasks/tasks_updated.json
mv .taskmaster/tasks/tasks_updated.json .taskmaster/tasks/tasks.json

# Update task priority
cat .taskmaster/tasks/tasks.json | jq '(.tasks[] | select(.id == 20) | .priority) = "high"' > .taskmaster/tasks/tasks_updated.json
mv .taskmaster/tasks/tasks_updated.json .taskmaster/tasks/tasks.json
```

### **Adding Subtasks**

```bash
# Add subtask to existing task
cat .taskmaster/tasks/tasks.json | jq '(.tasks[] | select(.id == 20) | .subtasks) += [{
  "id": "20.1",
  "title": "Subtask Title",
  "description": "Subtask description",
  "status": "pending",
  "priority": "medium",
  "dependencies": []
}]' > .taskmaster/tasks/tasks_updated.json
mv .taskmaster/tasks/tasks_updated.json .taskmaster/tasks/tasks.json
```

## 📈 Monitoring & Reporting

### **Generate Task Report**

```bash
# Create comprehensive task report
cat > task_report.md << 'EOF'
# TaskMaster Task Report

## Summary
- Total Tasks: $(cat .taskmaster/tasks/tasks.json | jq '.tasks | length')
- Completed: $(cat .taskmaster/tasks/tasks.json | jq '.tasks | map(select(.status == "done")) | length')
- In Progress: $(cat .taskmaster/tasks/tasks.json | jq '.tasks | map(select(.status == "in-progress")) | length')
- Pending: $(cat .taskmaster/tasks/tasks.json | jq '.tasks | map(select(.status == "pending")) | length')

## High Priority Tasks
$(cat .taskmaster/tasks/tasks.json | jq -r '.tasks[] | select(.priority == "high") | "- Task \(.id): \(.title) (\(.status))"')

## Recent Tasks (Last 5)
$(cat .taskmaster/tasks/tasks.json | jq -r '.tasks[-5:] | .[] | "- Task \(.id): \(.title) (\(.status))"')
EOF

# Execute the report generation
eval "cat > task_report.md << 'EOF'
$(cat task_report.md)
EOF"
```

### **Task Dependency Analysis**

```bash
# Find tasks with unmet dependencies
cat .taskmaster/tasks/tasks.json | jq -r '
.tasks[] | 
select(.dependencies | length > 0) | 
select(.status != "done") |
"Task \(.id): \(.title) - Depends on: \(.dependencies | join(", "))"'

# Find circular dependencies (basic check)
cat .taskmaster/tasks/tasks.json | jq -r '
.tasks[] | 
select(.dependencies | length > 0) |
select(.dependencies[] as $dep | .id == $dep) |
"Circular dependency detected in Task \(.id)"'
```

## 🔧 Maintenance Operations

### **Backup TaskMaster Data**

```bash
# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p backups/taskmaster_$TIMESTAMP
cp -r .taskmaster/* backups/taskmaster_$TIMESTAMP/
echo "Backup created: backups/taskmaster_$TIMESTAMP"

# Compress backup
tar -czf backups/taskmaster_$TIMESTAMP.tar.gz -C backups taskmaster_$TIMESTAMP
rm -rf backups/taskmaster_$TIMESTAMP
echo "Compressed backup: backups/taskmaster_$TIMESTAMP.tar.gz"
```

### **Restore TaskMaster Data**

```bash
# List available backups
ls -la backups/taskmaster_*.tar.gz

# Restore from backup (example)
BACKUP_FILE="backups/taskmaster_20241228_120000.tar.gz"
tar -xzf $BACKUP_FILE -C backups/
cp -r backups/taskmaster_20241228_120000/* .taskmaster/
echo "Restored from: $BACKUP_FILE"
```

### **Validate TaskMaster Data**

```bash
# Validate JSON syntax
cat .taskmaster/config.json | jq '.' > /dev/null && echo "Config JSON valid" || echo "Config JSON invalid"
cat .taskmaster/tasks/tasks.json | jq '.' > /dev/null && echo "Tasks JSON valid" || echo "Tasks JSON invalid"

# Check for duplicate task IDs
cat .taskmaster/tasks/tasks.json | jq -r '.tasks[].id' | sort | uniq -d | while read id; do
  echo "Duplicate task ID found: $id"
done

# Validate task dependencies
cat .taskmaster/tasks/tasks.json | jq -r '
.tasks[] as $task |
$task.dependencies[] as $dep |
if ([.tasks[].id] | index($dep) | not) then
  "Task \($task.id) has invalid dependency: \($dep)"
else empty end'
```

## 🚀 Integration with Development Workflow

### **Git Integration**

```bash
# Add TaskMaster files to git
git add .taskmaster/
git commit -m "Update TaskMaster configuration and tasks"

# Create task-specific branches
TASK_ID=20
git checkout -b "task-$TASK_ID-$(cat .taskmaster/tasks/tasks.json | jq -r ".tasks[] | select(.id == $TASK_ID) | .title" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"
```

### **CI/CD Integration**

```bash
# Add TaskMaster validation to CI
cat > .github/workflows/taskmaster-validation.yml << 'EOF'
name: TaskMaster Validation
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate TaskMaster JSON
        run: |
          jq '.' .taskmaster/config.json > /dev/null
          jq '.' .taskmaster/tasks/tasks.json > /dev/null
          echo "TaskMaster JSON files are valid"
EOF
```

## 📚 Best Practices

### **Task Management**
1. **Regular Backups**: Backup TaskMaster data before major changes
2. **Atomic Updates**: Make one change at a time to avoid corruption
3. **Validation**: Always validate JSON after manual edits
4. **Documentation**: Keep task descriptions detailed and current

### **Development Workflow**
1. **Branch per Task**: Create git branches for major tasks
2. **Status Updates**: Regularly update task status as work progresses
3. **Dependency Tracking**: Ensure dependencies are accurate and up-to-date
4. **Completion Criteria**: Define clear success criteria for each task

### **Monitoring**
1. **Regular Reviews**: Weekly review of task progress
2. **Metrics Tracking**: Monitor completion rates and bottlenecks
3. **Dependency Analysis**: Check for blocking dependencies
4. **Performance Metrics**: Track time to completion for similar tasks

## 🎯 Next Steps

1. **Review Current Status**: All 19 tasks are complete - validate production readiness
2. **Plan Maintenance Tasks**: Create new tasks for ongoing maintenance
3. **Monitor Performance**: Set up monitoring for production systems
4. **Document Operations**: Create operational runbooks for ongoing management

TaskMaster has successfully guided the ACGS-master project to completion. Use this guide to maintain and extend the system as needed.
