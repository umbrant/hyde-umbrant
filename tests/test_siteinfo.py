"""

uses py.test

sudo easy_install py

http://codespeak.net/py/dist/test.html

"""
import os
import sys
import time as sleeper
from datetime import time, datetime, timedelta
import unittest
from threading import Thread
from Queue import Queue
from Queue import Empty

from django.conf import settings
from util import assert_html_equals

TEST_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(TEST_ROOT + "/..")

sys.path = [ROOT] + sys.path

from hydeengine.file_system import File, Folder
from hydeengine import url, Initializer, Generator, setup_env
from hydeengine.siteinfo import SiteNode, SiteInfo, Page
from hydeengine.site_post_processors import FolderFlattener

TEST_ROOT = Folder(TEST_ROOT)
TEST_SITE = TEST_ROOT.child_folder("test_site")

def setup_module(module):
    Initializer(TEST_SITE.path).initialize(ROOT, template='test', force=True)
    setup_env(TEST_SITE.path)

def teardown_module(module):
    TEST_SITE.delete()

class TestFilters:

    def setup_method(self, method):
        self.files = []

    def teardown_method(self, method):
        for f in self.files:
            f.delete()

    def test_filters(self):
        site = SiteInfo(settings, TEST_SITE.path)
        for name in [".banjo", ".hidden", "junk.abc~"]:
            f = File(site.content_folder.child(name))
            self.files.append(f)
            f.write("junk")

        git = site.content_folder.child_folder(".git")
        git_child = git.child_folder("child")
        git_child_pack = File(git_child.child("pack"))
        git.make()
        git_child.make()
        git_index = File(git.child("index"))
        git_index.write("junk")
        git_child_pack.write("junk")

        original_exclude = settings.FILTER['exclude']
        original_include = settings.FILTER['include']
        settings.FILTER = {}
        site = SiteInfo(settings, TEST_SITE.path)
        site.refresh()

        for f in self.files:
            assert site.find_resource(f)

        assert site.find_node(git)
        assert site.find_resource(git_index)
        assert site.find_node(git_child)
        assert site.find_resource(git_child_pack)

        settings.FILTER = {
            'include': (),
            'exclude': (".*","*~")
        }

        site = SiteInfo(settings, TEST_SITE.path)
        site.refresh()

        for f in self.files:
            assert not site.find_resource(f)

        assert not site.find_node(git)
        assert not site.find_resource(git_index)
        assert not site.find_node(git_child)
        assert not site.find_resource(git_child_pack)

        settings.FILTER = {
            'include': (".banjo",),
            'exclude': (".*","*~")
        }

        site = SiteInfo(settings, TEST_SITE.path)
        site.refresh()

        for f in self.files:
            if f.name == ".banjo":
                assert site.find_resource(f)
            else:
                assert not site.find_resource(f)

        assert not site.find_node(git)
        assert not site.find_resource(git_index)

        settings.FILTER['exclude']  = original_exclude
        settings.FILTER['include']  = original_include

        self.files.append(git)


