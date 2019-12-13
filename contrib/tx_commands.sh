if [[ -z "$TRANSIFEX_USER" || -z "$TRANSIFEX_TOKEN" || -z "$TRANSIFEX_PROJECT" ]] ; then
    echo "NB: Skipping tests of $TX since TRANSIFEX_USER or TRANSIFEX_TOKEN or TRANSIFEX_PROJECT is undefined or empty"

    # TRANSIFEX_ ENV variables are not expected for pull requests or local builds
    [[ "${CIRCLE_BRANCH+x}" != x || "${CIRCLE_BRANCH}" == master || "${CIRCLE_BRANCH}" =~ ^pull/.* ]]
    exit $?
fi

# Exit on fail
set -e

export TX_TOKEN=$TRANSIFEX_TOKEN

# Set up repo, tx config
rm -rf txci
git clone https://github.com/transifex/txci.git
cd txci
rm -rf .tx
$TX init --host="https://www.transifex.com" --skipsetup --no-interactive
$TX config mapping -r $TRANSIFEX_PROJECT.$BRANCH\_$TRANSIFEX_USER\_$RANDOM -s en 'locale/<lang>/LC_MESSAGES/django.po' -t PO --execute

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

# Try to upload/download translations in parallel
# Choose some languages to work with
LANGS=bs_BA,en_GB,fr,id,ku_IQ,pa,sr@latin,vi,ach,ca,eo,fr_CA,id_ID,lt,sr_RS,zh_CN,ar,ca@valencia,es,fy,it,lv,pt,sv,zh_TW

echo "Pushing translations for 26 languages in parallel"
$TX push -t -f -l $LANGS --no-interactive --parallel

echo "Removing the original translation files"
IFS=','  # This is needed for splitting the languages list
for lang_code in $LANGS; do
    rm locale/$lang_code/LC_MESSAGES/django.po
done

echo "Pulling translations for the 26 languages in parallel"
IFS=' ' # Revert splitting back to normal (using spaces)
$TX --traceback pull -f -l $LANGS --parallel

echo "Checking if translation files have been downloaded..."
IFS=','  # This is needed for splitting the languages list
for lang_code in $LANGS; do
    ls locale/$lang_code/LC_MESSAGES/django.po
done
IFS=' ' # Revert splitting back to normal (using spaces)

# upload xliff
echo "Pushing xliff for pt_BR"
$TX --traceback push -t -l pt_BR --xliff -f --no-interactive

# Retrying logic to delete resource. This is an ugly hack necessitated by a random
# 'Conflict/Duplicate' server error occuring when trying to delete the resource
for i in 1 2 3 4; do echo "Attempt to delete Source..."; $TX --traceback delete -f && break || sleep 20; done
