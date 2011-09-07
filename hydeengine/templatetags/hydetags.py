from datetime import datetime
import operator
import os
import re
import string

from django import template
from django.conf import settings
from django.template import Template
from django.template.loader import render_to_string
from django.template.defaultfilters import truncatewords_html, stringfilter
from django.template.loader_tags import do_include
from django.template import Library
from django.utils.safestring import mark_safe

from hydeengine.file_system import File, Folder


marker_start = "<!-- Hyde::%s::Begin -->"
marker_end = "<!-- Hyde::%s::End -->"
current_referrer = 'current_referrer'

register = Library()


class HydeContextNode(template.Node):
    def __init__(self):
        pass

    def render(self, context):
        return ""


@register.tag(name="hyde")
def hyde_context(parser, token):
    return HydeContextNode()


@register.tag(name="excerpt")
def excerpt(parser, token):
    nodelist = parser.parse(('endexcerpt',))
    parser.delete_first_token()
    return BracketNode("Excerpt", nodelist)


@register.tag(name="article")
def article(parser, token):
    nodelist = parser.parse(('endarticle',))
    parser.delete_first_token()
    return BracketNode("Article", nodelist)


@register.tag(name="refer")
def refer_page(parser, token):
    bits = token.contents.split()
    if (len(bits) < 5 or
        bits[1] != 'to' or
        bits[3] != 'as'):
        raise TemplateSyntaxError("Syntax: 'refer to _page_path_ as _namespace_'")
    return ReferNode(bits[2], bits[4])


@register.tag(name="reference")
def reference(parser, token):
    bits = token.contents.split()
    if len(bits) < 2:
        raise TemplateSyntaxError("Syntax: 'reference _variable_'")
    nodelist = parser.parse(('endreference',))
    parser.delete_first_token()
    return ReferenceNode(bits[1], nodelist)


class ReferNode(template.Node):
    def __init__(self, path, namespace):
        self.path = path
        self.namespace = namespace

    def render(self, context):
        original_page = context['page']
        self.path = original_page.node.folder.child(self.path.strip('"'))
        context.push()
        context[current_referrer] = {'namespace': self.namespace}
        context['page'] = original_page.node.find_resource(File(self.path))
        render_to_string(str(self.path), context)
        var = context[current_referrer]
        context.pop()
        context[self.namespace] = var
        return ''


class ReferenceNode(template.Node):
    def __init__(self, variable, nodelist):
        self.variable = variable
        self.nodelist = nodelist

    def render(self, context):
        rendered_string = self.nodelist.render(context)
        if current_referrer in context and context[current_referrer]:
            context[current_referrer][self.variable] = rendered_string
        return rendered_string


class BracketNode(template.Node):
    def __init__(self, marker, nodelist):
        self.nodelist = nodelist
        self.marker = marker

    def render(self, context):
        rendered_string = self.nodelist.render(context)
        return marker_start % self.marker +\
                rendered_string + \
                marker_end % self.marker


class LatestExcerptNode(template.Node):
    def __init__(self, path, words=50):
        self.path = path
        self.words = words

    def render(self, context):
        sitemap_node = None
        self.path = self.path.render(context).strip('"')
        sitemap_node = context["site"].find_node(Folder(self.path))
        if not sitemap_node:
            sitemap_node = context["site"]

        def later(page1, page2):
            return (page1, page2)[page2.created > page1.created]
        page = reduce(later, sitemap_node.walk_pages())
        rendered = None
        rendered = render_to_string(str(page), context)
        excerpt_start = marker_start % "Excerpt"
        excerpt_end = marker_end % "Excerpt"
        start = rendered.find(excerpt_start)
        if not start == -1:
            context["latest_excerpt_url"] = page.url
            context["latest_excerpt_title"] = page.title
            start = start + len(excerpt_start)
            end = rendered.find(excerpt_end, start)
            return truncatewords_html(rendered[start:end], self.words)
        else:
            return ""


