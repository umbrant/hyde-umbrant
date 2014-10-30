#!/usr/bin/python
import simples3
import os, sys
import re
import json, zlib
import ConfigParser
from Queue import Queue
from threading import Thread


checksums = {}
checksums_mod = False

class Worker(Thread):
    def __init__(self, queue, BUCKET_NAME, ACCESS_KEY, SECRET_KEY, BASE_URL):
        Thread.__init__(self)
        self.queue = queue
        self.bucket = simples3.S3Bucket(BUCKET_NAME, access_key=ACCESS_KEY, 
                        secret_key=SECRET_KEY, base_url=BASE_URL)

    def run(self):
        # Get a new item from the work queue, do work, do it again
        while True:
            key, filename = self.queue.get()
            try:
                self.upload(key, filename)
            finally:
                self.queue.task_done()

    def upload(self, key, filename):
        global checksums, checksums_mod
        # check the checksum
        contents = open(filename).read()
        crc = zlib.crc32(contents)
        # update dict if no match
        if checksums.setdefault(key) != crc:
            checksums[key] = crc
            checksums_mod = True
        # on match, we skip
        else:
            return

        stat = os.stat(filename)
        metadata = {"modtime":str(stat.st_mtime)}
        headers = {'x-amz-meta-Cache-Control' : 'max-age=3600'}

        # check if it's changed with modtimes
        sf = False
        try:
            sf = self.bucket.info(key)
            if sf["metadata"].has_key("modtime") and \
            sf["metadata"]["modtime"] == str(stat.st_mtime):
                return
        #except simples3.bucket.KeyNotFound:
        #    pass
        except KeyError:
            pass

        print "Uploading", key
        self.bucket.put(key, contents, acl="public-read", metadata=metadata, headers=headers)

def main():
    global checksums, checksums_mod

    # S3 config options are parsed from deploy.cfg
    config = ConfigParser.ConfigParser()
    config.readfp(open('deploy.cfg'))

    ACCESS_KEY = config.get('main', 'access_key')
    SECRET_KEY = config.get('main', 'secret_key')
    BUCKET_NAME = config.get('main', 'bucket_name')
    BASE_URL = config.get('main', 'base_url')
    SOURCE_DIR = config.get('main', 'source_dir')
    NUM_WORKERS = int(config.get('main', 'num_workers'))

    # Regex patterns for files/directories to ignore
    IGNORE = (
            "\.(.*).swp$", "~$", # ignore .swp files
            )

    # number of upload threads

    # clean up SOURCE_DIR for reliable parsing
    SOURCE_DIR = os.path.abspath(SOURCE_DIR)

    if not os.path.isdir(SOURCE_DIR):
        print "Error: specified path",SOURCE_DIR,"is invalid"
        sys.exit(-1)

    ignore_re = []
    for i in IGNORE:
        ignore_re.append(re.compile(i))

    # open bucket
    bucket = simples3.S3Bucket(BUCKET_NAME, access_key=ACCESS_KEY, 
                    secret_key=SECRET_KEY, base_url=BASE_URL)

    # attempt to get the checksum file from the bucket
    try:
        temp = bucket.get("__checksums")
        checksums = json.loads(temp.read())
    except simples3.bucket.KeyNotFound:
        pass

    # Work queue
    queue = Queue()

    # recursively put all files in SOURCE_DIR into the work queue
    for root, dirs, files in os.walk(SOURCE_DIR):
        relroot = root[len(SOURCE_DIR)+1:]
        for f in files:
            # root directory files should not have a preceding "/"
            # puts the files in a blank named directory, not what we want
            key = ""
            if relroot:
                key = relroot + "/" + f
            else:
                key = f
            filename = root + "/" + f

            # check for a match in the ignore list
            ignore = False
            for i in ignore_re:
                if re.match(i, f):
                    print "Ignoring", key
                    ignore = True
                    break
            if ignore:
                continue

            queue.put((key, filename))

    print "Found", queue.qsize(), "files"

    # Set up a worker pool
    for i in range(NUM_WORKERS):
        t = Worker(queue, BUCKET_NAME, ACCESS_KEY, SECRET_KEY, BASE_URL)
        t.daemon = True
        t.start()

    print "Started", NUM_WORKERS, "upload threads"

    # Wait for all the workers to finish
    queue.join()

    # Upload the checksums file too, if it was modified
    if checksums_mod:
        print "Updating checksums file...",
        bucket.put("__checksums", json.dumps(checksums))
        print "done."

### call main

if __name__ == "__main__":
    main()
