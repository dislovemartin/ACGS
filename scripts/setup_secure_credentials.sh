#!/bin/bash

# ACGS-PGP Secure Credential Setup Script
# This script helps set up secure credential management for the ACGS-PGP framework

set -e

echo "🔐 ACGS-PGP Secure Credential Setup"
echo "=================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if .env file exists
check_env_file() {
    if [ -f ".env" ]; then
        print_warning ".env file already exists. Backing up to .env.backup"
        cp .env .env.backup
    else
        print_status "Creating new .env file from template"
        cp .env.example .env
    fi
}

# Function to prompt for credential input
prompt_credential() {
    local var_name=$1
    local description=$2
    local current_value=$(grep "^${var_name}=" .env 2>/dev/null | cut -d'=' -f2- | tr -d '"' || echo "")
    
    echo
    print_header "Setting up: $description"
    echo "Environment variable: $var_name"
    
    if [ -n "$current_value" ] && [ "$current_value" != "your_${var_name,,}_here" ]; then
        echo "Current value: ${current_value:0:10}... (truncated)"
        read -p "Keep current value? (y/n): " keep_current
        if [ "$keep_current" = "y" ] || [ "$keep_current" = "Y" ]; then
            return
        fi
    fi
    
    read -s -p "Enter $description: " new_value
    echo
    
    if [ -n "$new_value" ]; then
        # Update .env file
        if grep -q "^${var_name}=" .env; then
            sed -i "s|^${var_name}=.*|${var_name}=\"${new_value}\"|" .env
        else
            echo "${var_name}=\"${new_value}\"" >> .env
        fi
        print_status "✓ $var_name updated"
    else
        print_warning "Skipped $var_name (empty value)"
    fi
}

# Function to setup MCP configuration
setup_mcp_config() {
    print_header "Setting up MCP Server Configuration"
    
    if [ ! -d ".kilocode" ]; then
        mkdir -p .kilocode
        print_status "Created .kilocode directory"
    fi
    
    if [ -f ".kilocode/mcp.json" ]; then
        print_warning "MCP configuration already exists. Backing up to mcp.json.backup"
        cp .kilocode/mcp.json .kilocode/mcp.json.backup
    fi
    
    if [ -f ".kilocode/mcp.json.template" ]; then
        # Use envsubst to substitute environment variables
        envsubst < .kilocode/mcp.json.template > .kilocode/mcp.json
        print_status "✓ MCP configuration created from template"
    else
        print_error "MCP template not found. Please ensure .kilocode/mcp.json.template exists"
        return 1
    fi
}

# Function to validate credentials
validate_credentials() {
    print_header "Validating Credentials"
    
    # Check if required environment variables are set
    local required_vars=("GITHUB_PERSONAL_ACCESS_TOKEN" "BRAVE_API_KEY" "POWER_API_KEY")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        local value=$(grep "^${var}=" .env 2>/dev/null | cut -d'=' -f2- | tr -d '"' || echo "")
        if [ -z "$value" ] || [ "$value" = "your_${var,,}_here" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        print_status "✓ All required credentials are configured"
    else
        print_warning "Missing or placeholder values for: ${missing_vars[*]}"
        echo "Please run this script again to configure missing credentials"
    fi
}

# Function to show security reminders
show_security_reminders() {
    print_header "Security Reminders"
    echo
    print_warning "IMPORTANT SECURITY NOTES:"
    echo "1. Never commit .env files to version control"
    echo "2. Regularly rotate your API keys and tokens"
    echo "3. Use least-privilege access for all credentials"
    echo "4. Monitor for unauthorized access to your accounts"
    echo "5. Keep this script and templates updated"
    echo
    print_status "For more information, see: docs/security/credential_management.md"
}

# Main execution
main() {
    print_header "Starting Secure Credential Setup"
    
    # Check if we're in the right directory
    if [ ! -f ".env.example" ]; then
        print_error "This script must be run from the ACGS-PGP root directory"
        exit 1
    fi
    
    # Setup environment file
    check_env_file
    
    # Prompt for credentials
    prompt_credential "GITHUB_PERSONAL_ACCESS_TOKEN" "GitHub Personal Access Token"
    prompt_credential "BRAVE_API_KEY" "Brave Search API Key"
    prompt_credential "POWER_API_KEY" "Power MCP Server API Key"
    
    # Setup MCP configuration
    setup_mcp_config
    
    # Validate setup
    validate_credentials
    
    # Show security reminders
    show_security_reminders
    
    print_status "✓ Credential setup complete!"
    echo
    print_status "Next steps:"
    echo "1. Test your MCP server configuration"
    echo "2. Review the security documentation"
    echo "3. Set up credential rotation schedule"
}

# Run main function
main "$@"
