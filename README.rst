django-template-minimizer
=========================

For Django developers obsessed with performance. 
Minimize your templates once and not your HTML each time you serve it up.

:Download: http://pypi.python.org/pypi/django-template-minimizer/
:Source: http://github.com/Charles-Kaminski/django-template-minimizer
:License: MIT

Run this Django command to minimize your Django templates.  Eliminate the need to reprocess your HTML to minimize it; as the HTML is now being put together in minimized form.

The command minimizes django templates along with the html, in-line ``<script>`` javascript, and in-line ``<style>`` css inside the templates.  The command includes a minimize and an undo option.  The minimizers for html, css, and javascript are plugable so you can override or add your own.

Installing django-template-minimizer
====================================

You can install ``django-template-minimizer`` either via the Python Package Index (PyPI) or from source.

To install using ``pip`` (recommended)::

    $ pip install django-template-minimizer

To install using ``easy_install``::

    $ easy_install django-template-minimizer

Register the app in your Django project's settings file::

    import tmin
    ...
    INSTALLED_APPS += ('tmin',)

To install from source, download the source from github (http://github.com/Charles-Kaminski/django-template-minimizer/downloads).  Decompress it and put it in the folder with your django project as another django app.  Register the app in your Django project's settings file.  

Usage
=====

**Commands**::

    $ python manage.py minimizetemplates    -> help text
    $ python manage.py minimizetemplates -m -> minimize
    $ python manage.py minimizetemplates -u -> undo
    
Use these commands to minimize (or unminimize) Django templates after development.  This way, your templates are small when they are evaluated and the HTML served is already minimized; eliminiating any post-processing minimization step.  

Use the comment tags ``{# NOMINIFY #} {# ENDNOMINIFY #}`` inside your templates to wrap content you do not want minified.  

Uses the setting ``TEMPLATE_DIRS`` in your Django settings file to tell the command where to find templates to minimize.::

    TEMPLATE_DIRS = [...]

Customization
=============

The minimizer command uses default minimizers for html, style tag embeded css, and script tag embeded javascript. You can override these and chain any number of your own minimizers using the settings below.  These settings go in the Django settings file. Custom minimizers must be functions that accept text as a string parameter and return text as a string.:: 

    JAVASCRIPT_MINIMIZERS = [my_function_1, my_function_2, ...]
    CSS_MINIMIZERS        = [my_function_3, my_function_4, ...]
    HTML_MINIMIZERS       = [my_function_5, my_function_6, ...]

To turn off a minimizer, use the following pattern::

    f = lambda x: x
    JAVASCRIPT_MINIMIZERS = [f,]

You can tell the minimizer command to disable an aggressive HTML minimizer in the default HTML minimizer chain.  This minimizer normally removes (instead of just collapsing) the remaining space between '``>``' & '``<``' character.  To disable this minimizer in the default chain, set the following setting to False in your Django settings file::

    AGGRESSIVE_HTML_MINIMIZER = False

Method
======

For each template, the minimizer command:  

1. Replaces any ``{# NOMINIFY #} {# ENDNOMINIFY #}`` tags and content with a unique identifier and saves the content in memory so that it is excluded from the rest of the process.

2. Remaining Django comments are removed.

3. Django tags and django variables are replaced with unique identifiers.  The tags and variables are saved in memory.  This approach "protects" the tags and variables from the minimizers.  It also allows you to use Django tags and variables inside your javascript and CSS without ill effect by the CSS or javascript minimizer.

4. HTML script tags and content are replaced with unique identifiers. The tags and content are saved in memory for additional processing.  The type attribute for the script tag is checked to see if the script content is javascript.  If no type is provided, then javascript is assumed.  Any javascript is then run through the javascript minimizers.

5. An almost identical process to step 4 is implemented on the HTML style tags for css.

6. The remaining text (with the identifiers) is run through the html minimizers.

7. All of the content saved in memory and associated with unique identifiers are put back.

8. The original template is moved to an archive folder.  The minimized template is put in the original location.

Limitations
===========

Use the ``{# NOMINIFY #} {# ENDNOMINIFY #}`` comment tags to overcome these limitations.

1. The default javascript and css minimizers do not handle script tags inside script tags or style tags inside style tags; an unusual occurance.

    ``eg: <script>bla bla<script>bla</script>bla</script>``

2. The minimizer collapses all white space not in a django tag, django variable, javascript, or inline css.  This includes whitespace inside ``<pre>``, ``<textarea>``, and similar tags; and whitespace inside html attributes.
