#!/usr/bin/python
import simples3
import os, sys
import re
import json, zlib
import ConfigParser

# S3 config options are parsed from deploy.cfg
config = ConfigParser.ConfigParser()
config.readfp(open('deploy.cfg'))

ACCESS_KEY = config.get('main', 'access_key')
SECRET_KEY = config.get('main', 'secret_key')
BUCKET_NAME = config.get('main', 'bucket_name')
BASE_URL = config.get('main', 'base_url')
SOURCE_DIR = config.get('main', 'source_dir')


# Regex patterns for files/directories to ignore
IGNORE = (
          "\.(.*).swp$", "~$", # ignore .swp files
         )

#### code below ####

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
checksums = {}
checksums_mod = False
try:
    temp = bucket.get("__checksums")
    checksums = json.loads(temp.read())
except simples3.bucket.KeyNotFound:
    pass

# recursively put in all files in SOURCE_DIR

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

        # check the checksum
        contents = open(filename).read()
        crc = zlib.crc32(contents)
        # update dict if no match
        if checksums.setdefault(key) != crc:
            checksums[key] = crc
            checksums_mod = True
        # on match, we skip
        else:
            continue

        stat = os.stat(filename)
        metadata = {"modtime":str(stat.st_mtime)}

        # check if it's changed with modtimes
        sf = False
        try:
            sf = bucket.info(key)
            if sf["metadata"].has_key("modtime") and \
            sf["metadata"]["modtime"] == str(stat.st_mtime):
                continue
        #except simples3.bucket.KeyNotFound:
        #    pass
        except KeyError:
            pass
        finally:
            bucket.put(key, contents, acl="public-read", metadata=metadata)
            print "Uploading", key


# Upload the checksums file too, if it was modified
if checksums_mod:
    print "Updating checksums file...",
    bucket.put("__checksums", json.dumps(checksums))
    print "done."