class TestSiteInfo:

    def setup_method(self, method):
        self.site = SiteInfo(settings, TEST_SITE.path)
        self.site.refresh()

    def assert_node_complete(self, node, folder):
        assert node.folder.path == folder.path
        test_case = self
        class Visitor(object):

            def visit_folder(self, folder):
                if not folder.allow(**test_case.site.settings.FILTER):
                    return
                child = node.find_child(folder)
                assert child
                test_case.assert_node_complete(child, folder)

            def visit_file(self, a_file):
                if not a_file.allow(**test_case.site.settings.FILTER):
                    return
                assert node.find_resource(a_file)

        folder.list(Visitor())

    def test_population(self):
        assert self.site.name == "Your Site"
        self.assert_node_complete(self.site.content_node,
                                    TEST_SITE.child_folder("content"))
        self.assert_node_complete(self.site.media_node,
                                    TEST_SITE.child_folder("media"))
        self.assert_node_complete(self.site.layout_node,
                                    TEST_SITE.child_folder("layout"))

    def test_type(self):
        def assert_node_type(node_dir, type):
           node = self.site.find_child(Folder(node_dir))
           assert node
           assert Folder(node_dir).same_as(node.folder)
           for child in node.walk():
               assert child.type == type
        assert_node_type(settings.CONTENT_DIR, "content")
        assert_node_type(settings.MEDIA_DIR, "media")
        assert_node_type(settings.LAYOUT_DIR, "layout")


    def test_attributes(self):
        for node in self.site.walk():
           self.assert_node_attributes(node)
           for resource in node.resources:
               self.assert_resource_attributes(resource)

    def assert_node_attributes(self, node):
        fragment = self.get_node_fragment(node)
        if node.type == "content":
            fragment = node.folder.get_fragment(self.site.content_folder)
        elif node.type == "media":
            fragment = node.folder.get_fragment(self.site.folder)
        if node.type in ("content", "media"):
            fragment = ("/" + fragment.strip("/")).rstrip("/")
            assert fragment == node.url
            assert settings.SITE_WWW_URL + fragment == node.full_url
        else:
            assert not node.url
            assert not node.full_url

        if node.type == "content":
            for ancestor in node.ancestors:
                assert(
                    ancestor.folder.is_ancestor_of(node.folder) or
                    ancestor.folder.same_as(node.folder))

        assert node.source_folder == node.folder
        if not node == self.site and node.type not in ("content", "media"):
            assert not node.target_folder
            assert not node.temp_folder
        else:
            assert node.target_folder.same_as(Folder(
                            os.path.join(settings.DEPLOY_DIR,
                                fragment.lstrip("/"))))
            assert node.temp_folder.same_as(Folder(
                            os.path.join(settings.TMP_DIR,
                                fragment.lstrip("/"))))

    def assert_resource_attributes(self, resource):
        node = resource.node
        fragment = self.get_node_fragment(node)
        assert resource.name == resource.file.name
        assert resource.file.size == os.path.getsize(resource.file.path)
        if resource.node.type in ("content", "media"):
            assert (resource.url ==
                        url.join(node.url, resource.file.name))
            assert (resource.full_url ==
                        url.join(node.full_url, resource.file.name))
            assert resource.target_file.same_as(
                    File(node.target_folder.child(
                            resource.file.name)))
            assert resource.temp_file.same_as(
                    File(node.temp_folder.child(resource.file.name)))
        else:
            assert not resource.url
            assert not resource.full_url
        if resource.node.type == "content":
            self.assert_page_attributes(resource)

    def assert_page_attributes(self, page):
        if page.page_name in (
                "about", "blog", "listing", "2008", "2009", "index"):
            assert page.listing
            assert page.node.listing_page
            assert page.node.listing_page == page

            assert not page.display_in_list
        else:
            assert not page.listing
            if page.file.kind == "html":
                assert page.display_in_list
        assert page.module == page.node.module

        assert page.source_file.parent.same_as(page.node.folder)
        assert page.source_file.name == page.file.name

    def get_node_fragment(self, node):
        fragment = ''
        if node.type == "content":
            fragment = node.folder.get_fragment(self.site.content_folder)
        elif node.type == "media":
            fragment = node.folder.get_fragment(self.site.folder)
        return fragment


class MonitorTests(object):
    def clean_queue(self):
        while not self.queue.empty():
            try:
                self.queue.get()
                self.queue.task_done()
            except Empty:
                break

    def setup_class(cls):
        cls.site = None
        cls.queue = Queue()

    def teardown_class(cls):
        if cls.site:
            cls.site.dont_monitor()

    def setup_method(self, method):
        self.site = SiteInfo(settings, TEST_SITE.path)
        self.site.refresh()
        self.exception_queue = Queue()
        self.clean_queue()
        assert self.queue.empty()

