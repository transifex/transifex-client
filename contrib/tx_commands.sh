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
$TX set --auto-local -r txci.$BRANCH -s en 'locale/<lang>/LC_MESSAGES/django.po' -t PO --execute

# push/pull without XLIFF
$TX --traceback push -s
$TX --traceback pull -l pt_BR -f

# # Push dummy translation to pt_BR language
# cp locale/en/LC_MESSAGES/django.po locale/pt_BR/LC_MESSAGES/django.po
# yes | $TX --traceback push -t -l pt_BR -f
#
# # try to download translation xliff
# $TX --traceback pull -l pt_BR -f --xliff
# echo 'Checking if translation xlf file has been downloaded...'
# ls locale/pt_BR/LC_MESSAGES/django.po.xlf
#
# # upload xliff
# yes | $TX --traceback push -t -l pt_BR -f --xliff

$TX --traceback delete -f
