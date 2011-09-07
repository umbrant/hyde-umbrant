from __future__ import with_statement
import os, re,  string, subprocess, codecs
from django.conf import settings
from django.template.loader import render_to_string
from file_system import File
from datetime import datetime
from hydeengine.templatetags.hydetags import xmldatetime
import commands


class YUICompressor:

    @staticmethod
    def process(folder, params):
		class Compressor:
			def visit_file(self, thefile):
				if settings.YUI_COMPRESSOR == None:
					return
				compress = settings.YUI_COMPRESSOR
				if not os.path.exists(compress):
					compress = os.path.join(
							os.path.dirname(
							os.path.abspath(__file__)), "..", compress)

				if not compress or not os.path.exists(compress):
					raise ValueError(
					"YUI Compressor cannot be found at [%s]" % compress)

				tmp_file = File(thefile.path + ".z-tmp")
				status, output = commands.getstatusoutput(
				u"java -jar %s %s > %s" % (compress, thefile.path, tmp_file.path))
				if status > 0:
					print output
				else:
					thefile.delete()
					tmp_file.move_to(thefile.path)

		folder.walk(Compressor(), "*.css")

class FolderFlattener:
    
    @staticmethod
    def process(folder, params): 
        class Flattener:
            def __init__(self, folder, params):
                self.folder = folder
                self.remove_processed_folders = \
                 params["remove_processed_folders"]
                self.previous_folder = None
            
            def visit_file(self, file):
                if not self.folder.is_parent_of(file):
                    file.copy_to(self.folder)
                
            def visit_folder(self, this_folder):                
                if self.previous_folder and self.remove_processed_folders:
                    self.previous_folder.delete()
                if not self.folder.same_as(this_folder):
                    self.previous_folder = this_folder
                    
            def visit_complete(self):
                if self.previous_folder and self.remove_processed_folders:
                    self.previous_folder.delete()

        folder.walk(Flattener(folder, params), params["pattern"])


SITEMAP_CONFIG = \
"""<?xml version="1.0" encoding="UTF-8"?>
<site
  base_url="%(base_url)s"
  store_into="%(sitemap_path)s"
  suppress_search_engine_notify="1"
  verbose="1"
  >
  <urllist  path="%(url_list_file)s"/>
</site>"""

class GoogleSitemapGenerator:
    
    @staticmethod
    def process(folder, params):
        site = settings.CONTEXT['site']
        sitemap_path = params["sitemap_file"]
        url_list_file = File(sitemap_path).parent.child("urllist.txt")
        config_file =  File(sitemap_path).parent.child("sitemap_config.xml")
        urllist = open(url_list_file, 'w')
        for page in site.walk_pages():
            if not page.display_in_list and not page.listing:
                continue
            created = xmldatetime(page.created)
            updated = xmldatetime(page.updated)
            url = page.full_url
            priority = 0.5
            if page.listing:
                priority = 1.0
            changefreq = "weekly"   
            urllist.write(
                "%(url)s lastmod=%(updated)s changefreq=%(changefreq)s \
priority=%(priority).1f\n" 
                % locals())
        urllist.close() 
        base_url = settings.SITE_WWW_URL
        config = open(config_file, 'w')
        config.write(SITEMAP_CONFIG % locals())        
        config.close()
        generator = params["generator"]
        command = u"python %s --config=%s" % (generator, config_file)
        status, output = commands.getstatusoutput(command)
        if status > 0: 
            print output
        File(config_file).delete()
        File(url_list_file).delete()

class RssGenerator:
    """
    Can create a rss feed for a blog and its categories whenever 
    specified in params
    """
    @staticmethod
    def process(folder, params):
        #defaults initialisation
        site = settings.CONTEXT['site']
        node = params['node']
        by_categories = False
        categories = None
        output_folder = 'feed'
        generator = Rss2FeedGenerator()
        if params.has_key('output_folder'):
            output_folder = params['output_folder']
        if params.has_key('generate_by_categories'):
            by_categories = params['generate_by_categories']
        if hasattr(node, 'categories'):
            categories = node.categories
        if categories != None:
            #feed generation for each category
            for category in categories:
                #create a ContentNode adapter for categories to walk through the collection (walk_pages function)
                #the same way than through the site's ContentNode
                category_adapter = ContentNodeAdapter(category)
                feed = generator.generate(category_adapter)
                feed_filename = "%s.xml" % (category["name"].lower().replace(' ','_'))
                feed_url = "%s/%s/%s/%s" % (settings.SITE_WWW_URL, site.url, output_folder, feed_filename)
                category["feed_url"] = feed_url
                RssGenerator._write_feed(feed, output_folder, feed_filename)
        feed = generator.generate(node)
        node.feed_url = "%s/%s/%s/%s" % (settings.SITE_WWW_URL, site.url, output_folder, "feed.xml")
        RssGenerator._write_feed(feed, output_folder, "feed.xml")

    @staticmethod
    def _write_feed(feed, folder, file_name):
        output = os.path.join(settings.CONTENT_DIR, folder)
        if not os.path.isdir(output):
            os.makedirs(output)
        filename = os.path.join(output, file_name)
        with codecs.open(filename, 'w', 'utf-8') as f:
            f.write(feed)

