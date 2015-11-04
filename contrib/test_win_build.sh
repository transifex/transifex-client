HOST="https://www.transifex.com"
USER=$TRANSIFEX_USER
PASSWORD=$TRANSIFEX_PASSWORD
TX=`pwd`"/dist/tx.exe"

# Exit on fail
set -e

rm -rf txci
git clone https://github.com/diegobz/txci.git
cd txci
rm -rf .tx
$TX init --host=$HOST --user=$USER --pass=$PASSWORD
$TX set --auto-local -r txci.test -s en 'locale/<lang>/LC_MESSAGES/django.po' -t PO --execute
$TX push -s
$TX pull -l pt_BR -f

# $TX delete -f
