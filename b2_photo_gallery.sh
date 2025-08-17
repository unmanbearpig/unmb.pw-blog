#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to show help
show_help() {
    echo "b2_photo_gallery - Upload photos to Backblaze B2 and generate Jekyll gallery pages"
    echo
    echo "Usage:"
    echo "  ./b2_photo_gallery.sh [OPTIONS] <photo-directory>"
    echo
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -t, --title TITLE         Custom title for the gallery (defaults to directory name)"
    echo "  -d, --date YYYY-MM-DD     Custom date for the post (defaults to today)"
    echo "  -o, --output PATH         Custom output markdown file path"
    echo "  --dry-run                 Show what would be done without making changes"
    echo "  --force-reupload          Force reupload even if files exist in B2"
    echo
    echo "Examples:"
    echo "  ./b2_photo_gallery.sh /path/to/photos"
    echo "  ./b2_photo_gallery.sh -t \"My Gallery\" -d 2024-03-20 /path/to/photos"
    echo "  ./b2_photo_gallery.sh --dry-run /path/to/photos"
    echo
    echo "Environment:"
    echo "  The script will automatically:"
    echo "  - Create and manage a Python virtual environment"
    echo "  - Install required dependencies"
    echo "  - Check for b2 CLI authorization"
    echo
    echo "Requirements:"
    echo "  - Python 3"
    echo "  - b2 CLI tool (will be installed if missing)"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--title)
            TITLE="$2"
            shift 2
            ;;
        -d|--date)
            DATE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --force-reupload)
            FORCE_REUPLOAD="--force-reupload"
            shift
            ;;
        *)
            PHOTO_DIR="$1"
            shift
            ;;
    esac
done

# Check if photo directory is provided
if [ -z "$PHOTO_DIR" ]; then
    echo "Error: Photo directory is required"
    echo "Use --help for usage information"
    exit 1
fi

# Check if Python 3 is installed
if ! command_exists python3; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists, create if it doesn't
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
    
    # Activate virtual environment and install requirements
    source "$SCRIPT_DIR/venv/bin/activate"
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    # Activate existing virtual environment
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Check if b2 CLI is installed
if ! command_exists b2; then
    echo "Installing b2 CLI tool..."
    pip install b2
fi

# Check if b2 is authorized
if ! b2 account get >/dev/null 2>&1; then
    echo "Error: b2 CLI is not authorized"
    echo "Please run: b2 authorize-account"
    exit 1
fi

# Build command arguments
CMD_ARGS=("$PHOTO_DIR")
[ ! -z "$TITLE" ] && CMD_ARGS+=("--title" "$TITLE")
[ ! -z "$DATE" ] && CMD_ARGS+=("--date" "$DATE")
[ ! -z "$OUTPUT" ] && CMD_ARGS+=("--output" "$OUTPUT")
[ ! -z "$DRY_RUN" ] && CMD_ARGS+=("$DRY_RUN")
[ ! -z "$FORCE_REUPLOAD" ] && CMD_ARGS+=("$FORCE_REUPLOAD")

# Run the Python script with all arguments
python3 "$SCRIPT_DIR/b2_photo_gallery.py" "${CMD_ARGS[@]}" 
