if [[ -z "$TRANSIFEX_USER" || -z "$TRANSIFEX_TOKEN" ]] ; then
	echo "NB: Skipping tests of $TX since TRANSIFEX_USER or TRANSIFEX_TOKEN is undefined or empty"
	exit 0
fi

# Exit on fail
set -e

# Set up repo, tx config
rm -rf txci
git clone https://github.com/transifex/txci.git
cd txci
rm -rf .tx
$TX init --host="https://www.transifex.com" --token=$TRANSIFEX_TOKEN --skipsetup --no-interactive
$TX config mapping -r txci.$BRANCH\_$TRANSIFEX_USER\_$RANDOM -s en 'locale/<lang>/LC_MESSAGES/django.po' -t PO --execute

# push/pull without XLIFF
echo "Pushing Source..."
$TX --traceback push -s
echo "Pushing Brazilian..."
$TX --traceback push -t -l pt_BR -f --no-interactive
$TX --traceback pull -l pt_BR -f

echo "Pushing a file that doesn't exist..."
$TX --traceback push -t -l pt_PT -f --no-interactive

# try to download translation xliff
echo "Pulling xliff for pt_BR"
$TX --traceback pull -l pt_BR --xliff
echo "Checking if translation xlf file has been downloaded..."
ls locale/pt_BR/LC_MESSAGES/django.po.xlf

# upload xliff
echo "Pushing xliff for pt_BR"
$TX --traceback push -t -l pt_BR --xliff -f --no-interactive


$TX --traceback delete -f
