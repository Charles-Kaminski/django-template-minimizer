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
from _SimpleHTMLParser import get_first_tag_info
from _ManageMinimizers import get_minimizers

FLAGS  = re.IGNORECASE + re.DOTALL

EXCLUDE = r'({#\s*NOMINIFY\s*#})(.*?)({#\s*ENDNOMINIFY\s*#})'
REMOVE  = r'({%\s*COMMENT\s*%})(.*?)({%\s*ENDCOMMENT\s*%})' # Tag Comments
REMOVE2 = r'({#[^\n\r]+#})' # Other Comments
DVAR    = r'({{[^\n\r]+}})' # Django variable
DTAG    = r'({%[^\n\r]+%})' # Django tag
SCRIPT  = r'(<SCRIPT\b[^>]*>)(.*?)(</SCRIPT>)'
STYLE   = r'(<STYLE\b[^>]*>)(.*?)(</STYLE>)'

RE_EXCLUDE = re.compile(EXCLUDE, flags=FLAGS)
RE_REMOVE  = re.compile(REMOVE,  flags=FLAGS)
RE_REMOVE2 = re.compile(REMOVE2, flags=FLAGS)
RE_DVAR    = re.compile(DVAR,    flags=FLAGS)
RE_DTAG    = re.compile(DTAG,    flags=FLAGS)
RE_SCRIPT  = re.compile(SCRIPT,  flags=FLAGS)
RE_STYLE   = re.compile(STYLE,   flags=FLAGS)

# Will encasing the key in quotes. Will work well with javascript minifiers?
KEY    = '_~%s~_'

JSMINIMIZERS, CSSMINIMIZERS, HTMLMINIMIZERS = get_minimizers()

def minimize_template_text(text):
    """Takes a Django template text and returns a minified version.

    Performance is not critical as this function should be run off-line
    to store minimized templates.

    This function does not properly handle script or style tags embeded inside
    themselves; an unusual occurence.

    EG:
    <script>bla
       <script>bla</script>
    </script>

    Use the {# NOMINIFY #} {# ENDNOMINIFY #} comment tags to wrap code you do
    not want minified.  Suggested uses include wrapping pre, code, and textarea
    html tags as well as the example above.
    """

    # Create a list to hold special values temporarily removed
    # from the text.
    # format -> [(key, value), ...]
    word_list = []

    # Remove Excluded text
    excludes = RE_EXCLUDE.findall(text)

    # Strip out the {# NOMINIFY #} and {# ENDNOMINIFY #} tags
    excludes_find    = [''.join(x) for x in excludes]
    excludes_replace = [x[1] for x in excludes]

    # replace excluded text with keys and populate word_list
    text = subsitute_text(text, word_list, KEY, excludes_find, excludes_replace)

    # Remove any remaining template comments
    text = RE_REMOVE.sub('', text)
    text = RE_REMOVE2.sub('', text)

    # We want to "protect" Django Vars and Tags
    # then treat scripts and styles after "protecting" Django Vars and tags

    # Extract Django Variables
    dvars = RE_DVAR.findall(text)

    # replace Django Variables text with keys and populate word_list
    text = subsitute_text(text, word_list, KEY, dvars)

    # Extract django tags
    dtags = RE_DTAG.findall(text)

    # replace Django Tags text with keys and populate word_list
    text = subsitute_text(text, word_list, KEY, dtags)

    # Extract Styles
    styles  = RE_STYLE.findall(text)

    # Minimize syles
    styles_replace = minimize_tag_data(styles) or None

    # Put style pieces together
    styles_find = [''.join(x) for x in styles]

    # replace styles with keys and populate word_list
    text = subsitute_text(text, word_list, KEY, styles_find, styles_replace)

    # Extract Scripts
    scripts = RE_SCRIPT.findall(text)

    # Put scripts pieces together
    scripts_find = [''.join(x) for x in scripts]

    # Minimize javascripts if requested
    scripts_replace = minimize_tag_data(scripts) or None

    # replace scripts with keys and populate word_list
    text = subsitute_text(text, word_list, KEY, scripts_find, scripts_replace)

    # Run HTML Minimizers
    for f in HTMLMINIMIZERS: text = f(text)

    # put values back into text
    text = revert_text_keys(text, word_list)

    return text.strip()

