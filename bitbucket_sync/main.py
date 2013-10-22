"""bitbucket-sync synchronize all the repositories of a bitbucket account to a
directory. The OAuth key and secret must already be activated in bitbucket.

Usage:
  bitbucket-sync [--processes=processes] --key=<key> --secret=<secret> --directory=<directory>
  bitbucket-sync --help

Options:
  --help                     Show help
  --directory=<directory>    Directory where the repositories are mirrored
  --key=<key>                Bitbucket API key
  --secret=<secret>          Bitbucket API secret
  --processes=<processes>    Number of repositories to mirror at the same time (defaults to CPU count)
"""

from multiprocessing import Pool
import os
import signal
import subprocess
import sys

from docopt import docopt
from requests_oauthlib import OAuth1
import requests

def sync_repo(args):
    directory, repo = args
    os.chdir(directory)
    repo_url = "git@bitbucket.org:%s/%s.git" % (repo["owner"], repo["slug"])
    try:
        subprocess.call(["git", "clone", "--mirror", repo_url])
        os.chdir("%s.git" % repo["slug"])
        subprocess.call(["git", "fetch", "-q"])
    except Exception:
        raise

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def main():
    arguments = docopt(__doc__, argv=sys.argv[1:], help=True, version="0.1")

    key = arguments["--key"]
    secret = arguments["--secret"]
    directory = arguments["--directory"]
    processes = arguments["--processes"]

    oauth = OAuth1(client_key=unicode(key), client_secret=unicode(secret))
    API_ROOT = 'https://api.bitbucket.org'
    deploy_keys_resource = "%s/1.0/user/repositories/" % API_ROOT
    response = requests.get(deploy_keys_resource, auth=oauth)
    if response.status_code != 200:
        print "Error while listing the repositories"
        sys.exit(1)

    repo_list = response.json()
    only_git = [repo for repo in repo_list if repo["scm"] == "git"]

    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.isdir(directory):
        print "%s is not a directory" % directory
        sys.exit(1)

    pool = Pool(processes=processes, initializer=init_worker)
    directory = os.path.abspath(directory)

    try:
        pool.map(sync_repo, [(directory, repo) for repo in only_git])
    except KeyboardInterrupt:
        pool.close()
        pool.terminate()
        pool.join()
