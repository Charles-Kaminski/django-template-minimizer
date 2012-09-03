"""Copyright (c) 2012 Charles Kaminski (CharlesKaminski@gmail.com)

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE."""

from HTMLParser import HTMLParser

def get_first_tag_info(html):
    """ Takes an html snippet and returns:
        (tag, attribute dictionary)
    """
    parser = FirstTagInfo()
    parser.feed(html)
    return (parser.tag, parser.attrs)

class FirstTagInfo(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        # For new style classes
        # super(FirstTagInfo, self).__init__()
        self.tag = ''
        self.attrs = {}

    def handle_starttag(self, tag, attrs):
        if not self.tag:
            self.tag = tag.lower()
            attrs = [(x.lower(), y and y.lower() or '') for x,y in attrs]
            self.attrs = dict(attrs)

if __name__ == '__main__':
    text = ('<scRipt t="bla" t2 = bla t3= \'bla\' t4>cat dog'
                             '<Script>mouse</scriPt>bla</scripT>')
    print text
    print get_first_tag_info(text)
