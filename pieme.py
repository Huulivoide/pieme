#!/usr/local/bin/python2.5
# -*- coding: UTF-8 -*-

################################################################################
#Copyright (c) 2013, Jesse Jaara.                                              #
#All rights reserved.                                                          #
#                                                                              #
#Redistribution and use in source and binary forms, with or without,           #
#modification, are permitted provided that the following conditions are met:   #
#                                                                              #
# 1. Redistributions of source code must retain the above copyright notice,    #
#       this list of conditions and the following disclaimer.                  #
#                                                                              #
#    2. Redistributions in binary form must reproduce the above copyright      #
#       notice, this list of conditions and the following disclaimer in the    #
#       documentation and/or other materials provided with the distribution.   #
#                                                                              #
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"   #
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE     #
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE#
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE   #
#FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    #
#DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR    #
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER    #
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, #
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE #
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.          #
################################################################################

import sqlite3
from datetime import datetime
import time
from urllib import unquote as _un
import bbcode  # External module to enable use of BBcode in the messages
import re
import cgi
import cgitb  # So we can see the possible error messages

##   SETTINGS   ##
baseurl = "http://your/website/basepath/here"
log2file = False
logFileDir = "./logs"
DBfile = "comments.db"
## END SETTINGS ##


# We need to "open" the FildStorage before we enable cgitb, otherwice POST
# method will not work and using GET sets some limitations.
form = cgi.FieldStorage()
cgitb.enable(display=log2file, logdir=logFileDir)

# For those who do not know SQL: This basicly selects all of the messages
# in the database and puts them in a descending order, according to their
# 'id' values. All of the messages have a unique ID value used to identify them
select = "SELECT id, nick, date, message FROM comments ORDER BY id DESC;"
insert = "INSERT INTO comments (id, nick, date, message) VALUES (?, ?, ?, ?);"
# SQL query to insert our new comment into the database. ? is a space holder
# like ("%s %s" % (mystring, a)), using it instead of the Pythons own % or
# format function should minimize the risk of a SQL injection. Not that those
# really matter in our case, as we do not have personal info in the database.

# Open the database file for reading and writing
connection = sqlite3.connect(DBfile)
c = connection.cursor()


# Print out a HTML page that containts a haeder with CSS and possible
# javascript links/codes. Add an unsorted list and make a <li> element for
# each of our messages stored in the database.
def list_comments():
    # Run the SQL query used to fetch the messages
    comments = c.execute(select)
    # We need a HTML haeder and one empty line after it.
    print "Content-type: text/html; charset=utf-8"
    print
    print """
    <!DOCTYPE html>
    <html lang="fi">
    <head>
        <meta charset="UTF-8" />
        <link rel="stylesheet" type="text/css"
          href="%(url)s/css/main.css" />
        <link rel="stylesheet" type="text/css"
          href="%(url)s/css/comments-frame.css" />
    </head>
    <body>
        <ul>
    """ % {'url': baseurl}

    # Loop over the list messages in our databse. Parse the that is stored as
    # a unix timestamp into a date represanrtation used in Finland
    # DAY.MONTH.YEAR HOURS:MINUTES
    for comment in comments:
        date = datetime.fromtimestamp(comment[2]).strftime('%d.%m.%Y %H:%M')
        message = comment[3]
        nick = comment[1]
        print """
        <li>
            <div class="header">
                <span class="id">%i</span>: 
                    <span class="date">%s</span>
                    <span class="nick">%s</span> kirjoitti:
            </div>
            <div class="message">%s</div>
        </li>
        """ % (comment[0], date, nick.encode('utf-8'), message.encode('utf-8'))

    print """
        </ul>
    </body>
    </html>
    """


# Insert a new comment into out database and printout a HTML page that does a
# redirection back to the comments page.
def post():
    date = int(time.time())
    nick = _un(form.getvalue("nick"))

    # Stip away all HTML one might have inserted into the message. Should
    # prevent one from doing nasty things.
    message = re.sub('<[^<]+?>', '', _un(form.getvalue("message")))
    message = bbcode.render_html(message)  # Render the BBcode to html

    # Get the highest ID currently owned by one of the messages in our database
    # and increase it by one, this will be the ID of our new message.
    _id = c.execute("SELECT MAX(id) FROM comments;").fetchone()[0] + 1
    c.execute(insert, (_id, nick, date, message))
    # Flush the changes to disk
    connection.commit()

    print "Content-type: text/html; charset=utf-8"
    print
    print """
    <!DOCTYPE html>
    <html lang="fi">
    <head>
        <META HTTP-EQUIV="refresh"
            content="0; URL=%(url)s/comments.html">
    </head>
    """ % {'url': baseurl}


function = _un(form.getvalue("function"))

if (function == "list"):
    list_comments()
if (function == "post"):
    post()

connection.close()