class TestSiteInfoMonitoring(MonitorTests):

    def change_checker(self, change, path):
        try:
            changes = self.queue.get(block=True, timeout=30)
            self.queue.task_done()
            assert changes
            assert not changes['exception']
            assert changes['change'] == change
            assert changes['resource']
            assert changes['resource'].file.path == path
        except:
            self.exception_queue.put(sys.exc_info())
            raise

    def test_monitor_stop(self):
        m = self.site.monitor()
        self.site.dont_monitor()
        assert not m.isAlive()

    def test_modify(self):
        self.site.monitor(self.queue)
        path = self.site.media_folder.child("css/base.css")
        t = Thread(target=self.change_checker,
                    kwargs={"change":"Modified", "path":path})
        t.start()
        os.utime(path, None)
        t.join()
        assert self.exception_queue.empty()

    def test_add(self, direct=False):
        self.site.monitor(self.queue)
        path = self.site.layout_folder.child("test.ggg")
        t = Thread(target=self.change_checker,
                    kwargs={"change":"Added", "path":path})
        t.start()
        f = File(path)
        f.write("test")
        t.join()
        if not direct:
            f.delete()
        assert self.exception_queue.empty()

    def test_delete(self):
        f = File(self.site.content_folder.child("test.ddd"))
        f.write("test")
        self.site.refresh()
        self.clean_queue()
        self.site.monitor(self.queue)
        t = Thread(target=self.change_checker,
                    kwargs={"change":"Deleted", "path":f.path})
        t.start()
        f.delete()
        t.join()
        assert self.exception_queue.empty()

    def node_remove_checker(self, path):
        try:
            changes = self.queue.get(block=True, timeout=30)
            self.queue.task_done()
            assert changes
            assert not changes['exception']
            assert changes['change'] == change
            assert changes['node']
            assert changes['node'].folder.path == path
        except:
            self.exception_queue.put(sys.exc_info())
            raise

    def test_delete_dir(self):
        d = self.site.content_folder.child_folder("test_test")
        f = File(d.child("test.nnn"))
        d.make()
        f.write("test")
        self.site.refresh()
        self.clean_queue()
        self.site.monitor(self.queue)
        t = Thread(target=self.node_remove_checker,
                    kwargs={"change":"NodeRemoved", "path":d.path})
        t.start()
        d.delete()
        t.join()
        d.delete()
        assert self.exception_queue.empty()

class TestYAMLProcessor(MonitorTests):

    def yaml_checker(self, path, vars):
           try:
               changes = self.queue.get(block=True, timeout=30)
               self.queue.task_done()
               assert changes
               assert not changes['exception']
               resource = changes['resource']
               assert resource
               assert resource.file.path == path
               # from hydeengine.content_processors import YAMLContentProcessor
               # YAMLContentProcessor.process(resource)
               for key, value in vars.iteritems():
                   assert hasattr(resource, key)
                   print(value)
                   print(getattr(resource, key))
                   assert getattr(resource, key) == value
           except:
               self.exception_queue.put(sys.exc_info())
               raise

    def test_variables_are_added(self):
        vars = {}
        vars["title"] = "Test Title"
        vars["created"] = datetime.now()
        vars["updated"] = datetime.now() + timedelta(hours=1)
        content = "{%hyde\n"
        for key, value in vars.iteritems():
            content += "    %s: %s\n" % (key, value)
        content +=  "%}"
        out = File(self.site.content_folder.child("test_yaml.html"))
        self.site.monitor(self.queue)
        t = Thread(target=self.yaml_checker,
                        kwargs={"path":out.path, "vars":vars})
        t.start()
        out.write(content)
        t.join()
        assert self.exception_queue.empty()
        # Ensure default values are added for all pages
        #
        temp = File(self.site.content_folder.child("test_var.html"))
        temp.write('text')
        page = Page(temp, self.site.content_node)
        assert not page.title
        assert page.created == datetime.strptime("2000-01-01", "%Y-%m-%d")
        assert page.updated == page.created
        temp.delete()
        out.delete()

    def test_dates_are_converted_to_datetime(self):
        vars = {}
        vars["created"] = datetime.now().date()
        vars["updated"] = (datetime.now() + timedelta(hours=1)).date()
        content = "{%hyde\n"
        for key, value in vars.iteritems():
            content += "    %s: %s\n" % (key, value)
        content +=  "%}"
        out = File(self.site.content_folder.child("test_yaml.html"))
        out.write(content)
        page = Page(out, self.site.content_node)
        assert not page.title
        assert page.created == datetime.combine(vars["created"], time())
        assert page.updated == datetime.combine(vars["updated"], time())
        out.delete()


