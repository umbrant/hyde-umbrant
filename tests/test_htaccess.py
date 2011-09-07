"""
Tests of .htaccess file generation. 

For now, this just checks whether the demo site's generated .htaccess file
matches a known good file.
"""

import os
import sys
from django.conf import settings

TEST_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(TEST_ROOT + "/..")
 
sys.path = [ROOT] + sys.path

from hydeengine.file_system import File, Folder
from hydeengine import url, Initializer, setup_env
from hydeengine.templatetags.hydetags \
        import RenderHydeListingPageRewriteRulesNode as htaccessgen

TEST_SITE = Folder(TEST_ROOT).child_folder("test_site")

def setup_module(module):
    Initializer(TEST_SITE.path).initialize(ROOT, template="test", force=True)
    setup_env(TEST_SITE.path)

def teardown_module(module):
    TEST_SITE.delete()

class TestHtaccess:
    def test_listing_page_rewite_rule_generator(self):
        # test with two names
        settings.LISTING_PAGE_NAMES = ['listing', 'index']
        expected = r"""
###  BEGIN GENERATED REWRITE RULES  ####

RewriteCond %{REQUEST_FILENAME}/listing.html -f
RewriteRule ^(.*) $1/listing.html

RewriteCond %{REQUEST_FILENAME}/index.html -f
RewriteRule ^(.*) $1/index.html

####  END GENERATED REWRITE RULES  ####
"""
        actual = htaccessgen().render('')
        assert actual.strip() == expected.strip()

        # test with no names
        settings.LISTING_PAGE_NAMES = []
        actual = htaccessgen().render('')
        assert actual == ""
