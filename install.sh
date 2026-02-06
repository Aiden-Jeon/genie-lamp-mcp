#!/bin/bash
#
# Installation script for Databricks Genie MCP Server
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Interactive menu with arrow key navigation
# Usage: selected=$(select_option "Prompt" "option1" "option2" "option3")
select_option() {
    local prompt="$1"
    shift
    local options=("$@")
    local selected=0
    local key=""

    # Hide cursor
    tput civis >&2

    # Initial draw (to stderr so it's visible when using command substitution)
    echo -e "${BLUE}$prompt${NC}" >&2
    echo "" >&2
    for i in "${!options[@]}"; do
        if [ $i -eq $selected ]; then
            echo -e "  ${GREEN}▶${NC} ${YELLOW}${options[$i]}${NC}" >&2
        else
            echo -e "    ${options[$i]}" >&2
        fi
    done

    while true; do
        # Read key from terminal
        read -rsn1 key </dev/tty

        case "$key" in
            $'\x1b')  # ESC sequence
                read -rsn2 key </dev/tty
                case "$key" in
                    '[A')  # Up arrow
                        ((selected--))
                        if [ $selected -lt 0 ]; then
                            selected=$((${#options[@]} - 1))
                        fi
                        ;;
                    '[B')  # Down arrow
                        ((selected++))
                        if [ $selected -ge ${#options[@]} ]; then
                            selected=0
                        fi
                        ;;
                    *)
                        continue
                        ;;
                esac

                # Redraw menu (to stderr)
                # Move cursor up to start of options
                for i in $(seq 1 ${#options[@]}); do
                    tput cuu1 >&2
                done

                # Redraw all options
                for i in "${!options[@]}"; do
                    tput el >&2
                    if [ $i -eq $selected ]; then
                        echo -e "  ${GREEN}▶${NC} ${YELLOW}${options[$i]}${NC}" >&2
                    else
                        echo -e "    ${options[$i]}" >&2
                    fi
                done
                ;;
            '')  # Enter
                break
                ;;
        esac
    done

    # Show cursor
    tput cnorm >&2

    echo "" >&2
    # Return selected index to stdout (this is what gets captured by $())
    echo "$selected"
}

# Check if Python is installed and meets version requirement
check_python() {
    print_header "Checking Python Installation"

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Please install Python 3.10 or higher from https://www.python.org/"
        exit 1
    fi

    # Get Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.10"

    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
        print_error "Python version $PYTHON_VERSION is installed, but 3.10+ is required"
        exit 1
    fi

    print_success "Python $PYTHON_VERSION found"
}

# Create virtual environment
create_venv() {
    print_header "Creating Virtual Environment"

    if [ -d ".venv" ]; then
        print_warning "Virtual environment already exists"
        echo ""

        local venv_options=(
            "Use existing virtual environment"
            "Recreate virtual environment"
        )

        local venv_choice=$(select_option "What would you like to do? (use ↑↓ arrows, Enter to select):" "${venv_options[@]}")

        if [ "$venv_choice" -eq 1 ]; then
            print_info "Removing existing virtual environment..."
            rm -rf .venv
        else
            print_info "Using existing virtual environment"
            return 0
        fi
    fi

    python3 -m venv .venv
    print_success "Virtual environment created at .venv/"
}

# Activate virtual environment
activate_venv() {
    print_info "Activating virtual environment..."
    source .venv/bin/activate
    print_success "Virtual environment activated"
}

# Upgrade pip
upgrade_pip() {
    print_header "Upgrading pip"
    python -m pip install --upgrade pip
    print_success "pip upgraded"
}

# Install package
install_package() {
    print_header "Installing Genie MCP Server"
    echo ""

    local install_options=(
        "Production only"
        "Production + Development dependencies"
    )

    local install_choice=$(select_option "Select installation type (use ↑↓ arrows, Enter to select):" "${install_options[@]}")

    if [ "$install_choice" -eq 1 ]; then
        print_info "Installing package with development dependencies..."
        pip install -e ".[dev]"
        INSTALL_TYPE="with development dependencies"
    else
        print_info "Installing package..."
        pip install -e .
        INSTALL_TYPE="(production only)"
    fi

    print_success "Package installed $INSTALL_TYPE"
}

# Check if Databricks CLI is installed
check_databricks_cli() {
    if command -v databricks &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Get Databricks profiles as array
get_databricks_profiles() {
    if check_databricks_cli; then
        databricks auth profiles 2>/dev/null | grep -v "^$" || echo ""
    else
        echo ""
    fi
}

# Get host from Databricks CLI profile
get_host_from_profile() {
    local profile=$1
    if check_databricks_cli && [ -n "$profile" ]; then
        databricks auth env --profile "$profile" 2>/dev/null | grep DATABRICKS_HOST | cut -d'=' -f2 | tr -d '"' || echo ""
    else
        echo ""
    fi
}

# Get profile details
get_profile_details() {
    local profile=$1
    if check_databricks_cli && [ -n "$profile" ]; then
        local host=$(get_host_from_profile "$profile")
        local auth_type=$(databricks auth env --profile "$profile" 2>/dev/null | grep DATABRICKS_AUTH_TYPE | cut -d'=' -f2 | tr -d '"' || echo "unknown")
        echo "$host|$auth_type"
    else
        echo "|"
    fi
}

# Interactive profile selection
select_databricks_profile() {
    local profiles_output=$(get_databricks_profiles)

    if [ -z "$profiles_output" ]; then
        echo ""
        return 1
    fi

    # Convert profiles to array
    local -a profiles=()
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            profiles+=("$line")
        fi
    done <<< "$profiles_output"

    if [ ${#profiles[@]} -eq 0 ]; then
        echo ""
        return 1
    fi

    # Build display options with workspace details
    local -a display_options=()
    local -a profile_hosts=()

    for profile in "${profiles[@]}"; do
        local details=$(get_profile_details "$profile")
        local host=$(echo "$details" | cut -d'|' -f1)
        local auth_type=$(echo "$details" | cut -d'|' -f2)

        profile_hosts+=("$host")

        if [ -n "$host" ]; then
            display_options+=("$(printf '%-20s %s (%s)' "$profile" "$host" "$auth_type")")
        else
            display_options+=("$(printf '%-20s (not configured)' "$profile")")
        fi
    done

    # Add skip option
    display_options+=("Skip profile selection")

    echo ""
    local profile_choice=$(select_option "Select Databricks profile (use ↑↓ arrows, Enter to select):" "${display_options[@]}")

    # Check if skip was selected
    if [ "$profile_choice" -eq ${#profiles[@]} ]; then
        echo ""
        return 1
    fi

    # Return selected profile name and host
    local selected_profile="${profiles[$profile_choice]}"
    local selected_host="${profile_hosts[$profile_choice]}"

    echo "$selected_profile|$selected_host"
    return 0
}

# Setup environment file
setup_env() {
    print_header "Setting up Environment Configuration"

    if [ -f ".env" ]; then
        print_warning ".env file already exists"
        read -p "Do you want to reconfigure it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Keeping existing .env file"
            return 0
        fi
    fi

    echo ""
    print_info "This will configure your Databricks connection settings"
    echo ""

    # Check for Databricks CLI
    local use_cli_auth=false
    local databricks_host=""
    local auth_method=""

    if check_databricks_cli; then
        print_success "Databricks CLI detected"
        echo ""

        local auth_options=(
            "Use Databricks CLI authentication (recommended)"
            "Use Personal Access Token (PAT)"
            "Use OAuth M2M Service Principal"
        )

        local auth_choice=$(select_option "Select authentication method (use ↑↓ arrows, Enter to select):" "${auth_options[@]}")
        auth_choice=$((auth_choice + 1))  # Convert 0-based to 1-based

        case $auth_choice in
            1)
                use_cli_auth=true
                auth_method="CLI"
                print_success "Using Databricks CLI authentication"

                # Interactive profile selection
                local selection=$(select_databricks_profile)
                if [ $? -eq 0 ] && [ -n "$selection" ]; then
                    local selected_profile=$(echo "$selection" | cut -d'|' -f1)
                    local selected_host=$(echo "$selection" | cut -d'|' -f2)

                    print_success "Selected profile: $selected_profile"

                    if [ -n "$selected_host" ]; then
                        databricks_host="$selected_host"
                        print_success "Using workspace: $databricks_host"
                    else
                        print_warning "Profile has no configured host"
                    fi

                    # Store profile name for reference
                    SELECTED_PROFILE="$selected_profile"
                fi
                ;;
            2)
                auth_method="PAT"
                ;;
            3)
                auth_method="OAuth"
                ;;
            *)
                print_error "Invalid choice, using CLI authentication"
                use_cli_auth=true
                auth_method="CLI"
                ;;
        esac
    else
        print_warning "Databricks CLI not found"
        print_info "Install with: pip install databricks-cli"
        echo ""

        local auth_options=(
            "Personal Access Token (PAT)"
            "OAuth M2M Service Principal"
        )

        local auth_choice=$(select_option "Select authentication method (use ↑↓ arrows, Enter to select):" "${auth_options[@]}")
        auth_choice=$((auth_choice + 1))  # Convert 0-based to 1-based

        case $auth_choice in
            1)
                auth_method="PAT"
                ;;
            2)
                auth_method="OAuth"
                ;;
            *)
                print_error "Invalid choice, using PAT"
                auth_method="PAT"
                ;;
        esac
    fi

    # Get Databricks host if not already set
    if [ -z "$databricks_host" ]; then
        echo ""
        read -p "Enter Databricks workspace URL: " databricks_host
        if [ -z "$databricks_host" ]; then
            print_error "Host is required"
            databricks_host="https://your-workspace.cloud.databricks.com"
        fi
    fi

    # Get authentication credentials based on method
    local databricks_token=""
    local databricks_client_id=""
    local databricks_client_secret=""

    if [ "$auth_method" = "PAT" ]; then
        echo ""
        read -p "Enter Personal Access Token: " databricks_token
        if [ -z "$databricks_token" ]; then
            print_warning "Token not provided - you'll need to add it manually"
            databricks_token="dapi..."
        fi
    elif [ "$auth_method" = "OAuth" ]; then
        echo ""
        read -p "Enter OAuth Client ID: " databricks_client_id
        read -p "Enter OAuth Client Secret: " databricks_client_secret
        if [ -z "$databricks_client_id" ] || [ -z "$databricks_client_secret" ]; then
            print_warning "OAuth credentials not provided - you'll need to add them manually"
        fi
    fi

    # Get optional configuration
    echo ""
    print_info "Optional configuration (press Enter for defaults)"
    echo ""
    read -p "Timeout in seconds (default: 300): " timeout
    timeout=${timeout:-300}

    read -p "Poll interval in seconds (default: 2): " poll_interval
    poll_interval=${poll_interval:-2}

    read -p "Max retries (default: 3): " max_retries
    max_retries=${max_retries:-3}

    read -p "Serving endpoint name (default: databricks-dbrx-instruct): " serving_endpoint
    serving_endpoint=${serving_endpoint:-databricks-dbrx-instruct}

    # Create .env file
    cat > .env << EOF
# Databricks Workspace Configuration
DATABRICKS_HOST=$databricks_host

# Authentication Method: $auth_method
EOF

    if [ "$auth_method" = "PAT" ]; then
        cat >> .env << EOF
DATABRICKS_TOKEN=$databricks_token
EOF
    elif [ "$auth_method" = "OAuth" ]; then
        cat >> .env << EOF
DATABRICKS_CLIENT_ID=$databricks_client_id
DATABRICKS_CLIENT_SECRET=$databricks_client_secret
EOF
    else
        cat >> .env << EOF
# Using Databricks CLI default authentication
# No token or OAuth credentials needed
EOF
    fi

    cat >> .env << EOF

# Server Configuration
DATABRICKS_TIMEOUT_SECONDS=$timeout
DATABRICKS_POLL_INTERVAL_SECONDS=$poll_interval
DATABRICKS_MAX_RETRIES=$max_retries

# Config Generation
DATABRICKS_SERVING_ENDPOINT_NAME=$serving_endpoint
EOF

    print_success ".env file created successfully"

    if [ "$auth_method" = "CLI" ]; then
        echo ""
        print_info "Using Databricks CLI authentication"
        print_warning "Make sure you're authenticated: databricks auth login"
    fi
}

# Verify installation
verify_installation() {
    print_header "Verifying Installation"

    if command -v genie-mcp-server &> /dev/null; then
        print_success "genie-mcp-server command is available"
    else
        print_error "genie-mcp-server command not found"
        print_info "Try running: source .venv/bin/activate"
        return 1
    fi

    # Check if we can import the module
    if python -c "import genie_mcp_server" 2>/dev/null; then
        print_success "Python module can be imported"
    else
        print_error "Cannot import genie_mcp_server module"
        return 1
    fi
}

# Print next steps
print_next_steps() {
    print_header "Installation Complete!"

    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo ""

    # Check if .env is properly configured
    if [ -f ".env" ] && grep -q "your-workspace.cloud.databricks.com" .env 2>/dev/null; then
        echo -e "1. ${YELLOW}Configure your Databricks credentials:${NC}"
        echo -e "   ${YELLOW}./configure.sh${NC}"
        echo ""
        echo -e "2. Activate the virtual environment:"
        echo -e "   ${YELLOW}source .venv/bin/activate${NC}"
        echo ""
        echo -e "3. Run the server:"
        echo -e "   ${YELLOW}genie-mcp-server${NC}"
    else
        echo -e "1. Activate the virtual environment:"
        echo -e "   ${YELLOW}source .venv/bin/activate${NC}"
        echo ""
        echo -e "2. Run the server:"
        echo -e "   ${YELLOW}genie-mcp-server${NC}"
    fi

    echo ""
    echo -e "Or integrate with Claude Desktop:"
    echo -e "   See ${BLUE}README.md${NC} for configuration instructions"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "   - README.md - Main documentation"
    echo "   - QUICKSTART.md - Quick start guide"
    echo "   - TOOLS.md - Tool reference"
    echo ""

    if [ -n "$SELECTED_PROFILE" ]; then
        echo -e "${GREEN}Using Databricks profile:${NC} $SELECTED_PROFILE"
        echo ""
    fi
}

# Main installation flow
main() {
    clear
    print_header "Databricks Genie MCP Server - Installation"
    echo ""

    # Run installation steps
    check_python
    create_venv
    activate_venv
    upgrade_pip
    install_package
    setup_env

    echo ""
    if verify_installation; then
        print_next_steps
    else
        print_error "Installation verification failed"
        echo "Please check the error messages above"
        exit 1
    fi
}

# Run main function
main
