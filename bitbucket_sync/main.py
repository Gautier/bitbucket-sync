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

def sync_repo(directory, repo, lock):
    git_dir = os.path.join(directory, "%s.git" % repo["slug"])
    repo_url = "git@bitbucket.org:%s/%s.git" % (repo["owner"], repo["slug"])

    try:
        subprocess.check_output(["git", "--git-dir", git_dir, "rev-parse"],
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        # git repository hasn't yet been cloned properly
        if os.path.exists(git_dir):
            shutil.rmtree(git_dir)

        try:
            subprocess.check_output(["git",
                                     "clone",
                                     "--mirror",
                                     repo_url,
                                     git_dir],
                                     stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, e:
            lock.acquire()
            print("")
            print("Couldn't clone %s" % repo_url)
            print("git command: %s" % " ".join(e.cmd))
            print("git output:\n%s" % e.output)
            print("")
            lock.release()
    else:
        # git repository is valid
        subprocess.call(["git", "--git-dir", git_dir, "fetch", "-q"])


def worker(repositories, lock):
    while not repositories.empty():
        directory, repo = repositories.get()
        sync_repo(directory, repo, lock)


def ensure_base_directory(directory):
    directory = os.path.abspath(directory)

    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.isdir(directory):
        print("%s is not a directory" % directory)
        sys.exit(1)

    return directory


def retrieve_repositories_list(key, secret):
    oauth = OAuth1(client_key=unicode(key), client_secret=unicode(secret))
    API_ROOT = 'https://api.bitbucket.org'
    deploy_keys_resource = "%s/1.0/user/repositories/" % API_ROOT
    response = requests.get(deploy_keys_resource, auth=oauth)
    if response.status_code != 200:
        print("Error while listing the repositories")
        sys.exit(1)

    repo_list = response.json()
    return [repo for repo in repo_list if repo["scm"] == "git"]


def configure_queue(api_repositories, directory):
    directory = ensure_base_directory(directory)

    repositories_queue = Queue()
    for repo in api_repositories:
        repositories_queue.put((directory, repo))
    return repositories_queue


def consume_queue(repositories_queue, processes):
    lock = thread.allocate_lock()
    worker_threads = []
    for i in range(processes):
        worker_thread = Thread(target=worker, args=(repositories_queue, lock))
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
    try:
        processes = int(arguments["--processes"] or "")
    except ValueError:
        processes = cpu_count()

    api_repositories = retrieve_repositories_list(key, secret)
    repositories_queue = configure_queue(api_repositories, directory)
    consume_queue(repositories_queue, processes)