class ContentNodeAdapter:
    """
    Adapter for a collection of posts to fulfill the ContentNode 
    walk_pages contract
    """
    def __init__(self, category):
        self.category = category

    def walk_pages(self):
        for post in self.category["posts"]:
            yield post

class FeedGenerator:
    """
    Base abstract class for the generation of syndication feeds
    """
    def __init__(self):
        pass

    def generate(self, node):
        """
        Template method calling child implementations
        """
        #generate items
        items = self.generate_items(node)
        #generate feed with items inside
        feed = self.generate_feed(items)
        return feed

    def generate_items(self, node):
        raise TypeError('abstract function')

    def generate_feed(self, items):
        raise TypeError('abstract function')

RSS2_FEED = \
"""<?xml version="1.0" encoding="UTF-8"?> 
<rss version="2.0">
   <channel>
      <title>%(title)s</title>
      <link>%(url)s/</link>
      <description>%(description)s</description>
      <language>%(language)s</language>
      <docs>http://blogs.law.harvard.edu/tech/rss</docs>
      <generator>Hyde</generator>
      <webMaster>%(webmaster)s</webMaster>
      %(items)s
   </channel>
</rss>"""

RSS2_ITEMS = \
"""    
      <item>
         <title>%(item_title)s</title>
         <link>%(item_link)s</link>
         <guid>%(guid)s</guid>
         <description><![CDATA[%(description)s]]></description>
         <pubDate>%(publication_date)s</pubDate>
         <author>%(author)s</author>
      </item>"""

class Rss2FeedGenerator(FeedGenerator):
    """
    Implementation of a rss version 2 generator
    """
    def __init__(self):
        FeedGenerator.__init__(self)
        self.re_content = re.compile(r"<!-- Hyde::Article::Begin -->(.*)<!-- Hyde::Article::End -->", re.DOTALL)
        self.date_format = hasattr(settings, "POST_DATE_FORMAT") and \
                            settings.POST_DATE_FORMAT or "%d %b %y %H:%M GMT"

    def generate_items(self, node):
        items = ""
        author = settings.SITE_AUTHOR_EMAIL or [''][0]
        for post in node.walk_pages():
            if hasattr(post, 'listing') and post.listing:
                continue
            item_title = post.title
            item_link = post.full_url
            guid = post.full_url
            description = self.re_content.findall(post.temp_file.read_all())
            description = len(description) > 0 and description[0] or ""
            description = description.decode("utf-8")
            publication_date = post.created.strftime(self.date_format)
            cur_item = RSS2_ITEMS % locals()
            items = "%s%s" % (items, cur_item)
        return items

    def generate_feed(self, items):
        title = settings.SITE_NAME
        url = settings.SITE_WWW_URL
        description = ''
        language = settings.LANGUAGE_CODE or 'en-us'
        webmaster = settings.SITE_AUTHOR_EMAIL
        return RSS2_FEED % locals()

class WhiteSpaceVisitor(object):
    def __init__(self, **kw):
        self.operations = []
        del kw['node']
        for k,v in kw.items():
            if v == True and hasattr(self, k):
                self.operations.append(getattr(self, k))
            elif not hasattr(self, k):
                raise Exception("Unknown WhiteSpaceRemover operation: %s" % k)

    def visit_file(self, a_file):
        for oper in self.operations:
            oper(a_file)

    def remove_document_leading_whitespace(self, a_file):
        lines = a_file.read_all().splitlines()
        while lines[0] == '':
            lines.pop(0)
        a_file.write(unicode("\n".join(lines), 'utf8'))

class WhiteSpaceRemover:
    @staticmethod
    def process(folder, params):
        visitor = WhiteSpaceVisitor(**params)

        extensions = ['html', 'xml']
        if params.has_key('extensions'):
            extensions = params['extensions']

        for ext in extensions:
            folder.walk(visitor, '*.%s' % ext)
