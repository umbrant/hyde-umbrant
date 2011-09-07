Clyde - Sometimes you can't hack
================================

Clyde is a barebones web app to make editing & creating posts using Hyde.

## Background

1. The [tweet](http://twitter.com/poxd/status/7329895507) that started it.
2. Discussion [thread](http://groups.google.com/group/hyde-dev/browse_thread/thread/44832e915e2d6103) that took off from the tweet.
3. Pretty [pictures and some text](http://groups.google.com/group/hyde-dev/web/online-adding-editing-content).

## Requirements

1. [Facebook Tornado](http://github.com/facebook/tornado) - This now exists as a git submodule in the lib directory. You can init and setup right from the lib directory.
2. A branch for drafts and a branch for production for each of the hyde sites you
want to maintain with Clyde.

## Setup

Right now the only thing that you need to do is to modify sites.yaml in the root directory.

## Run Clyde

You can start clyde by simply executing `python clyde.py` from the hyde directory.
                                                     
-----------------------------------------------------

## Next Steps

1. <del>Create New Files.</del>
2. Allow uploading and replacing media files
3. Create commands(sets) for `markitup` editor for Hyde specific commands
4. Add client side scripts for better file detection and `markitup` initialization
5. <del>Allow generating the site for preview</del>
6. The site right now is unresponsive - No feedback, no indicators and no error messages.
7. Sign In/Sign Out
8. Documentation










