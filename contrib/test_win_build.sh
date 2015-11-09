DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BRANCH="win-${PYTHON//C:\\/}"
TX="$DIR/../dist/tx.exe"
source "$DIR/tx_commands.sh"