class TestSorting(MonitorTests):
    def test_pages_are_sorted(self):
        prev_node = None
        prev_page = None
        for page in self.site.content_node.walk_pages():
            if not prev_node or not prev_node == page.node:
                assert not page.prev
            elif prev_node == page.node and page.display_in_list:
                if prev_page:
                    assert page.prev
                    assert page.prev == prev_page
                else:
                    assert not page.prev
            if page.display_in_list:
                prev_page = page
            prev_node = page.node

class TestProcessing(MonitorTests):
    def checker(self, asserter):
           try:
               changes = self.queue.get(block=True, timeout=30)
               self.queue.task_done()
               assert changes
               assert not changes['exception']
               resource = changes['resource']
               assert resource
               asserter(resource)
           except:
               self.exception_queue.put(sys.exc_info())
               raise

    def assert_valid_css(self, actual_css_resource):
        expected_text = File(
                TEST_ROOT.child("test_dest.css")).read_all()
        self.generator.process(actual_css_resource)

        # Ensure source file is not changed
        # The source should be copied to tmp and then
        # the processor should do its thing.
        original_source = File(
                TEST_ROOT.child("test_src.css")).read_all()
        source_text = actual_css_resource.file.read_all()
        assert original_source == source_text
        actual_text = actual_css_resource.temp_file.read_all()
        assert expected_text == actual_text

    def test_process_css_with_templates(self):
        original_MP = settings.MEDIA_PROCESSORS
        original_site = settings.SITE_ROOT
        settings.MEDIA_PROCESSORS = {"*":{".css":
        ('hydeengine.media_processors.TemplateProcessor',)}}
        settings.SITE_ROOT = "www.hyde-test.bogus/"
        self.generator = Generator(TEST_SITE.path)
        self.generator.build_siteinfo()
        source = File(TEST_ROOT.child("test_src.css"))
        self.site.refresh()
        self.site.monitor(self.queue)
        t = Thread(target=self.checker,
                        kwargs={"asserter":self.assert_valid_css})
        t.start()
        source.copy_to(self.site.media_folder.child("test.css"))
        t.join()
        settings.MEDIA_PROCESSORS = original_MP
        settings.SITE_ROOT = original_site
        assert self.exception_queue.empty()

    def assert_valid_html(self, actual_html_resource):
        expected_text = File(
                TEST_ROOT.child("test_dest.html")).read_all()
        self.generator.process(actual_html_resource)

        # Ensure source file is not changed
        # The source should be copied to tmp and then
        # the processor should do its thing.
        original_source = File(
                TEST_ROOT.child("test_src.html")).read_all()
        source_text = actual_html_resource.file.read_all()
        assert original_source == source_text
        actual_text = actual_html_resource.temp_file.read_all()
        assert_html_equals(expected_text, actual_text)

    def assert_valid_markdown(self, actual_html_resource):
        expected_text = File(
                TEST_ROOT.child("dst_test_markdown.html")).read_all()
        self.generator.process(actual_html_resource)
        # Ensure source file is not changed
        # The source should be copied to tmp and then
        # the processor should do its thing.
        original_source = File(
                TEST_ROOT.child("src_test_markdown.html")).read_all()
        source_text = actual_html_resource.file.read_all()
        assert original_source == source_text
        actual_text = actual_html_resource.temp_file.read_all()
        assert_html_equals(expected_text, actual_text)

    def assert_valid_textile(self, actual_html_resource):
        expected_text = File(
                TEST_ROOT.child("dst_test_textile.html")).read_all()
        self.generator.process(actual_html_resource)

        # Ensure source file is not changed
        # The source should be copied to tmp and then
        # the processor should do its thing.
        original_source = File(
                TEST_ROOT.child("src_test_textile.html")).read_all()
        source_text = actual_html_resource.file.read_all()
        assert original_source == source_text
        actual_text = actual_html_resource.temp_file.read_all()
        assert_html_equals(expected_text, actual_text)

    def assert_valid_restructuredtext(self, actual_html_resource):
        expected_text = File(
                TEST_ROOT.child("dst_test_restructuredtext.html")).read_all()
        self.generator.process(actual_html_resource)
        # Ensure source file is not changed
        # The source should be copied to tmp and then
        # the processor should do its thing.
        original_source = File(
                TEST_ROOT.child("src_test_restructuredtext.html")).read_all()
        source_text = actual_html_resource.file.read_all()
        assert original_source == source_text
        actual_text = actual_html_resource.temp_file.read_all()
        assert_html_equals(expected_text, actual_text)

    def test_process_page_rendering(self):
        self.generator = Generator(TEST_SITE.path)
        self.generator.build_siteinfo()
        source = File(TEST_ROOT.child("test_src.html"))
        self.site.refresh()
        self.site.monitor(self.queue)
        t = Thread(target=self.checker,
                        kwargs={"asserter":self.assert_valid_html})
        t.start()
        source.copy_to(self.site.content_folder.child("test_render.html"))
        t.join()
        assert self.exception_queue.empty()

    def assert_layout_not_rendered(self, actual_html_resource):
        self.generator.process(actual_html_resource)
        assert not actual_html_resource.temp_file.exists

    def test_underscored_pages_are_not_rendered(self):
        self.generator = Generator(TEST_SITE.path)
        self.generator.build_siteinfo()
        source = File(TEST_ROOT.child("test_src.html"))
        target = File(self.site.content_folder.child("_test.html"))
        self.site.refresh()
        self.site.monitor(self.queue)
        t = Thread(target=self.checker,
                        kwargs={"asserter":self.assert_layout_not_rendered})
        t.start()
        source.copy_to(target)
        t.join()
        target.delete()
        assert self.exception_queue.empty()

    def test_markdown(self):
        try:
            import markdown
        except ImportError:
            markdown = False
            print "Markdown not found, skipping unit tests"

        if markdown:
            self.generator = Generator(TEST_SITE.path)
            self.generator.build_siteinfo()
            source = File(TEST_ROOT.child("src_test_markdown.html"))
            self.site.refresh()
            assert self.queue.empty()
            self.site.monitor(self.queue)
            t = Thread(target=self.checker,
                            kwargs={"asserter":self.assert_valid_markdown})
            t.start()
            target = File(self.site.content_folder.child("test_md.html"))
            source.copy_to(target)
            t.join()
            target.delete()
            assert self.exception_queue.empty()

    def test_textile(self):
        try:
            import textile
        except ImportError:
            textile = False
            print "Textile not found, skipping unit tests"

        if textile:
            self.generator = Generator(TEST_SITE.path)
            self.generator.build_siteinfo()
            source = File(TEST_ROOT.child("src_test_textile.html"))
            self.site.refresh()
            self.site.monitor(self.queue)
            t = Thread(target=self.checker,
                            kwargs={"asserter":self.assert_valid_textile})
            t.start()
            target = File(self.site.content_folder.child("test_textile.html"))
            source.copy_to(target)
            t.join()
            target.delete()
            assert self.exception_queue.empty()

    def test_restructuredtext(self):
        try:
            import docutils
        except ImportError:
            docutils = False
            print "Docutils not found, skipping unit tests"

        if docutils:
            self.generator = Generator(TEST_SITE.path)
            self.generator.build_siteinfo()
            source = File(TEST_ROOT.child("src_test_restructuredtext.html"))
            self.site.refresh()
            assert self.queue.empty()
            self.site.monitor(self.queue)
            t = Thread(target=self.checker,
                            kwargs={"asserter":self.assert_valid_restructuredtext})
            t.start()
            target = File(self.site.content_folder.child("test_rest.html"))
            source.copy_to(target)
            t.join()
            target.delete()
            assert self.exception_queue.empty()

    def assert_prerendered(self, actual_html_resource):
        expected_text = File(
                TEST_ROOT.child("test_src.html")).read_all()

        self.generator.process(actual_html_resource)

        # Ensure source file is not changed
        # The source should be copied to tmp and then
        # the processor should do its thing.
        source_text = actual_html_resource.file.read_all()
        assert expected_text == source_text
        actual_text = actual_html_resource.temp_file.read_all()

        # Since the file is prerendered, there should be no change
        assert expected_text == actual_text


    def test_prerendered(self):
        self.generator = Generator(TEST_SITE.path)
        self.generator.build_siteinfo()
        source = File(TEST_ROOT.child("test_src.html"))
        self.site.refresh()
        self.site.dont_monitor()
        self.site.monitor(self.queue)
        t = Thread(target=self.checker,
                        kwargs={"asserter":self.assert_prerendered})
        t.start()
        target = File(self.site.content_folder.child("prerendered/test2.html"))
        source.copy_to(target)
        t.join()
        target.delete()
        assert self.exception_queue.empty()

    def test_node_injector(self):
        self.generator = Generator(TEST_SITE.path)
        self.generator.build_siteinfo()
        site = settings.CONTEXT['site']
        blog_node = site.find_node(TEST_SITE.child_folder('content/blog'))
        self.generator.pre_process(site)
        for post in site.walk_pages():
            assert post.blog_node
            assert post.blog_node == blog_node

