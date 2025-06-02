# Darwin Gödel Machine - Best Software Engineering Agent

🧬 A self-improving AI system for software engineering tasks based on the theoretical foundation of the Darwin Gödel Machine from research paper arXiv:2505.22954v1.

## Overview

The Darwin Gödel Machine (DGM) is a self-referential, self-improving AI system that iteratively modifies its own approach to become better at coding tasks. This implementation combines the theoretical DGM concepts with practical improvements discovered through iterative evolution.

### Key Features

- **🔄 Self-Improving Evolution**: Iteratively improves solutions through multiple attempts
- **🧪 Multi-Strategy Optimization**: Uses different improvement strategies based on test results
- **🌐 Polyglot Programming**: Supports Python, JavaScript, Rust, Go, C++, and Java
- **📊 Detailed Analytics**: Comprehensive test result analysis and progress tracking
- **🔧 Enhanced Editing**: Advanced editing capabilities with undo, string replacement, and insertion
- **🏛️ Solution Archive**: Maintains a growing archive of successful solutions
- **🎯 Performance Thresholds**: Configurable success criteria and optimization targets
- **🔌 API Integration**: Optional integration with Requesty API system

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Darwin Gödel Machine                    │
├─────────────────────────────────────────────────────────────┤
│  Evolution Loop:                                            │
│  1. Problem Analysis                                        │
│  2. Strategy Selection                                      │
│  3. Solution Generation                                     │
│  4. Test Execution                                          │
│  5. Result Analysis                                         │
│  6. Archive Update                                          │
│  7. Next Iteration                                          │
├─────────────────────────────────────────────────────────────┤
│  Components:                                                │
│  • Enhanced Edit Tool                                       │
│  • Test Result Analyzer                                     │
│  • Strategy Selector                                        │
│  • Solution Archive                                         │
│  • Performance Tracker                                      │
└─────────────────────────────────────────────────────────────┘
```

## Installation & Setup

### Prerequisites

```bash
# Python 3.8+
pip install -r requirements.txt

# Git repository with test suite
# Working directory with appropriate language toolchain
```

### Basic Installation

```bash
# Clone or download the DGM files
cp dgm_best_swe_agent.py /path/to/your/project/
cp dgm_config.json /path/to/your/project/

# Optional: Install Requesty API for enhanced capabilities
pip install -r requirements-requesty.txt
```

## Usage

### Basic Usage

```bash
python dgm_best_swe_agent.py \
    --problem_statement "Fix the failing unit tests in the authentication module" \
    --git_dir /path/to/repo \
    --base_commit abc123def \
    --chat_history_file ./dgm_evolution.md \
    --language python \
    --max_attempts 5
```

### Advanced Usage with Configuration

```bash
python dgm_best_swe_agent.py \
    --problem_statement "Implement OAuth2 authentication with JWT tokens" \
    --git_dir /path/to/repo \
    --base_commit abc123def \
    --chat_history_file ./dgm_evolution.md \
    --language python \
    --config_file dgm_config.json \
    --enable_requesty \
    --outdir ./dgm_results/
```

### Configuration Options

The `dgm_config.json` file provides comprehensive configuration:

```json
{
  "max_attempts": 5,
  "max_tokens": 4000,
  "temperature": 0.7,
  "enable_self_improvement": true,
  "enable_requesty_integration": true,
  "archive_solutions": true,
  "use_novelty_selection": true,
  "performance_threshold": 0.85
}
```

## Improvement Strategies

The DGM employs different strategies based on the current state:

### 1. **Initial Analysis** 
- First attempt at understanding the problem
- Comprehensive code analysis
- Test suite exploration

### 2. **Error Resolution**
- Focus on runtime errors and exceptions
- Syntax and compilation fixes
- Dependency resolution

### 3. **Test-Driven Fix**
- Address specific test failures
- Implement missing functionality
- Fix assertion errors

### 4. **Incremental Improvement**
- Build upon previous successful changes
- Optimize existing solutions
- Enhance code quality

### 5. **Fine-Tuning**
- Minor adjustments for edge cases
- Performance optimizations
- Code style improvements

### 6. **Comprehensive Refactor**
- Major architectural changes
- Complete reimplementation
- Design pattern application

## Language Support

### Python
- **Test Framework**: pytest
- **Features**: Full support for all strategies
- **Specializations**: Django, Flask, FastAPI patterns

### JavaScript/Node.js
- **Test Framework**: npm test, Jest, Mocha
- **Features**: ES6+, TypeScript support
- **Specializations**: React, Vue, Express patterns

### Rust
- **Test Framework**: cargo test
- **Features**: Memory safety analysis
- **Specializations**: Performance-critical optimizations

### Go
- **Test Framework**: go test
- **Features**: Concurrency patterns
- **Specializations**: Microservices, CLI tools

### C++
- **Test Framework**: CMake + CTest
- **Features**: Memory management, performance
- **Specializations**: Systems programming

### Java
- **Test Framework**: Gradle test
- **Features**: OOP patterns, Spring Boot
- **Specializations**: Enterprise applications

## Enhanced Editing Capabilities

The DGM includes advanced editing tools beyond basic file operations:

### String Replacement
```python
# Replace specific strings with precision
edit_tool.str_replace(path, "old_function_name", "new_function_name")
```

### Line Insertion
```python
# Insert code at specific line numbers
edit_tool.insert_text(path, line_number=42, text="new_code_line")
```

### Undo Operations
```python
# Undo the last edit operation
edit_tool.undo_edit(path)
```

### View with Line Ranges
```python
# View specific portions of files
edit_tool.view_path(path, view_range=[10, 50])
```

## Results and Analytics

### Output Files

After execution, the DGM generates several output files:

- **`dgm_model_patch.diff`**: Final solution patch
- **`dgm_solution_metadata.json`**: Solution analytics
- **`dgm_evolution.md`**: Detailed evolution log

### Solution Metadata Example

```json
{
  "attempt_number": 3,
  "test_success": true,
  "test_stats": {
    "passed": 15,
    "failed": 0,
    "errors": 0,
    "total": 15,
    "execution_time": 2.34
  },
  "improvement_strategy": "incremental_improvement",
  "generation": 1,
  "archive_size": 8
}
```

## Integration with Requesty API

For enhanced capabilities, integrate with the Requesty API system:

```python
from requesty_example import RequestyAPI

