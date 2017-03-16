if [[ -z "$TRANSIFEX_USER" ]] ; then
	echo "NB: Skipping tests of $TX since TRANSIFEX_USER is undefined or empty"
	exit 0
fi

# Exit on fail
set -e

# Set up repo, tx config
rm -rf txci
git clone https://github.com/transifex/txci.git
cd txci
rm -rf .tx
$TX init --host="https://www.transifex.com" --user=$TRANSIFEX_USER --pass=$TRANSIFEX_PASSWORD
$TX set --auto-local -r txci.$BRANCH\_$TRANSIFEX_USER\_$RANDOM -s en 'locale/<lang>/LC_MESSAGES/django.po' -t PO --execute

# push/pull without XLIFF
echo "Pushing Source..."
$TX --traceback push -s
echo "Pushing Brazilian..."
yes | $TX --traceback push -t -l pt_BR -f
yes | $TX --traceback pull -l pt_BR -f

echo "Pushing a file that doesn't exist..."
yes | $TX --traceback push -t -l pt_PT -f

# try to download translation xliff
echo "Pulling xliff for pt_BR"
$TX --traceback pull -l pt_BR --xliff
echo "Checking if translation xlf file has been downloaded..."
ls locale/pt_BR/LC_MESSAGES/django.po.xlf

# upload xliff
echo "Pushing xliff for pt_BR"
$TX --traceback push -t -l pt_BR --xliff


$TX --traceback delete -f
