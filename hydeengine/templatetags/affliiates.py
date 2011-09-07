# affiliates.py

from django import template
from django.utils import html
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
import urllib;

if (not vars().has_key('ITUNES_AFFILIATE_ID')):
    ITUNES_AFFILIATE_ID = 'FU9TTuAveps'
if (not vars().has_key('AMAZON_AFFILIATE_ID')):
    AMAZON_AFFILIATE_ID = '6tringle-20'

register = template.Library()

def doubleurlescape(some_string):
    return urllib.quote(urllib.quote(some_string, ''), '')

@register.filter()
@stringfilter
def itunes(value, arg=None, autoescape=None):
    """Takes an iTunes link (http://phobos.apple.com/Web... or http://itunes.apple.com/Web...) and turns it into an affilate link
    If there is an argument, the arg becomes a text link.  If not, the standard iTunes Badge is used
    
    Usage Example:
    {{"http://itunes.apple.com/WebObjects/MZStore.woa/wa/viewSoftware?id=288545208&mt=8"|itunes:"Instapaper Pro" }}
    {{"http://itunes.apple.com/WebObjects/MZStore.woa/wa/viewSoftware?id=288545208&mt=8"|itunes }}
    """
    
    if (value[0:34] != 'http://phobos.apple.com/WebObjects' and value[0:34] != 'http://itunes.apple.com/WebObjects'):
        return value
    str_list = []
    str_list.append('<a href="http://click.linksynergy.com/fs-bin/stat?id=')
    str_list.append(ITUNES_AFFILIATE_ID)
    str_list.append('&offerid=146261&type=3&subid=0&tmpid=1826&RD_PARM1=')
    withpartner = value + '&partnerId=30'
    str_list.append(doubleurlescape(withpartner))
    str_list.append('">')
    if (arg):
        str_list.append(arg)
    else:
        str_list.append('<img height="15" width="61" alt="Buy app through iTunes" src="http://ax.phobos.apple.com.edgesuite.net/images/badgeitunes61x15dark.gif" />')
    str_list.append('</a>')
    return_string = ''.join(str_list)
    return mark_safe(return_string)
itunes.needs_autoescape = True


@register.filter()
@stringfilter
def amazon_link(value, arg=None, autoescape=None):
    """take any amazon link and affiliates it.  The argument is set inside the anchor tags.  No argument will just place the link itself in the anchor tags
    
    Usage Example:
    {{"http://www.amazon.com/Kindle-Amazons-Wireless-Reading-Generation/dp/B00154JDAI/"|amazon_link:"Kindle2"}}
    {{"http://www.amazon.com/dp/B00154JDAI/"|amazon_link}}
    """
    str_list = []
    str_list.append('<a href="http://www.amazon.com/gp/redirect.html?ie=UTF8&location=')
    str_list.append(urllib.quote(value, ''))
    str_list.append('&tag=')
    str_list.append(AMAZON_AFFILIATE_ID)
    str_list.append('&linkCode=ur2')
    str_list.append('">')
    if (arg):
        str_list.append(arg)
    else:
        str_list.append(value)
    str_list.append('</a>')
    str_list.append('<img src="http://www.assoc-amazon.com/e/ir?t=')
    str_list.append(AMAZON_AFFILIATE_ID)
    str_list.append('&l=ur2&o=1" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />')    
    
    return_string = ''.join(str_list)
    return mark_safe(return_string)
amazon_link.needs_autoescape = True

@register.filter()
@stringfilter
def amazon_asin(value, arg=None, autoescape=None):
    """take any amazon ASIN and affiliates it.  The argument is set inside the anchor tags.  No argument will just place the link itself in the anchor tags
    
    Usage Example:
    {{"B00154JDAI"|amazon_asin:"Kindle2"}}
    {{"B00154JDAI"|amazon_asin}}
    
    """
    str_list = []
    str_list.append('<a href="http://www.amazon.com/gp/product/')
    str_list.append(value) #ASIN
    str_list.append('?ie=UTF8&tag=')
    str_list.append(AMAZON_AFFILIATE_ID)
    str_list.append('&linkCode=as2&creativeASIN=')
    str_list.append(value) #ASIN
    str_list.append('">')
    if (arg):
        str_list.append(arg)
    else:
        str_list.append("Amazon Product Link: %s" % value)
    str_list.append('</a>')
    str_list.append('<img src="http://www.assoc-amazon.com/e/ir?t=')
    str_list.append(AMAZON_AFFILIATE_ID)
    str_list.append('&l=as2&o=1&a=')
    str_list.append(value) #ASIN
    str_list.append('" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />')
    
    return_string = ''.join(str_list)
    return mark_safe(return_string)
amazon_asin.needs_autoescape = True

    



