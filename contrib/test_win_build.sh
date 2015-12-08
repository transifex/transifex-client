DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BRANCH="win-${PYTHON//C:\\/}"

# Test the PyInstaller executable:
TX="$DIR/../dist/tx.exe"
source "$DIR/tx_commands.sh"

# Test the Setuptools script:
TX="tx"
source "$DIR/tx_commands.sh"