def revert_text_keys(text, word_list):
    """ revert the text keys.  We may have to do this multiple times
    as some keys may be embeded in other word_list entries"""
    
    if not text or not word_list: 
        return text

    # If we loop through the word_list 10 times without
    #   consuming it completely, then something's probably wrong.

    max_iterations = len(word_list) * 10

    for x in xrange(max_iterations):

        # When the wordlist empties, break the for loop
        if not word_list:
            break

        # Take the first entry off the list
        key, value = word_list.pop(0)

        if key in text:
            # Replace the key with the value
            text = text.replace(key, value)
        else:
            # Put the entry back at the end of the list
            word_list.append((key, value))
    else:
        # We looped through too many time and
        # never consumed the whole word_list
        raise Exception('Minimizer failed to find all embeded variables.\n'
                        '%s\n%s' % (word_list, text))

    return text

def subsitute_text(text, word_list, key_template,
                   find_list, substitute_list=None):
    """ Using the text provided, subsitutes the first occurance of each entry
        in find_list with a key.  Store the key and value in the substitute_list
        in the word_list.  If no substitute_list is provided, use the value in
        the find list"""
    if not substitute_list: substitute_list = find_list

    values_list = zip(find_list, substitute_list)

    for find, substitute in values_list:
        key = key_template % len(word_list)
        text = text.replace(find, key, 1)
        word_list.append((key, substitute))

    return text

def minimize_tag_data(tags):
    """ This minimizes data in certain tags.
    Currently <script>Javascript</script> and <style>css</style>.
    Function assumes script is javascript if no type is specified.
    Function also assumes style is css if no type is specified.
    """

    retval = []

    for tag, data, end_tag in tags:

        tag_name, attr = get_first_tag_info(tag)
        type_attr = attr.get('type', 'javascript')

        if tag_name == 'script':
            type_attr = attr.get('type', 'javascript')
            if 'javascript' in type_attr:
                for f in JSMINIMIZERS: data = f(data)

        if tag_name == 'style':
            type_attr = attr.get('type', 'css')
            if 'css' in type_attr:
                for f in CSSMINIMIZERS: data = f(data)

        retval.append(tag + data + end_tag)

    return retval

