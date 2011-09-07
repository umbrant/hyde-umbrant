# -*- coding: utf-8 -*-
"""
PRE PROCESSORS

Can be launched before the parsing of each templates and
after the loading of site info.
"""

from __future__ import with_statement

import codecs
import operator
import os
import urllib

from django.conf import settings
from django.template.loader import render_to_string

import hydeengine.url as url


class Category:
    """
    Plain object
    """
    def __init__(self, name="", meta={}):
        self.posts = []
        self.feed_url = None
        self.archive_url = None
        self.name = name
        for key, value in meta.iteritems():
            if not hasattr(Category, key):
                setattr(Category, key, None)
            setattr(self, key, value)

    @property
    def name(self):
        return self.name

    @property
    def posts(self):
        return self.posts

    @property
    def feed_url(self):
        return self.feed_url

    @property
    def archive_url(self):
        return self.archive_url

class CategoriesManager:
    """Category Manager

    Fetch the category(ies) from every post under the given node
    and creates a reference on them in the node.

    By default it generates also listing pages displaying every posts belonging
    to each category. You can turn it off by setting `archiving` param to `False`

       `params` : must contain the `template` key which will be used to render
                  the archive page
                  may contain the `output_folder` key to specify the destination
                  folder of the generated listing pages (by default: 'archives')
                  may contain the `listing_template` key. this template will be used
                  to render the index page of the archive
    """
    @staticmethod
    def process(folder, params):
        context = settings.CONTEXT
        site = context['site']
        node = params['node']
        meta = params.get('meta', {})
        categories = {}
        for post in node.walk_pages():
            if hasattr(post, 'categories') and post.categories != None:
                for category in post.categories:
                    if categories.has_key(category) is False:
                        categories[category] = Category(category)
                    categories[category].posts.append(post)
                    categories[category].posts.sort(key=operator.attrgetter("created"), reverse=True)
        l = []
        for category in categories.values():
            d = {"name": category.name,
                 "posts": category.posts,
                 "feed_url": category.feed_url,
                 "post_count": len(category.posts)}
            d.update(meta.get(category.name, {}))
            l.append(d)

        node.categories = l
        for sub_node in node.walk():
            sub_node.categories = l

        #archiving section
        archiving = False
        if 'archiving' in params.keys():
            archiving = params['archiving'] is True

        if archiving:
            categories = l
            #: defining the output folder - customisable
            if hasattr(settings,"CATEGORY_ARCHIVES_DIR"):
                relative_folder = output_folder = settings.CATEGORY_ARCHIVES_DIR
            else:
                relative_folder = output_folder = 'archives'
            if 'output_folder' in params and params['output_folder'] is not None \
                    and len(params['output_folder']) > 0:
                relative_folder = output_folder = params['output_folder']
            output_folder = os.path.join(settings.TMP_DIR, output_folder)
            if not os.path.isdir(output_folder):
                os.makedirs(output_folder)

            #: fetching default archive template
            template = None
            if 'template' in params:
                template = os.path.join(settings.LAYOUT_DIR, params['template'])
            else:
                raise ValueError("No template reference in CategoriesManager's settings")

            clean_urls = False
            if hasattr(settings, "GENERATE_CLEAN_URLS"):
                clean_urls = settings.GENERATE_CLEAN_URLS

            for category in categories:
                cat_url = urllib.quote_plus(category["name"])
                if clean_urls:
                    cat_folder = os.path.join(output_folder, cat_url)
                    if not os.path.isdir(cat_folder):
                        os.makedirs(cat_folder)
                    archive_resource = "%s/index.html" % cat_url
                    category["archive_url"] = "/%s/%s" % (relative_folder,
                                                            cat_url)
                else:
                    archive_resource = "%s.html" % cat_url
                    category["archive_url"] = "/%s/%s" % (relative_folder,
                                                            archive_resource)
                category["archive_resource"] = archive_resource

            for category in categories:
                #: stubbing page object for use in template
                page = {
                    'module': node.module,
                    'node': node,
                    'title': relative_folder,
                }
                context.update({'category':category["name"],
                                'posts': category["posts"],
                                'categories': categories,
                                'page': page})
                output = render_to_string(template, context)
                with codecs.open(os.path.join(output_folder, \
                                     category['archive_resource']), \
                                     "w", "utf-8") as file:
                    file.write(output)

            # listing page for categories
            if 'listing_template' in params:
                template = os.path.join(settings.LAYOUT_DIR, params['listing_template'])
                archive_resource = "%s/index.html" % output_folder

                context.update({'categories': categories})
                output = render_to_string(template, context)
                with codecs.open(os.path.join(output_folder, \
                                     archive_resource), \
                                     "w", "utf-8") as file:
                    file.write(output)


class NodeInjector(object):
    """Node Injector

    Finds the node that represents the given path and injects it with the given
    variable name into all the posts contained in the current node.
    """
    @staticmethod
    def process(folder, params):
        context = settings.CONTEXT
        site = context['site']
        node = params['node']
        try:
            varName = params['variable']
            path = params['path']
            params['injections'] = { varName: path }
        except KeyError:
            pass

        for varName, path in params['injections'].iteritems():
            nodeFromPathFragment = site.find_node(site.folder.parent.child_folder(path))
            if not nodeFromPathFragment:
                continue
            for post in node.walk_pages():
                setattr(post, varName, nodeFromPathFragment)


