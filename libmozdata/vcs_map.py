import argparse
import io
import os
import shutil
import tarfile

import requests

MAP_FILE_URL = "https://moz-vcssync.s3-us-west-2.amazonaws.com/mapping/gecko-dev/git-mapfile.tar.bz2"
MAPPER_SERVICE = "https://mapper.mozilla-releng.net"
VCS_MAP_FULL_PATH = "vcs_map_full"
VCS_MAP_CACHE_PATH = "vcs_map_cache"

git_to_mercurial_mapping = {}
mercurial_to_git_mapping = {}


def download_mapfile():
    r = requests.head(MAP_FILE_URL, allow_redirects=True)

    new_etag = r.headers["ETag"]

    try:
        with open(f"{VCS_MAP_FULL_PATH}.etag", "r") as f:
            old_etag = f.read()
    except IOError:
        old_etag = None

    if old_etag != new_etag or not os.path.exists(VCS_MAP_FULL_PATH):
        r = requests.get(MAP_FILE_URL)

        with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:bz2") as tar:
            with open(VCS_MAP_FULL_PATH, "wb") as f:
                shutil.copyfileobj(
                    tar.extractfile("./build/conversion/beagle/.hg/git-mapfile"), f
                )

        with open(f"{VCS_MAP_FULL_PATH}.etag", "w") as f:
            f.write(new_etag)


MAPFILE_LOADED = False


def load_mapfile():
    global MAPFILE_LOADED
    if MAPFILE_LOADED:
        return

    MAPFILE_LOADED = True

    def _read_mapping_file(path):
        with open(path, "r") as f:
            for line in f:
                git_hash, mercurial_hash = line.rstrip("\n").split(" ")
                git_to_mercurial_mapping[git_hash] = mercurial_hash
                mercurial_to_git_mapping[mercurial_hash] = git_hash

    try:
        _read_mapping_file(VCS_MAP_FULL_PATH)
    except FileNotFoundError:
        pass

    try:
        _read_mapping_file(VCS_MAP_CACHE_PATH)
    except FileNotFoundError:
        pass


def _write_result(git_hash, mercurial_hash):
    with open(VCS_MAP_CACHE_PATH, "a") as f:
        mercurial_to_git_mapping[mercurial_hash] = git_hash
        git_to_mercurial_mapping[git_hash] = mercurial_hash

        f.write(f"{git_hash} {mercurial_hash}\n")


def mercurial_to_git(mercurial_hash):
    load_mapfile()

    if mercurial_hash not in mercurial_to_git_mapping:
        r = requests.get(f"{MAPPER_SERVICE}/gecko-dev/rev/hg/{mercurial_hash}")
        if not r.ok:
            raise Exception(
                f"Missing mercurial commit in the VCS map: {mercurial_hash}"
            )

        git_hash = r.text.split(" ")[0]

        _write_result(git_hash, mercurial_hash)

        return git_hash

    return mercurial_to_git_mapping[mercurial_hash]


def git_to_mercurial(git_hash, cache_only=False):
    load_mapfile()

    if git_hash not in git_to_mercurial_mapping:
        if cache_only:
            raise Exception("Missing git commit in the VCS map: {git_hash}")

        r = requests.get(f"{MAPPER_SERVICE}/gecko-dev/rev/git/{git_hash}")
        if not r.ok:
            raise Exception(f"Missing git commit in the VCS map: {git_hash}")

        mercurial_hash = r.text.split(" ")[1]

        _write_result(git_hash, mercurial_hash)

        return mercurial_hash

    return git_to_mercurial_mapping[git_hash]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repository_dir", help="Path to the repository", action="store")
    args = parser.parse_args()

    download_mapfile()

    import hglib

    hg = hglib.open(args.repository_dir)
    args = hglib.util.cmdbuilder(b"log", template="{node}\n")
    x = hg.rawcommand(args)
    revs = x.splitlines()

    for rev in revs:
        mercurial_to_git(rev.decode("ascii"))
