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

import re
from _JavascriptMinify import jsmin
from _cssmin import cssmin
from django.conf import settings

FLAGS  = re.IGNORECASE + re.DOTALL

SPACE   = r'(\s+)'
TAGS    = r'(>\s+<)'

RE_SPACE   = re.compile(SPACE,   flags=FLAGS)
RE_TAGS    = re.compile(TAGS,    flags=FLAGS)

HTMLMIN1 = lambda x: RE_SPACE.sub(' ', x)
HTMLMIN2 = lambda x: RE_TAGS.sub('><', x)


def get_minimizers():
    """Returns ->
    [jsminimizers_list, cssminimizers_list, htmlminimizers_list]"""

    # Initialize
    jsminimizers = [jsmin]
    cssminimizers = [cssmin]
    htmlminimizers = [HTMLMIN1, HTMLMIN2]
    
    if hasattr(settings, 'AGGRESSIVE_HTML_MINIMIZER'):
        aggressive = settings.AGGRESSIVE_HTML_MINIMIZER   
        if not aggressive: htmlminimizers.pop()  

    # Get any override settings
    if hasattr(settings, 'JAVASCRIPT_MINIMIZERS'):
        jsminimizers = settings.JAVASCRIPT_MINIMIZERS
    if hasattr(settings, 'CSS_MINIMIZERS'):
        cssminimizers = settings.CSS_MINIMIZERS
    if hasattr(settings, 'HTML_MINIMIZERS'):
        htmlminimizers = settings.HTML_MINIMIZERS

    retval = [jsminimizers, cssminimizers, htmlminimizers]

    # Check that they are lists or tuples
    for cat in retval:
        if not isinstance(cat, (list, tuple)):
            raise Exception('Minimizers must be enclosed in a list or tuple.\n'
                            'Check your django settings file')
        for f in cat:
            if not callable(f):
                raise Exception('Minimizers must be callable functions.\n'
                                'Check your django settings file')

    # Convert any tuples into lists
    for cat in retval:
        cat = isinstance(cat, tuple) and list(cat) or cat

    return retval