class ResourcePairer(object):
    @staticmethod
    def process(folder, params):
        site = settings.CONTEXT['site']
        node = params['node']

        # fetch or setup content and pairs
        content_name = params.get('name', 'media_content')
        content = site.__dict__.setdefault(content_name, {})

        variable = params.get('variable', 'media')
        rvariable = params.get('recursive_variable', 'media')
        recursive = params.get('recursive', True)

        if node.type == 'content':
            while content:
                path, node = content.popitem()
                setattr(node, variable, [])
                setattr(node, rvariable, [])
            content.update(dict([(page.url, page.node) for page in node.walk_pages()]))
        elif node.type == 'media':
            for resource in node.walk_resources():
                # strip top directories (eg. media/images/) to be able to match
                path = resource.node.fragment
                path = path[path.index('/', 1):]

                # append the resource for all matching directories
                key = variable
                node = content.get(path)
                while node is not None:
                    resources = node.__dict__.setdefault(key, [])
                    resources.append(resource)
                    resources.sort(key=lambda x: x.file.last_modified, reverse=True)

                    key = rvariable
                    node = recursive and node.parent or None


class RecursiveAttributes(object):
    """Adds recursivity base on attributes with dots"""
    def __setattr__(self, key, value):
        parts = key.split('.', 1)
        if len(parts) == 1:
            self.__dict__[key] = value
        else:
            target = getattr(self, parts[0], None)
            if target is None:
                target = RecursiveAttributes()
                self.__dict__[parts[0]] = target

            setattr(target, parts[1], value)

    def __getattr__(self, key):
        parts = key.split('.', 1)
        try:
            if len(parts) == 1:
                return self.__dict__[key]
            else:
                return getattr(self.__dict__[parts[0]], parts[1])
        except KeyError:
            raise AttributeError('Unknown attribute: %s' % (key,))

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join(['%s=%r' % (k, v) for k, v in self.__dict__.items() if not k.startswith('_')]))


class ImageMetadata(object):
    """Image metadata retriever based on PIL"""
    DEFAULT_MAPPING = {'iptc.description': 'caption'}

    # A subset of the IPTC Information Interchange Model
    # mapping extracted from:
    # http://www.iptc.org/std/IIM/
    IIM_MAPPING = {(2, 90):   'city',
                   (2, 101):  'country',
                   (2, 100):  'country_code',
                   (2, 120):  'description',
                   (2, 25):   'keywords',
                   (2, 116):  'copyright',
                   (2, 105):  'headline',
                   (2, 5):    'title',
                   (2, 15):   'category',
                   (2, 20):   'supplemental_category'}

    @staticmethod
    def process(folder, params):
        import PIL.ExifTags
        import PIL.Image
        import PIL.IptcImagePlugin

        class AttributeMapper(RecursiveAttributes):
            def __init__(self, values, mapping, internal_mapping={}):
                if values is None:
                    return

                for tag, name in mapping.iteritems():
                    value = values.get(tag)
                    if value is None:
                        continue

                    if name in internal_mapping:
                        for extra_tag, extra_name in internal_mapping[name].iteritems():
                            extra_value = value.get(extra_tag)
                            if extra_value is not None:
                                setattr(self, '.'.join((name, extra_name)), extra_value)
                    else:
                        setattr(self, name, value)

        # setup the mapping
        mapping = ImageMetadata.DEFAULT_MAPPING.copy()
        mapping.update(params.get('mapping', {}))

        # loop through all metadata resources
        node = params['node']
        if node.type == 'media':
            for resource in node.walk_resources():
                try:
                    image = PIL.Image.open(resource.source_file.path)
                except:
                    continue

                # not all images have exif information
                try:
                    resource.meta = RecursiveAttributes()
                    resource.meta.exif = AttributeMapper(image._getexif(), PIL.ExifTags.TAGS, {'GPSInfo': PIL.ExifTags.GPSTAGS})
                except AttributeError:
                    pass

                iptc = PIL.IptcImagePlugin.getiptcinfo(image)
                resource.meta.iptc = AttributeMapper(iptc, ImageMetadata.IIM_MAPPING)

                # use the mapping to add easier access to some attributes
                for key, attr in mapping.items():
                    try:
                        setattr(resource.meta, attr, getattr(resource.meta, key))
                    except AttributeError:
                        pass


class ImageMetadataPyExiv2(object):
    """Image metadata retriever based on pyexiv2"""
    DEFAULT_MAPPING = {'Iptc.Application2.Caption': 'caption'}

    @staticmethod
    def process(folder, params):
        import pyexiv2

        class AttributeMapper(RecursiveAttributes):
            def __init__(self, keys, image):
                super(AttributeMapper, self).__init__()
                for key in keys:
                    setattr(self, key, image[key])

        # setup default mapping + local overrides
        mapping = ImageMetadataPyExiv2.DEFAULT_MAPPING.copy()
        mapping.update(params.get('mapping', {}))

        # loop through all media resources
        node = params['node']
        if node.type == 'media':
            for resource in node.walk_resources():
                try:
                    image = pyexiv2.Image(resource.source_file.path)
                    image.readMetadata()
                except:
                    continue

                # setup all retrieved keys in resource.meta
                keys = set(image.exifKeys() + image.iptcKeys())
                resource.meta = AttributeMapper(keys, image)

                # use the mapping to add easier access to some attributes
                for key, attr in mapping.items():
                    if key in keys:
                        setattr(resource.meta, attr, getattr(resource.meta, key))
                        
class InclusionManager:
    """Inclusion Manager

    Include listing page properties into corresponding node
    """
    @staticmethod
    def process(folder, params):
        context = settings.CONTEXT
        site = context['site']
        node = params['node']

        inclusions = params['include']

        for inc_key, info in inclusions.iteritems():
            for p in node.walk_pages():
                if p.listing:
                    value = getattr(p, info['field'])
                    if value is None:
                        value = getattr(p.node, info['fallback'])
                    setattr(p.node,inc_key, value)

