"""bitbucket-sync synchronize repositories of a bitbucket account to a local
directory. The OAuth key and secret must already be activated in bitbucket.

Usage:
  bitbucket-sync [--processes=processes]  [--owner=<owner>] --key=<key> --secret=<secret> --directory=<directory>
  bitbucket-sync --help

Options:
  --help                     Show help
  --directory=<directory>    Directory where the repositories are mirrored
  --owner=<owner>            Only retrieve repository from this owner. Default: retrieve all repositories
  --key=<key>                Bitbucket API key
  --secret=<secret>          Bitbucket API secret
  --processes=<processes>    Number of repositories to mirror at the same time (defaults to CPU count)
"""

from Queue import Queue
from multiprocessing import cpu_count
from threading import Thread
import os
import shutil
import subprocess
import sys
import thread
import time

from docopt import docopt
from requests_oauthlib import OAuth1
import requests


class GitCommands(object):
    def __init__(self, directory, owner, slug):
        self.owner = owner
        self.slug = slug
        self.local_dir = os.path.join(directory, owner, "%s.git" % slug)
        self.repo_url = "git@bitbucket.org:%s/%s.git" % (owner, slug)

    def validate_local_repository(self):
        subprocess.check_output(
                ["git", "--git-dir", self.local_dir, "rev-parse"],
                stderr=subprocess.STDOUT)

    def clone(self):
        subprocess.check_output(
                ["git", "clone", "--mirror", self.repo_url, self.local_dir],
                stderr=subprocess.STDOUT)

    def update(self):
        subprocess.call(["git", "--git-dir", self.local_dir, "fetch", "-q"])


class HgCommands(object):
    def __init__(self, directory, owner, slug):
        self.owner = owner
        self.slug = slug
        self.local_dir = os.path.join(directory, owner, "%s.hg" % slug)
        self.repo_url = "ssh://hg@bitbucket.org/%s/%s" % (owner, slug)

    def validate_local_repository(self):
        subprocess.check_output(["hg", "-R", self.local_dir, "verify", "-q"],
                                stderr=subprocess.STDOUT)

    def clone(self):
        subprocess.check_output(
                ["hg", "clone", "-U", self.repo_url, self.local_dir],
                stderr=subprocess.STDOUT)

    def update(self):
        subprocess.call(["hg", "-R", self.local_dir, "pull", "-q"])


def sync_repo(directory, repo, owner, lock):
    if repo["scm"] == "git":
        scm = GitCommands(directory, owner, repo["slug"])
    elif repo["scm"] == "hg":
        scm = HgCommands(directory, owner, repo["slug"])
    else:
        raise NotImplementedError(
                "SCM of type %s is not currently supported" % repo["scm"])

    try:
        scm.validate_local_repository()
    except subprocess.CalledProcessError:
        # git repository hasn't yet been cloned properly
        if os.path.exists(scm.local_dir):
            shutil.rmtree(scm.local_dir)

        try:
            scm.clone()
            return True
        except subprocess.CalledProcessError, e:
            lock.acquire()
            print("")
            print("Couldn't clone %s" % scm.repo_url)
            print("command: %s" % " ".join(e.cmd))
            print("output:\n%s" % e.output)
            print("")
            lock.release()
    else:
        # git repository is valid
        scm.update()
        return True


def worker(repositories, lock, owner):
    while not repositories.empty():
        directory, repo = repositories.get()
        if sync_repo(directory, repo, owner, lock):
            print "%s/%s synchronised" % (owner, repo["slug"])


def ensure_base_directory(directory):
    directory = os.path.abspath(directory)

    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.isdir(directory):
        print("%s is not a directory" % directory)
        sys.exit(1)

    return directory


def retrieve_repositories_list_pages(key, secret, owner, nextP=""):
    oauth = OAuth1(client_key=unicode(key), client_secret=unicode(secret))
    API_ROOT = 'https://api.bitbucket.org'
    deploy_keys_resource = "%s/2.0/repositories/%s/%s" % (API_ROOT, owner, nextP)
    response = requests.get(deploy_keys_resource, auth=oauth)
    if response.status_code != 200:
        print("Error while listing the repositories")
        sys.exit(1)

    return response

def retrieve_repositories_list(key, secret, owner, nextP=""):
    resp = []
    page =""
    while True:
        r = retrieve_repositories_list_pages(key, secret, owner, nextP=page).json()
        resp += r['values']
        if 'next' in r:
            page = r['next'].split('/')[-1]
        else:
            break
    for repository in resp:
        yield repository
 

def configure_queue(api_repositories, directory):
    directory = ensure_base_directory(directory)

    repositories_queue = Queue()
    for repository in api_repositories:
        repositories_queue.put((directory, repository))
    return repositories_queue


def consume_queue(repositories_queue, processes, owner):
    lock = thread.allocate_lock()
    worker_threads = []
    for i in range(processes):
        worker_thread = Thread(target=worker, args=(repositories_queue, lock, owner))
        worker_thread.start()
        worker_threads.append(worker_thread)

    try:
        while any(w.isAlive() for w in worker_threads):
            time.sleep(.5)
    except KeyboardInterrupt:
        # purge rest of queue
        # Note that the git processes inside the workder threads should get
        # killed
        while not repositories_queue.empty():
            repositories_queue.get()

def main():
    arguments = docopt(__doc__, argv=sys.argv[1:], help=True, version="0.3.0")

    key = arguments["--key"]
    secret = arguments["--secret"]
    directory = arguments["--directory"]
    owner = arguments["--owner"] or ""
    try:
        processes = int(arguments["--processes"] or "")
    except ValueError:
        processes = cpu_count()

    api_repositories = retrieve_repositories_list(key, secret, owner)
    repositories_queue = configure_queue(api_repositories, directory)
    consume_queue(repositories_queue, processes, owner)