class RecentPostsNode(template.Node):
    def __init__(self, var='recent_posts', count=5, node=None, categories=None):
        self.var = var
        self.count = count
        self.node = node
        self.categories = categories

    def render(self, context):
        if not self.node:
            self.node = context['site']
        else:
            self.node = self.node.resolve(context)
        if not self.count == 5:
            self.count = self.count.render(context)

        if not self.var == 'recent_posts':
            self.var = self.var.render(context)

        category_filter = None
        if not self.categories is None:
            category_filter = re.compile(self.categories)

        if (not hasattr(self.node, 'complete_page_list') or
            not self.node.complete_page_list):
                complete_page_list = sorted(
                    self.node.walk_pages(),
                    key=operator.attrgetter("created"), reverse=True)
                complete_page_list = filter(lambda page: page.display_in_list, complete_page_list)
                self.node.complete_page_list = complete_page_list

        if category_filter is None:
            context[self.var] = self.node.complete_page_list[:int(self.count)]
        else:
            posts = filter(lambda page: page.display_in_list and \
                                            reduce(lambda c1,c2: c1 or category_filter.match(c2) is not None, \
                                                    hasattr(page, 'categories') and page.categories or [], False), self.node.complete_page_list)
            context[self.var] = posts[:int(self.count)]
        return ''


@register.tag(name="recent_posts")
def recent_posts(parser, token):
    tokens = token.split_contents()
    count = 5
    node = None
    categories = None
    var = 'recent_posts'
    if len(tokens) > 1:
        var = Template(tokens[1])
    if len(tokens) > 2:
        count = Template(tokens[2])
    if len(tokens) > 3:
        node = parser.compile_filter(tokens[3])
    if len(tokens) > 4:
        categories = tokens[4]
    return RecentPostsNode(var, count, node, categories)


@register.tag(name="latest_excerpt")
def latest_excerpt(parser, token):
    tokens = token.split_contents()
    path = None
    words = 50
    if len(tokens) > 1:
        path = Template(tokens[1])
    if len(tokens) > 2:
        words = int(tokens[2])
    return LatestExcerptNode(path, words)


@register.tag(name="render_excerpt")
def render_excerpt(parser, token):
    tokens = token.split_contents()
    path = None
    words = 50
    if len(tokens) > 1:
        path = parser.compile_filter(tokens[1])
    if len(tokens) > 2:
        words = int(tokens[2])
    return RenderExcerptNode(path, words)


@register.tag(name="render_article")
def render_article(parser, token):
    tokens = token.split_contents()
    path = None
    if len(tokens) > 1:
        path = parser.compile_filter(tokens[1])
    return RenderArticleNode(path)


class RenderExcerptNode(template.Node):
    def __init__(self, page, words=50):
        self.page = page
        self.words = words

    def render(self, context):
        page = self.page.resolve(context)
        context["excerpt_url"] = page.url
        context["excerpt_title"] = page.title
        rendered = get_bracketed_content(context, page, "Excerpt")
        return truncatewords_html(rendered, self.words)


class RenderArticleNode(template.Node):
    def __init__(self, page):
        self.page = page

    def render(self, context):
        page = self.page.resolve(context)
        return get_bracketed_content(context, page, "Article")


def get_bracketed_content(context, page, marker):
    rendered = None
    original_page = context['page']
    context['page'] = page
    rendered = render_to_string(str(page), context)
    context['page'] = original_page
    bracket_start = marker_start % marker
    bracket_end = marker_end % marker
    start = rendered.find(bracket_start)
    if not start == -1:
        start = start + len(bracket_start)
        end = rendered.find(bracket_end, start)
        return rendered[start:end]
    return ""


def hyde_thumbnail(url):
    postfix = getattr(settings, 'THUMBNAIL_FILENAME_POSTFIX', '-thumb')
    path, ext = url.rsplit('.', 1)
    return ''.join([path, postfix, '.', ext])
register.filter(stringfilter(hyde_thumbnail))


@register.filter
def value_for_key(dictionary, key):
    if not dictionary:
        return ""
    if not dictionary.has_key(key):
        return ""
    value = dictionary[key]
    return value


@register.filter
def xmldatetime(dt):
    if not dt:
        dt = datetime.now()
    zprefix = "Z"
    tz = dt.strftime("%z")
    if tz:
        zprefix = tz[:3] + ":" + tz[3:]
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + zprefix


