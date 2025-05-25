# AlphaEvolve-ACGS Reproducibility Guide

## Overview
This guide provides comprehensive instructions for reproducing all experimental results reported in the AlphaEvolve-ACGS paper. The framework has been designed with reproducibility as a core principle, addressing the key challenges identified in the peer review process.

## Quick Start

### Prerequisites
- Python 3.9+ with pip
- Docker (recommended for consistent environments)
- Git LFS for large datasets
- 16GB RAM minimum, 32GB recommended
- CUDA-compatible GPU (optional, for accelerated evaluation)

### Installation Options

#### Option 1: Docker (Recommended)
```bash
# Pull pre-configured environment
docker pull solnai/alphaevolve-acgs:latest

# Run interactive container
docker run -it --gpus all -v $(pwd):/workspace solnai/alphaevolve-acgs:latest
```

#### Option 2: Local Installation
```bash
# Clone repository
git clone https://github.com/soln-ai/alphaevolve-acgs.git
cd alphaevolve-acgs

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

## Experimental Reproduction

### Core Evaluation (Domains 1-3)
Reproduce the main experimental results from Section 5:

```bash
# Run all core experiments (estimated time: 4-6 hours)
python scripts/run_core_evaluation.py --config configs/core_experiments.yaml

# Run individual domains
python scripts/run_domain_evaluation.py --domain arithmetic --trials 50
python scripts/run_domain_evaluation.py --domain symbolic_regression --trials 50
python scripts/run_domain_evaluation.py --domain neural_architecture --trials 50
```

### Extended Evaluation (Domains 4-5)
Reproduce the extended evaluation results:

```bash
# Financial portfolio optimization
python scripts/run_domain_evaluation.py --domain financial_portfolio --trials 50 --generations 200

# Autonomous vehicle path planning
python scripts/run_domain_evaluation.py --domain autonomous_vehicle --trials 50 --generations 150
```

### Bias Detection Evaluation
Reproduce bias detection and fairness analysis:

```bash
# Run bias detection evaluation
python scripts/evaluate_bias_detection.py --config configs/bias_evaluation.yaml

# Generate fairness metrics
python scripts/compute_fairness_metrics.py --domains all --output results/fairness_analysis.json
```

## Deterministic Reproducibility

### LLM Reproducibility
To address non-deterministic LLM behavior, we provide multiple options:

#### Option 1: Cached Results (Fastest)
```bash
# Use pre-computed LLM responses
export ALPHAEVOLVE_USE_CACHE=true
python scripts/run_evaluation.py --use-cached-llm-responses
```

#### Option 2: Local Fine-tuned Model
```bash
# Download deterministic local model
python scripts/download_local_model.py --model alphaevolve-policy-synthesis-v1

# Run with local model
export ALPHAEVOLVE_LLM_BACKEND=local
python scripts/run_evaluation.py --llm-model local/alphaevolve-policy-synthesis-v1
```

#### Option 3: Fixed Seed GPT-4
```bash
# Use GPT-4 with fixed seed (requires API key)
export OPENAI_API_KEY=your_api_key_here
export ALPHAEVOLVE_LLM_SEED=42
python scripts/run_evaluation.py --llm-model gpt-4-turbo --seed 42
```

### Statistical Analysis Reproduction
```bash
# Reproduce all statistical tests and visualizations
python scripts/reproduce_statistics.py --input results/ --output reproduced_results/

# Generate paper figures
python scripts/generate_figures.py --config configs/figure_generation.yaml
```

## Data Availability

### Evaluation Datasets
All datasets used in evaluation are available in the `data/` directory:

- `data/arithmetic/`: Arithmetic expression evaluation datasets
- `data/symbolic_regression/`: Symbolic regression benchmark problems
- `data/neural_architecture/`: Neural architecture search spaces and constraints
- `data/financial_portfolio/`: Anonymized financial portfolio optimization scenarios
- `data/autonomous_vehicle/`: Synthetic autonomous vehicle path planning scenarios

### Synthetic Data Generation
Generate fresh synthetic datasets for validation:

```bash
# Generate all synthetic datasets
python scripts/generate_synthetic_data.py --config configs/data_generation.yaml

# Generate specific domain data
python scripts/generate_domain_data.py --domain financial_portfolio --size 1000
```

## Environment Specifications

### Python Dependencies
Core dependencies with exact versions:
```
torch==2.1.0
transformers==4.35.0
openai==1.3.0
rego-python==0.2.1
numpy==1.24.3
scipy==1.11.3
pandas==2.1.1
scikit-learn==1.3.0
matplotlib==3.7.2
seaborn==0.12.2
```

### System Requirements
- Operating System: Ubuntu 20.04+ (tested), macOS 12+ (compatible), Windows 10+ (compatible)
- Python: 3.9.0 - 3.11.x
- Memory: 16GB RAM minimum for full evaluation
- Storage: 10GB free space for datasets and results
- Network: Internet connection required for LLM API calls (unless using local models)

## Validation and Testing

### Unit Tests
```bash
# Run comprehensive test suite
python -m pytest tests/ -v --cov=alphaevolve_acgs

# Run specific test categories
python -m pytest tests/test_bias_detection.py -v
python -m pytest tests/test_constitutional_governance.py -v
```

### Integration Tests
```bash
# Test end-to-end pipeline
python scripts/integration_test.py --quick

# Full integration test (30+ minutes)
python scripts/integration_test.py --full
```

## Troubleshooting

### Common Issues

1. **LLM API Rate Limits**
   ```bash
   # Use rate limiting
   export ALPHAEVOLVE_API_RATE_LIMIT=10  # requests per minute
   ```

2. **Memory Issues**
   ```bash
   # Reduce batch sizes
   export ALPHAEVOLVE_BATCH_SIZE=16
   ```

3. **CUDA Out of Memory**
   ```bash
   # Use CPU-only mode
   export ALPHAEVOLVE_DEVICE=cpu
   ```

### Support
- GitHub Issues: https://github.com/soln-ai/alphaevolve-acgs/issues
- Documentation: https://alphaevolve-acgs.readthedocs.io
- Email: support@soln.ai

## Citation
If you use this framework in your research, please cite:
```bibtex
@article{alphaevolve2024,
  title={AlphaEvolve-ACGS Integration System: A Framework for Constitutionally Governed Evolutionary Computation},
  author={[Authors]},
  journal={[Journal]},
  year={2024},
  doi={[DOI]}
}
```