# Enable during initialization
dgm = DarwinGodelMachine(
    problem_statement=problem,
    git_tempdir=repo_path,
    base_commit=commit_hash,
    requesty_api=RequestyAPI()
)
```

## Performance Metrics

The DGM tracks comprehensive performance metrics:

### Test Metrics
- Pass rate percentage
- Test execution time
- Error categorization
- Regression detection

### Evolution Metrics
- Improvement rate per attempt
- Strategy effectiveness
- Archive growth
- Convergence speed

### Quality Metrics
- Code complexity reduction
- Test coverage improvement
- Performance optimizations
- Best practice compliance

## Best Practices

### 1. Problem Statement Quality
- Be specific and measurable
- Include acceptance criteria
- Provide context and constraints

### 2. Repository Preparation
- Ensure clean git state
- Verify test suite functionality
- Check dependency installation

### 3. Configuration Tuning
- Adjust `max_attempts` based on complexity
- Set appropriate `performance_threshold`
- Configure language-specific parameters

### 4. Monitoring Evolution
- Review chat history logs
- Analyze attempt progression
- Monitor archive growth

## Troubleshooting

### Common Issues

**1. Git Repository Issues**
```bash
# Ensure clean repository state
git status
git reset --hard HEAD

# Verify base commit exists
git log --oneline | head -10
```

**2. Test Framework Problems**
```bash
# Verify test commands work manually
cd /path/to/repo
python -m pytest  # For Python
npm test          # For JavaScript
cargo test        # For Rust
```

**3. Permission Issues**
```bash
# Ensure write permissions
chmod +w /path/to/repo
ls -la /path/to/repo
```

### Debug Mode

Enable detailed debugging:

```bash
export DGM_DEBUG=1
export DGM_LOG_LEVEL=DEBUG
python dgm_best_swe_agent.py [args...]
```

## Research Foundation

This implementation is based on the research paper:

**"Darwin Gödel Machine"** (arXiv:2505.22954v1)

Key concepts implemented:
- Self-referential self-improvement
- Open-ended exploration with solution archives
- Empirical validation through coding benchmarks
- Parent selection algorithms based on performance and novelty
- Tool use capabilities (enhanced editing tools)

## Contributing

### Adding New Languages

1. Add test commands to `TEST_COMMANDS` dictionary
2. Implement language-specific test parsing in `extract_test_details()`
3. Add language configuration to `dgm_config.json`
4. Test with representative repositories

### Enhancing Strategies

1. Add new strategy to `select_improvement_strategy()`
2. Implement strategy-specific instruction generation
3. Update configuration options
4. Document strategy behavior

### Extending API Integration

1. Create new API adapter class
2. Implement required interface methods
3. Add configuration options
4. Test integration thoroughly

## License

This implementation follows the research paper's contributions while adding practical enhancements for real-world software engineering tasks.

## Citation

If you use this implementation in research, please cite:

```bibtex
@article{darwin_godel_machine_2024,
  title={Darwin Gödel Machine},
  author={[Authors from arXiv:2505.22954v1]},
  journal={arXiv preprint arXiv:2505.22954},
  year={2024}
}
```

---

🧬 **Happy Evolving!** - The Darwin Gödel Machine Team