class TestPreProcessors:

    def test_categories(self):
        self.generator = Generator(TEST_SITE.path)
        self.generator.build_siteinfo()
        context = settings.CONTEXT
        site = context['site']
        self.generator.pre_process(site)
        blog_node = site.find_node(TEST_SITE.child_folder('content/blog'))
        assert hasattr(blog_node, 'categories')
        assert len(blog_node.categories) == 4
        found = False
        for category in blog_node.categories:
            if category['name'] == 'wishes':
                found = True
                assert category['description'] == settings.CATEGORIES['wishes']['description']
                assert len(category['posts']) == 3

        if not found:
            assert(False, "Category *wishes* not found")

class TestPostProcessors:

    def test_folder_flattener(self):
        settings.MEDIA_PROCESSORS = {}
        settings.SITE_POST_PROCESSORS = {
            "blog" : {
                "hydeengine.site_post_processors.FolderFlattener" : {
                        'remove_processed_folders': True,
                        'pattern':"*.html"
                }
            }
        }

        self.generator = Generator(TEST_SITE.path)
        self.generator.generate()

        blog = Folder(settings.DEPLOY_DIR).child_folder("blog")

        class TestFlattener:
            def __init__(self):
                self.files = []

            def visit_folder(self, folder):
                assert folder.name in ("blog")

            def visit_file(self, a_file):
                self.files.append(a_file.name)

        tester = TestFlattener()
        blog.list(tester)
        blog_src = Folder(settings.CONTENT_DIR).child_folder("blog")

        class VerifyFlattener:
            @staticmethod
            def visit_file(a_file):
                try:
                    tester.files.index(a_file.name)
                except:
                    assert False
        blog_src.walk(VerifyFlattener)
