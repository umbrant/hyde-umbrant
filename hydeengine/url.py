"""
Utility functions for dealing with urls. 

"""
import sys

def join(parent, child):
    """

    Appends the child to the parent, taking care of the slashes. The resulting
    url does not have a trailing slash.

    """
    return (parent.rstrip("/") + "/" + child.lstrip("/")).rstrip("/")
    
def fixslash(url, relative=True):
    """

    Removes trailing slash. If relative is True ensures a leading slash is present
    otherwise ensures it is not.

    """
    if sys.platform == 'win32':
        url = url.replace('\\', '/')
    url = url.strip("/")
    if relative:
        url = "/" + url
    return url
    
def clean_url(url):
        
    """

    Removes .html from the url if it exists.

    """
    parts = url.rsplit(".", 1)
    if parts[1] == "html":
        return parts[0]
    return url