@register.filter
def remove_date_prefix(slug, sep="-"):
    expr = sep.join([r"\d{2,4}"] * 3 + ["(.*)"])
    match = re.match(expr, slug)
    if not match:
        return slug
    else:
        return match.group(0)


@register.filter
def unslugify(slug):
    words = slug.replace("_", " ").\
                    replace("-", " ").\
                        replace(".", "").split()

    return ' '.join(map(lambda str: str.capitalize(), words))


@register.tag(name="hyde_listing_page_rewrite_rules")
def hyde_listing_page_rewrite_rules(parser, token):
    """Prints the Apache Mod_Rewrite RewriteRules for clean urls for pages in
    LISTING_PAGE_NAMES.  These rules are designed to be placed in a .htaccess
    file; they have not been tested inside of httpd.conf

    This only generates RewriteRules; it does not enable url rewriting or set
    RewriteBase.
    """
    return RenderHydeListingPageRewriteRulesNode()


LPN_REWRITE_RULE = string.Template(\
r"""
RewriteCond %{REQUEST_FILENAME}/${name}.html -f
RewriteRule ^(.*) $1/${name}.html
"""
)


class RenderHydeListingPageRewriteRulesNode(template.Node):
    def render(self, context):
        if not settings.LISTING_PAGE_NAMES:
            return ''
        rules = []  # For LISTING_PAGE_NAMES listings
        for name in settings.LISTING_PAGE_NAMES:
            rules.append(LPN_REWRITE_RULE.safe_substitute( \
                {'name': name}))
        return \
            "###  BEGIN GENERATED REWRITE RULES  ####\n" \
          + ''.join(rules) \
          + "\n####  END GENERATED REWRITE RULES  ####"


class IncludeTextNode(template.Node):
    def __init__(self, include_node):
        self.include_node = include_node

    def render(self, context):
        try:
            import markdown
            import typogrify
        except ImportError:
            print u"`includetext` requires Markdown and Typogrify."
            raise
        output = self.include_node.render(context)
        output = markdown.markdown(output)
        output = typogrify.typogrify(output)
        return output


@register.tag(name="includetext")
def includetext(parser, token):
    return IncludeTextNode(do_include(parser, token))


class RecentResourcesNode(template.Node):
    def __init__(self, tag_name, count=0, page='page', var_name='resources'):
        self.tag_name = tag_name
        self.count = int(count)
        self.page = template.Variable(page)
        self.var_name = var_name

    def render(self, context):
        page = self.page.resolve(context)
        resources = page is not None and page.node.media or []

        if self.count:
            resources = resources[:self.count]

        context[self.var_name] = resources

        return ''


@register.tag(name='recent_resources')
def recent_resources(parser, token):
    args = list(token.split_contents())
    kwargs = {}

    if len(args) >= 3 and args[-2] == 'as':
        kwargs['var_name'] = args.pop(-1)
        args.pop(-1)

    return RecentResourcesNode(*args, **kwargs)


class RenderNode(template.Node):
    def __init__(self, template_path, node_list=None, data=None):
        self.template_path = template_path
        self.node_list = node_list
        self.data = data

    def render(self, context):
        if self.node_list:
            text = self.node_list.render(context)
            import yaml
            self.data = yaml.load(text)
        else:
            self.data = self.data.resolve(context)
        context.push()
        context['data'] = self.data
        out = render_to_string(self.template_path, context)
        context.pop()
        return out


@register.tag(name='render')
def render(parser, token):
    bits = token.contents.split()
    if len(bits) < 2:
        raise TemplateSyntaxError("Syntax: {% render _template_ %}YAML{% endrender %}'")
    if ((len(bits) > 2 and len(bits) < 4) or (len(bits) == 4 and bits[2] != "with")):
        raise TemplateSyntaxError("Syntax: {% render _template_ with var_data %}'")
    template_path = bits[1]
    nodelist = None
    data = None
    if (len(bits) == 2):
        nodelist = parser.parse(('endrender',))
        parser.delete_first_token()
    else:
        data = template.Variable(bits[3])
    return RenderNode(template_path, node_list=nodelist, data=data)
