#!/usr/bin/python
# -*- encoding: utf-8 -*-
# usage: md2latex.py PATH < markdown.md
# splits markdown.md into individual talks and converts them to latex
# snippets
import sys
from cStringIO import StringIO
import os
import re
import mangle
import subprocess
from lxml import etree
from lxml import sax
import xml.sax.handler

authors = {
    u"Luang Por Pasanno": "lpp",
    u"Ajahn Amaro": "aa",
    u"Ajahn Yatiko": "ay",
    u"Ajahn Karuṇadhammo": "akd",
    u"Ajahn Jotipālo": "ajo",
    u"Ajahn Ñāṇiko": "an",
    u"Ajahn Vīradhammo": "av",
    u"Ajahn Sucitto": "asuc",
}

months = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}

xhtml_head = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<link rel="stylesheet" type="text/css" href="body.css" />
</head>
<body>"""

xhtml_tail = """</body>
</html>"""

class Html2Xhtml(xml.sax.handler.ContentHandler):
    def __init__(self, outfile=sys.stdout):
        xml.sax.handler.ContentHandler.__init__(self)
        self.outfile = outfile
        self.path = []
        self.curtitle = None
        self.curauthor = None
        self.curdate = None
    def characters(self, content):
        content = content.strip('\n')
        if content:
            #content = re.sub(r'\.\.\.', r'\ldots{}', content)
            #content = re.sub(ur'\u201c', '``', content)
            #content = re.sub(ur'\u201d', '\'\'', content)
            #content = re.sub(ur'\u2018', '`', content)
            #content = re.sub(ur'\u2019', '\'', content)
            #content = re.sub(ur'\u2014', '---', content)
            #content = content.encode('ascii', 'xmlcharrefreplace')
            content = content.encode('utf-8')
            cur = self.path[-1]
            if cur == 'h1':
                self.curtitle = content
            elif cur == 'h2':
                self.curauthor = content
            elif cur == 'h3':
                m = re.match(r'(..)-(..)-(..)', content)
                self.curdate = '%s 20%s' % (months[m.group(1)], m.group(3))
            else:
                self.outfile.write(content)
    def startElementNS(self, name, qname, attrs):
        self.path.append(qname)
        if qname == 'p':
            self.outfile.write('<p>')
        elif qname == 'em':
            self.outfile.write(r'<em>')
        #elif qname == 'h1':
        #    pass
    def endElementNS(self, name, qname):
        self.path.pop()
        if qname == 'p':
            self.outfile.write('</p>\n')
        elif qname == 'em':
            self.outfile.write('</em>')
        elif qname == 'h3':
            self.outfile.write('<h1>%s</h1>\n<h2>%s \xe2\x80\xa2 %s</h2>\n'
                % (self.curtitle, self.curauthor, self.curdate))


infile = sys.stdin
buf = StringIO()

if len(sys.argv) > 1:
    outdir = sys.argv[1]
else:
    outdir = '.'



def fixdate(d):
    m = re.match('(..)-(..)-(..)', d)
    return '20%s-%s-%s' % (m.group(3), m.group(1), m.group(2))


def md2xhtml(infile, outfile):
    pandoc = subprocess.Popen(['pandoc', '-f', 'markdown', '-t', 'html', '-S'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    fold = subprocess.Popen(['fold', '-s', '-w', '72'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    pandoc.stdin.write(infile.read())
    pandoc.stdin.close()
    tree = etree.parse(pandoc.stdout, etree.HTMLParser(encoding='utf-8'))
    sax.saxify(tree, Html2Xhtml(fold.stdin))
    fold.stdin.close()
    outfile.write(xhtml_head)
    outfile.write(fold.stdout.read())
    outfile.write(xhtml_tail)

line = infile.readline()




title = None
author = None
date = None


while line:
    m = re.match(r'(#+) (.*)\n', line)
    if m:
        nhash = len(m.group(1))
        if nhash == 1:
            if buf.tell():
                outname = '%s_%s_%s.xhtml' % (author, date, title)
                outfile = open(outdir + os.sep + outname, 'w')
                buf.seek(0)
                md2xhtml(buf, outfile)
                outfile.close()
                buf.truncate(0)
            title = mangle.mangle(m.group(2).decode('utf-8'))
        elif nhash == 2:
            author = authors[m.group(2).decode('utf-8')]
        elif nhash == 3:
            date = fixdate(m.group(2))
            
    buf.write(line)

    line = infile.readline()

if buf.tell():
    outname = '%s_%s_%s.xhtml' % (author, date, title)
    outfile = open(outdir + os.sep + outname, 'w')
    buf.seek(0)
    md2xhtml(buf, outfile)
    outfile.close()
