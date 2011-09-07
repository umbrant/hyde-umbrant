"""

uses py.test

sudo easy_install py

http://codespeak.net/py/dist/test.html

"""

from hydeengine.path_util import PathUtil


def test_filter_hidden_inplace():
    # Empty lists are not modified.
    empty_item_list = []
    PathUtil.filter_hidden_inplace(empty_item_list)
    assert empty_item_list == []

    # .htacess is not filtered.
    htaccess_list = [".htaccess"]
    PathUtil.filter_hidden_inplace(htaccess_list)
    assert htaccess_list == [".htaccess"]

    # Invisible files and filenames ending in tildes are filtered.
    item_list = [".htaccess", 'a.html', '.a.html', 'd.html~', 'b/c.html']
    PathUtil.filter_hidden_inplace(item_list)
    assert item_list == [".htaccess", 'a.html', 'b/c.html']


def test_get_path_fragment():
    fragment = PathUtil.get_path_fragment(
        "/root/directory",
        "/root/directory/sub/directory")
    assert fragment == "sub/directory/"


def test_get_mirror_dir():
    # Example from get_mirror_folder() docstring in hydeengine/file_system.py
    directory = "/usr/local/hyde/stuff"
    source_root = "/usr/local/hyde"
    mirror_root = "/usr/tmp"
    mirror_dir = PathUtil.get_mirror_dir(directory, source_root, mirror_root,
                                         ignore_root=False)
    assert mirror_dir == "/usr/tmp/hyde/stuff/"
    mirror_dir = PathUtil.get_mirror_dir(directory, source_root, mirror_root,
                                        ignore_root=True)
    assert mirror_dir == "/usr/tmp/stuff/"
    mirror_dir = PathUtil.get_mirror_dir(source_root, source_root, mirror_root,
                                        ignore_root=True)
    assert mirror_dir == mirror_root


# TODO: I haven't written any tests for mirror_dir_tree() because it doesn't
# appear to be used anywhere and because it catches all exceptions without
# handling them.
