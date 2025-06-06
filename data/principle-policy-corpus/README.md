# Policy Corpus Processor

This project collects, parses, and normalizes policies from various sources into a consistent format.

## Project Structure

```
principle-policy-corpus/
├── opa-library/           # Open Policy Agent library
├── gatekeeper-library/    # OPA Gatekeeper library
├── azure-policy/         # Azure built-in policies
├── Community-Policy/     # Azure community policies
├── aws-iam-examples/     # AWS IAM policy examples (manually downloaded)
├── nist-oscal-profiles/  # NIST OSCAL profiles (manually downloaded)
├── scripts/             # Python scripts for processing
│   └── parse_policies.py # Main parser script
└── output/               # Output directory for processed policies
```

## Setup

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the parser script:
   ```bash
   python scripts/parse_policies.py
   ```

2. The script will:
   - Scan all policy files in the source directories
   - Parse and normalize the policies
   - Save the results in the `output/` directory as JSONL files

## Adding New Policy Sources

1. Add the new policy files to their respective directories
2. Update the `sources` list in `parse_policies.py` if needed
3. Re-run the parser script

## Output Format

Each policy is saved in the following format:

```json
{
  "principle_id": "P-001",
  "principle_text": "Policy description...",
  "policy_code": "...policy content...",
  "source_repo": "Source Name",
  "source_path": "relative/path/to/file",
  "metadata": {
    "domain": "Azure|AWS|NIST|Kubernetes|Generic",
    "framework": "JSON|YAML|Rego",
    "date_collected": "YYYY-MM-DD"
  },
  "alignment_notes": ""
}
```

## Managing NIST OSCAL Profiles

The `nist-oscal-profiles` directory contains official OSCAL example
profiles from NIST and is over 100 MB. To reduce repository size, store
these files in [Git LFS](https://git-lfs.github.com/) or host them on an
external service (e.g., S3).

If the directory is missing, download the profiles manually:

```bash
git clone https://github.com/usnistgov/oscal-content.git tmp-oscal
mkdir -p nist-oscal-profiles
cp -r tmp-oscal/examples/* nist-oscal-profiles/
rm -rf tmp-oscal
```

Ensure the profiles are located at
`data/principle-policy-corpus/nist-oscal-profiles` before running the
parser.
