init_intro = """
 _____                    _  __
|_   _| __ __ _ _ __  ___(_)/ _| _____  __
  | || '__/ _` | '_ \/ __| | |_ / _ \ \/ /
  | || | | (_| | | | \__ \ |  _|  __/>  <
  |_||_|  \__,_|_| |_|___/_|_|  \___/_/\_\


Welcome to Transifex Client! Please follow the instructions to
initialize your project.
"""
init_initialized = "It seems that this project is already intitialized."

init_reinit = "Do you want to delete it and reinit the project?"
init_host = "Transifex instance"

token_instructions = """
Transifex Client needs a Transifex API token to authenticate.
If you don’t have one yet, you can generate a token at
https://www.transifex.com/user/settings/api/.
"""

token_validation_failed = """
Error: Invalid token. You can generate a new token at
https://www.transifex.com/user/settings/api/.
"""

token_msg = "Please enter your api token"

running_tx_set = "Running tx set command for you..."


create_project_instructions = """To create a new project, head to https://www.transifex.com/{org}/add.
Once you’ve created the project, you can continue.
"""

TEXTS = {
    "source_file": {
        "description": ("""
The Transifex Client syncs files between your local directory and Transifex.
The mapping configuration between the two is stored in a file called .tx/config
in your current directory. For more information, visit
https://docs.transifex.com/client/set/.
"""),
        "error": ("No file was found in that path. Please correct the path "
                  "or make sure a file exists in that location."),
        "processing": "",
        "message": "Enter a path to your local source file"
    },
    "expression": {
        "description": ("""
Next, we’ll need a path expression pointing to the location of the
translation files (whether they exist yet or not) associated with
the source file ‘{source_file}’. You should use <lang> as a
wildcard for the language code.
"""),
        "error": "The path expression doesn’t contain the <lang> placeholder.",
        "message": "Enter a path expression"
    },
    "formats": {
        "description": ("""
Here’s a list of the supported file formats. For more information,
check our docs at https://docs.transifex.com/formats/.
"""),
        "error": "",
        "message": "Select the file format type",
    },
    "organization": {
        "description": ("""
You’ll now choose a project in a Transifex organization to sync with your
local files.
You belong to these organizations in Transifex:
"""),
        "error": ("""
You don’t have any projects in the ‘Waze’ organization. To create a new
project, head to https://www.transifex.com/waze/add.  Once you’ve created
a project, you can continue.
"""),
        "message": "Select the organization",
    },
    "projects": {
        "description": ("""We found these projects in your organization."""),
        "error": "",
        "message": "Select project",
    },
}

epilog = """
The Transifex Client syncs files between your local directory and Transifex.
The mapping configuration between the two is stored in a file called
.tx/config in your current directory. For more information, visit
https://docs.transifex.com/client/set/.
"""

final_instr = """
Here’s the content of the .tx/config file that was created:

[{resource}]
source_file = {source_file}
file_filter = {file_filter}
source_lang = {source_lang}
type = {type}

You could also generate the same configuration by running a single command like:

tx set --auto-local -r {resource} -f {source_file} -s {source_lang} -t {type} '{file_filter}'

More info can be found at https://docs.transifex.com/client/set.

Here are some useful commands for your next steps:

# Upload source files to Transifex:
tx push  --source

# Download translation files from Transifex once translations are done:
tx pull --translations
"""
