==============
bitbucket-sync
==============

Synchronise all repositories of a bitbucket account to local clones.

Synchronising means that remote repositories are cloned to local disk and later
updated by changes in remote repository. This tool never pushes updates from
local disk to remote server.

Installation
============

using pip from pypi (recommended)::

    $ pip install bitbucket-sync

using pip from github::

    $ pip install git+https://github.com/Gautier/bitbucket-sync.git#bitbucket-sync

Requirements - git and/or hg command installed
----------------------------------------------

To be able working with git or mercurial repositories, the respective programs
must be installed locally.

However if you do not work with one of repository types, you won't need to
install the related command.

If you attempt to synchronise repositories without the related program
bitbucket-sync will fail.

Get credentials to access bitbucket account
===========================================

To access repositories under your bitbucket account, you need to configure the
account for that and get required OAuth tokens called Key and Secret.

1. go to https://.org - (your lovely avatar) - Manage account - Integrated applications

2. In section "OAuth consumers" click "Add consumer" and a form appears

3. Fill in some information (it is not really important what it will be):

   *Name*: bitbucket-sync

   *Description*: Synchronise all repositories of a bitbucket account to local clones.

   *URL*: https://github.com/Gautier/bitbucket-sync

   and click "Add consumer".

4. You will be presented with a page showing *Key* and *Secret* strings. These
   strings will be used in following calls to bitbucket-sync.


Note that the Key and Secret will become accessible in the same place (OAuth
consumers) in Bitbucket, where you created it. There is no need to recreate it
again.

Synchronizing your repositories from bitbucket to local directory
=================================================================

Initially clone all repositories you own on bitbucket
-----------------------------------------------------

Having a bitbucket account, e.g. "Gautier", bitbucket will show a set of
repositories prefixed with this account name "Gautier/". These are the
repositories, owned by that account.

To clone all bitbucket repositories owned by given user account to local disk::

    $ mkdir archive
    $ cd archive
    $ bitbucket-sync --key xxxxOAuthKeyxxx --secret yyyyOAuthSecretyyy --directory . --owner Gautier

This creates a subdirectory named Gautier with one deeper subdirectory per
cloned repository.

Fetch all updates from bitbucket repos owned by a given account
---------------------------------------------------------------

The process is very simple, just repeat the call as before::

    $ bitbucket-sync --key xxxxOAuthKeyxxx --secret yyyyOAuthSecretyyy --directory . --owner Gautier

All updates on bitbucket will be fetched down to local repositories.

All new repositories will be cloned.

There is no process of cleaning repositories which were removed from bitbucket.

Repositories renamed on bitbucket will be considered new ones (and cloned).

Syncing other repositories you have direct access to
----------------------------------------------------

If other users including team accounts grant you access to repositories owned
by them, you will get a chance to synchronise them too.

Syncing repositories from explicitly named owner
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You just change owner in the call and you get it done::

    $ bitbucket-sync --key xxxxOAuthKeyxxx --secret yyyyOAuthSecretyyy --directory . --owner vlcinsky

Syncing all repositories accessible by your account
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you omit the `--owner` parameter, all repositories you have access to will be synced::

    $ bitbucket-sync --key xxxxOAuthKeyxxx --secret yyyyOAuthSecretyyy --directory .

As usually, there will be one subdirectory per owner, and then all related repositories in it.

Questions and Answers
=====================

Does the tool synchronises Mercurial repositories?
--------------------------------------------------

Yes, as long as mercurial is installed locally.

Does it clone all publicly accessible repositories from bitbucket?
------------------------------------------------------------------

Simply no.

The tool takes into account only repositories: 

- created (and owned) by you

- created by someone else and with explicit grant of permission on that
  repository for your account.
