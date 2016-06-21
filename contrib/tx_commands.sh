if [[ -z "$TRANSIFEX_USER" ]] ; then
	echo "NB: Skipping tests of $TX since TRANSIFEX_USER is undefined or empty"
	exit 0
fi

# Exit on fail
set -e

rm -rf txci
git clone https://github.com/transifex/txci.git
cd txci
rm -rf .tx
$TX init --host="https://www.transifex.com" --user=$TRANSIFEX_USER --pass=$TRANSIFEX_PASSWORD
$TX set --auto-local -r txci.$BRANCH -s en 'locale/<lang>/LC_MESSAGES/django.po' -t PO --execute
$TX --traceback push -s
$TX --traceback pull -l pt_BR -f
$TX --traceback delete -f
