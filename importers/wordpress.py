#!/usr/bin/python
import sys
import os
import re
import MySQLdb

# I had a huge mixture of wordpress code tags, ie [sourcecode] [code] <pre><code>
# setting this to true will change them all to {% syntax %}
translate_code_tags = True
database_host       = "localhost"
database_user       = "wordpress"
database_password   = "your_db_password"
database_name       = "wordpress"

# You can safely ignore below this
if translate_code_tags:
    open_code_regex         = re.compile(r'\[(source)*code lang(uage)*=[\'"](?P<language>.*)[\'"]\]')
    close_code_regex        = re.compile(r'\[\/(source)*code\]')
    lower_case_lexer_regex  = re.compile(r'{% syntax C %}')
    pre_open_remove_regex   = re.compile(r'<pre>')
    pre_close_remove_regex  = re.compile(r'</pre>')
    code_open_remove_regex  = re.compile(r'<code>')
    code_close_remove_regex = re.compile(r'</code>')

# Content directory is just whatever directory you have the years in, ie /my_hyde_blog/content/blog
if len(sys.argv) != 2:
    print "Usage: %s [path_to_content_directory]" % sys.argv[0] 
    sys.exit(1)

output_directory = str(sys.argv[1])
if output_directory[-1] != '/':
    output_directory = output_directory + '/'

print "Outputting files to " + output_directory

conn = MySQLdb.connect ( host   = "localhost",
                         user   = "wpuser",
                         passwd = "phpaccess",
                         db     = "wp")

cursor = conn.cursor()
query = """select post_title, post_name, post_date, post_content, post_excerpt, ID, guid from wp_posts where post_status = 'publish' and post_type = 'post'"""

cursor.execute(query)

while True:
    row = cursor.fetchone()
  
    if row == None:
        break

    title = row[0]
    slug = row[1]
    date = row[2]
    content = row[3]
    name = "%02d-%02d-%02d-%s.html" % (date.year, date.month, date.day, slug)

    if translate_code_tags:
        content = open_code_regex.sub(r'{% syntax \g<language> %}', content)
        content = lower_case_lexer_regex.sub('{% syntax c %}', content)
        content = close_code_regex.sub(r'{% endsyntax %}', content)
        content = pre_open_remove_regex.sub('', content)
        content = pre_close_remove_regex.sub('', content)
        content = code_open_remove_regex.sub(r'{% syntax %}', content)
        content = code_close_remove_regex.sub(r'{% endsyntax %}', content)

    try:
        os.makedirs(output_directory + str(date.year) + "/")
    except OSError:
        pass
    file_handle = open(output_directory + str(date.year) + "/" + name, 'w')
    file_handle.write("{% extends \"_post.html\" %}\n")
    file_handle.write("{%load webdesign %}")
    file_handle.write("{%hyde\n    title: \"" + title + "\"\n    created: " + str(date) + "\n%}\n")
    file_handle.write("{% block article %}\n")
    file_handle.write(content)
    file_handle.write("{% endblock %}\n")
    file_handle.close()
    print "Wrote file " + name

cursor.close()
conn.close()
