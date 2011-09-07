"""
Tests of URL generation. 

Note that test_homepage doubles as a test for listing pages that have 
"listing: True" set manually.

Tests are still needed for GENERATE_ABSOLUTE_FS_URLS.
"""

import os
import sys
from django.conf import settings

TEST_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(TEST_ROOT + "/..")
 
sys.path = [ROOT] + sys.path

from hydeengine.file_system import File, Folder
from hydeengine import url, Initializer, Generator, setup_env
from hydeengine.siteinfo import SiteNode, SiteInfo, Page

TEST_SITE = Folder(TEST_ROOT).child_folder("test_site")
        
def setup_module(module):
    Initializer(TEST_SITE.path).initialize(ROOT, template="test", force=True)
    setup_env(TEST_SITE.path)

def teardown_module(module):
    TEST_SITE.delete()

class TestNormalUrls:
    """This is to make sure that the clean url generator hasn't interfered with
    regular urls"""

    def setup_class(self):
        settings.GENERATE_ABSOLUTE_FS_URLS = False
        settings.GENERATE_CLEAN_URLS = False
        settings.LISTING_PAGE_NAMES = ['listing']
        self.site = SiteInfo(settings, TEST_SITE.path)
        self.site.refresh()
        settings.site = self.site.content_node

    def test_homepage(self):
        assert self.site.content_node.listing_url == "/index.html"

    def test_regular_page(self):
        """Tests a non-listing page"""
        page = self.site.content_node.children[1].children[2].pages[0]
        assert page.name == "introducing-hyde.html"
        assert page.url == "/blog/2009/introducing-hyde.html"

    def test_auto_listing_page(self):
        """Tests listing pages whose filenames match the name of their
        enclosing folders."""
        blog = self.site.content_node.children[1]
        assert blog.name == "blog"
        assert blog.listing_url == "/blog/blog.html"

    def test_lpn_listing_page(self):
        """Tests listing pages whose names are in the LISTING_PAGE_NAMES
        setting"""
        print self.site.content_node.children[1].children[0]
        page = self.site.content_node.children[1].children[0].listing_page
        assert page.name == "listing.html"
        assert page.url == "/blog/2007/listing.html"


class TestCleanUrls:

    def setup_class(self):
        settings.GENERATE_ABSOLUTE_FS_URLS = False
        settings.GENERATE_CLEAN_URLS = True
        settings.APPEND_SLASH = False # See Also: TestCleanUrlsAppendSlash
        settings.LISTING_PAGE_NAMES = ['listing']
        self.site = SiteInfo(settings, TEST_SITE.path)
        self.site.refresh()
        settings.site = self.site.content_node

    def test_homepage(self):
        """Regardless of whether APPEND_SLASH is true, the homepage's url
        cannot be blank"""
        assert self.site.content_node.listing_url == "/"

    def test_regular_page(self):
        """Tests a non-listing page"""
        page = self.site.content_node.children[1].children[2].pages[0]
        assert page.name == "introducing-hyde.html"
        assert page.url == "/blog/2009/introducing-hyde"

    def test_auto_listing_page(self):
        """Tests listing pages whose filenames match the name of their
        enclosing folders."""
        blog = self.site.content_node.children[1]
        assert blog.name == "blog"
        assert blog.listing_url == "/blog"

    def test_lpn_listing_page(self):
        """Tests listing pages whose names are in the LISTING_PAGE_NAMES
        setting"""
        page = self.site.content_node.children[1].children[0].listing_page
        assert page.name == "listing.html"
        assert page.url == "/blog/2007"




class TestCleanUrlsAppendSlash:

    def setup_class(self):
        settings.GENERATE_ABSOLUTE_FS_URLS = False
        settings.GENERATE_CLEAN_URLS = True
        settings.APPEND_SLASH = True 
        settings.LISTING_PAGE_NAMES = ['listing']
        self.site = SiteInfo(settings, TEST_SITE.path)
        self.site.refresh()
        settings.site = self.site.content_node

    def test_homepage(self):
        """Regardless of whether APPEND_SLASH is true, the homepage's url
        cannot be blank"""
        assert self.site.content_node.listing_url == "/"

    def test_regular_page(self):
        """Tests a non-listing page"""
        page = self.site.content_node.children[1].children[2].pages[0]
        assert page.name == "introducing-hyde.html"
        assert page.url == "/blog/2009/introducing-hyde/"

    def test_auto_listing_page(self):
        """Tests listing pages whose filenames match the name of their
        enclosing folders."""
        blog = self.site.content_node.children[1]
        assert blog.name == "blog"
        assert blog.listing_url == "/blog/"

    def test_lpn_listing_page(self):
        """Tests listing pages whose names are in the LISTING_PAGE_NAMES
        setting"""
        page = self.site.content_node.children[1].children[0].listing_page
        assert page.name == "listing.html"
        assert page.url == "/blog/2007/"
