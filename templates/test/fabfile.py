"""generic fabfile to simplify management of your hyde sites.
Scenario: Freelance developer, working on several computers
and OS-platforms (including Windows).

Synchronisation between computers is done via a "pseudo repository",
hosted in the home directory on the webserver.

Uses the unison file synchronizer because it also works on Windows.
Needs working ssh access to the server (use mingw - msys on windows).
If you use password protected private keys for authentication you
need to run
ssh-agent -s
ssh-add
for serving them to unison."""

from fabric.api import *

#### BEGIN CUSTOMIZATION ####

# UNISON can't handle path with spaces.
ROOT_PATH = '.'
DEPLOY_PATH = './deploy'

# REPO -- used for synchronisation: Add full path
REPO = '/home/unixusername/projects/hyde/mycoolsite'

# PROD -- production releases go here
PROD = '/var/www/mycoolsite'

# UNISON Flags
UFLAGS = "-batch -perms 0"
env.hosts = ['myserver.org']
user = 'unixusername'

#### END CUSTOMIZATION ####

REMOTE = "ssh://{0}@{1}/".format(user, env.hosts[0])

def list():
    """check what's there"""
    run('ls -al {0} {1}'.format(REPO, PROD))
    local('ls -al', capture = False)

def clean():
    """delete deploy directory"""
    local('rm -rf ./deploy')

def regen():
    """re-generate site in deploy directory"""
    clean()
    local('hyde.py -g -s .')

def serve():
    """Start the CherryPy testserver at port 8000."""
    local('hyde.py -w -p 8000 -s .')

def reserve():
    """regen and test-serve"""
    regen()
    serve()

def commit():
    """push into home directory on server"""
    local('unison {source} {dest} -force {source} {uflags}'.format(
            source = ROOT_PATH,
            dest = REMOTE + REPO,
            uflags = UFLAGS),
        capture = False)

def checkout():
    """fetch from home directory on server"""
    local('unison {source} {dest} -force {source} {uflags}'.format(
            source = REMOTE + REPO,
            dest = ROOT_PATH,
            uflags = UFLAGS),
        capture = False)

def sync():
    """do a merge -- synchronize both ways"""
    local('unison {source} {dest} {uflags}'.format(
            source = ROOT_PATH,
            dest = REMOTE + REPO,
            uflags = UFLAGS),
        capture = False)

def publish():
    """push deploy directory to webroot on server"""
    local('unison {source} {dest} -force {source} {uflags}'.format(
            source = DEPLOY_PATH,
            dest = REMOTE + PROD,
            uflags = UFLAGS),
        capture = False)