if __name__ == '__main__':
    text = """{% block one %}
{% comment %}
This should be stripped out
{% endcomment %}
{# This comment should be gone as well #}
<Style> bla bla bla </stylE>
<style type="text/css">
h1 {letter-spacing:2px;}
h2 {letter-spacing:-3px;}
p {text-indent:50px;}
</style>
<scrIPT type="Text/javascript">a</Script>
<script language=Javascript>
<!--
var _P="http://www.js-examples.com/data/ex_1004/";

function preloadImage(fnImg)
{
    // create array for preloadedImages if not already created:
    if (!document.preloadedImages)
        document.preloadedImages = new Array();
    // create new image:
    document.preloadedImages[fnImg] = new Image();
    document.preloadedImages[fnImg].src = _P+fnImg;
}

function imgSwitch(imgId, fnImgNew)
{
    // switch to new image:
    if (document.preloadedImages && document.preloadedImages[fnImgNew])
        document.images[imgId].src = document.preloadedImages[fnImgNew].src;
    else
        document.images[imgId].src = _P+fnImgNew;
}

function imgMouseOver(imgId, fnImgOver)
{
    // remember original image:
    document.images[imgId].originalSrc = document.images[imgId].src;
    // switch to mouseover image:
    imgSwitch(imgId, fnImgOver);
}

function imgMouseOut(imgId)
{
    // switch back to original image:
    if (document.images[imgId] && document.images[imgId].originalSrc)
        document.images[imgId].src = document[imgId].originalSrc;
}


var timerID, now;

// These values are to store currently-displayed date digits.
// They're initialized to -1 to ensure that all digits are updated in
//   the first call to showTime:
var year10 = -1;
var year1 = -1;
var month10 = -1;
var month1 = -1;
var date10 = -1;
var date1 = -1;
var day = -1;
var hours10 = -1;
var hours1 = -1;
var minutes10 = -1;
var minutes1 = -1;
var seconds10 = -1;
var seconds1 = -1;

// updates clock display:
function showTime()
{
    // get digits in date:
    var now = new Date();
    var newYear = now.getYear();
    newYear = newYear % 100;
    var newYear10 = Math.floor(newYear / 10);
    var newYear1 = newYear - (newYear10 * 10);
    var newMonth = now.getMonth();
    newMonth++;
    var newMonth10 = Math.floor(newMonth / 10);
    var newMonth1 = newMonth - (newMonth10 * 10);
    var newDate = now.getDate();
    var newDate10 = Math.floor(newDate / 10);
    var newDate1 = newDate - (newDate10 * 10);
    var newDay = now.getDay();
    var newHours = now.getHours();
    var newHours10 = Math.floor(newHours / 10);
    var newHours1 = newHours - (newHours10 * 10);
    var newMinutes = now.getMinutes();
    var newMinutes10 = Math.floor(newMinutes / 10);
    var newMinutes1 = newMinutes - (newMinutes10 * 10);
    var newSeconds = now.getSeconds();
    var newSeconds10 = Math.floor(newSeconds / 10);
    var newSeconds1 = newSeconds - (newSeconds10 * 10);

    // only switch image if date digit has changed:
    if (newYear10 != year10)
    {
        imgSwitch("year10", "images/tinydigit" + newYear10 + ".gif");
        year10 = newYear10;
    }
    if (newYear1 != year1)
    {
        imgSwitch("year1", "images/tinydigit" + newYear1 + ".gif");
        year1 = newYear1;
    }
    if (newMonth10 != month10)
    {
        if (newMonth10 == 0)
            imgSwitch("month10", "images/tinyblank.gif");
        else
            imgSwitch("month10", "images/tinydigit" + newMonth10 + ".gif");
        month10 = newMonth10;
    }
    if (newMonth1 != month1)
    {
        imgSwitch("month1", "images/tinydigit" + newMonth1 + ".gif");
        month1 = newMonth1;
    }
    if (newDate10 != date10)
    {
        imgSwitch("date10", "images/tinydigit" + newDate10 + ".gif");
        date10 = newDate10;
    }
    if (newDate1 != date1)
    {
        imgSwitch("date1", "images/tinydigit" + newDate1 + ".gif");
        date1 = newDate1;
    }
    if (newDay != day)
    {
        imgSwitch("day", "images/day" + newDay + ".gif");
        day = newDay;
    }
    if (newHours10 != hours10)
    {
        imgSwitch("hours10", "images/digit" + newHours10 + ".gif");
        hours10 = newHours10;
    }
    if (newHours1 != hours1)
    {
        imgSwitch("hours1", "images/digit" + newHours1 + ".gif");
        hours1 = newHours1;
    }
    if (newMinutes10 != minutes10)
    {
        imgSwitch("minutes10", "images/digit" + newMinutes10 + ".gif");
        minutes10 = newMinutes10;
    }
    if (newMinutes1 != minutes1)
    {
        imgSwitch("minutes1", "images/digit" + newMinutes1 + ".gif");
        minutes1 = newMinutes1;
    }
    if (newSeconds10 != seconds10)
    {
        imgSwitch("seconds10", "images/smalldigit" + newSeconds10 + ".gif");
        seconds10 = newSeconds10;
    }
    imgSwitch("seconds1", "images/smalldigit" + newSeconds1 + ".gif");

    // update clock again in 1 second:
    timerID = setTimeout("showTime()", 1000);
}


function preloadImages()
{
    for (var i = 0; i <= 9; i++)
    {
        preloadImage("images/digit" + i + ".gif");
        preloadImage("images/smalldigit" + i + ".gif");
        preloadImage("images/tinydigit" + i + ".gif");
    }
    for (i = 0; i <= 6; i++)
        preloadImage("images/day" + i + ".gif");
}

// -->
</script>
here \t\t\tcomes        the rain \n\n\nagain <a href='bla'>test</a>
{% block two %}
{{ fun.times|here:"bla" }}
<div>over the rainbow</div>
{#NOMINiFY #} do     not minify     this   . {# ENDNOminify

#}
"""

    a = minimize_template_text(text)
    print text
    print '#' * 10
    print a
    print '#' * 10
    print 'Character length before: %s' % len(text)
    print 'Character length after:  %s' % len(a)
