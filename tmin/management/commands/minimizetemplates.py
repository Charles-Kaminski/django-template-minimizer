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

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os import getcwd, sep, walk, makedirs
from os.path import join, exists, basename, dirname
from shutil import move, rmtree
from optparse import make_option
from _TemplateTextMinimizer import minimize_template_text

ARCHIVE = '_minimizer_archive'
REVERTED = '_reverted_'
ARCHIVE_EXISTS = ('A minimizer archive folder already exists.\n'
                  'Check that the following templates are not already '
                  'minimized: \n%s')
ARCHIVE_DOESNT_EXIST = ("The below archive folder doesn't exist.\n"
                        "Check that you shouldn't be reverting the "
                        "coresponding folder: \n%s")

class Command(BaseCommand):
    help = '''Use this tool to minimize Django templates after
development.  This way, your templates are small when they are
evaluated and the HTML served is already minimized; eliminiating
any post-processing minimization step.  The command can be undone
using the -u option.

Use the comment tags {# NOMINIFY #} {# ENDNOMINIFY #} to wrap
content you do not want minified.

Uses the setting TEMPLATE_DIRS in your Django settings file to
    tell the command where to find templates to minimize.

Customization:
The minimizer command uses its own minimizers for html, style tag embeded
    css, and script tag embeded javascript. You can override these and chain
    any number of your own minimizers using settings below.  These
    settings go in the Django settings file. Custom minimizers must
    be functions that accept text as a string parameter and return
    text as a string.
    JAVASCRIPT_MINIMIZERS = [custom_function1, custom_function2,]
    CSS_MINIMIZERS        = [custom_function3, custom_function4,]
    HTML_MINIMIZERS       = [custom_function5, custom_function6,]

    To turn off a minimizer, use the following pattern:
    f = lambda x: x
    JAVASCRIPT_MINIMIZER = [f,]

You can tell the minimizer command to disable an aggressive minimizer 
    in the default HTML minimizer chain.  This minimizer normally removes 
    (instead of just collapsing) the remaining space between '>' & '<' 
    character.  Set the following setting to False in your Django
    settings file to disable this final step:
    AGGRESSIVE_HTML_MINIMIZER = False

Method - For each template, the minimizer command:
1. Replaces any {# NOMINIFY #} {# ENDNOMINIFY #} content with
    a unique identifier and saves the content in memory so that
    it is excluded from the rest of the process.
2. Remaining Django comments are removed.
3. Django tags and django variables are replaced with with unique
    identifiers.  The tags and variables are saved in memory.
    This approach "protects" the tags and variables from the
    minimizers.  It also allows you to use Django tags and variables
    inside your javascript and CSS without ill effect by the
    CSS or javascript minimizer.
4. HTML script tags and content are replaced with unique
    identifiers. The tags and content are saved in memory for
    additional processing.  The type attribute for the script tag
    is checked to see if the script content is javascript.  If no
    type is provided, then javascript is assumed.  Any javascript
    is then run through the javascript minimizers.
5. An almost identical process to step 4 is implemented on the HTML
    style tags for css.
6. The remaining text (with the identifiers) is run through the
    html minimizers.
7. All of the content saved in memory and associated with unique
    identifiers are put back.
8. The original template is moved to an archive folder and replaced
    with the minimized template.

Limitations:
The minimizer does not handle script tags inside script tags or
    style tags inside style tags; an unusual occurance.
    eg: <script>bla bla <script> bla</script></script>
The minimizer collapses all white space not in a django tag,
    django variable, javascript, or inline css.  This includes
    whitespace inside <pre>, <textarea>, & similar tags, and
    whitespace inside html attributes.
Use the {# NOMINIFY #} {# ENDNOMINIFY #} comment tags to overcome
    these limiations.
    
'''

    option_list = BaseCommand.option_list + (
        make_option('-m', '--minimize',
                    action='store_true', dest='minimize', default=False,
                    help='Minimize templates.'),
        make_option('-u', '--undo',
                    action='store_true', dest='undo', default=False,
                    help='Reverts minimized templates from the archive.'),)

    def handle(self, *args, **options):

        # Reading template location from settings
        try:
            dirs = settings.TEMPLATE_DIRS
        except AttributeError:
            raise CommandError('You must specify TEMPLATE_DIRS in your '
                               'settings file.')

        # Get the full and proper paths
        cwd = getcwd()
        dirs = [x.replace('/', sep).rstrip(sep) for x in dirs]
        dirs = [join(cwd,x) for x in dirs]

        if options['undo']:
            self.revert(dirs)
            self.stdout.write('Successfully reverted minimized Templates:\n')
            for d in dirs:
                self.stdout.write('%s\n' % d)
            return 0
        elif options['minimize']:
            self.minimize_templates(dirs)
            self.stdout.write('Successfully minimized Templates:\n')
            for d in dirs:
                self.stdout.write('%s\n' % d)
            return 0
        else:
            command_name = basename(__file__).rstrip('.py')
            self.print_help(command_name, '')

    def minimize_templates(self, dirs):

        # Check that the archive folders don't already exist
        for d in dirs:
            if exists(join(d, ARCHIVE)):
                raise CommandError(ARCHIVE_EXISTS % d)

        paths = []
        # Walk the directories to build a list of files to minimize
        # Currently not following symbolic links
        for d in dirs:
            archive_dir = join(d, ARCHIVE)
            for root, walk_dirs, files in walk(d):
                reverted_dirs = [x for x in walk_dirs if x.startswith(REVERTED)]
                for reverted_dir in reverted_dirs:
                    walk_dirs.remove(reverted_dir)  
                for name in files:
                    if not name.split('.')[-1] in ('.py', '.pyc'):
                        path= join(root,name)
                        paths.append([path, path.replace(d, archive_dir)])

        # Minimize the files
        num_files, before, after = 0, 0, 0
        for source_path, archive_path in paths:
            original = ''.join(open(source_path).readlines())
            minimized = minimize_template_text(original)

            num_files = num_files + 1
            before = before + len(original)
            after = after + len(minimized)

            d = dirname(archive_path)
            if not exists(d):
                makedirs(d)
            move(source_path, archive_path)
            open(source_path, 'wb').write(minimized)

        print 'Files:    %s' % num_files
        print 'Before:   %s' % before
        print 'After:    %s' % after
        print "Decrease: {0:.0%}".format((before - after) / float(before))

    def revert(self, dirs):
        # Put together Archive dirs
        # Check  the archive folders do exist
        archive_dirs = []
        for d in dirs:
            archive_dir = join(d, ARCHIVE)
            archive_dirs.append(archive_dir)
            if not exists(archive_dir):
                raise CommandError(ARCHIVE_DOESNT_EXIST % archive_dir)

        # Put together reverted dirs
        reverted_dirs = []
        for d in dirs:
            i = 1
            while exists(join(d, REVERTED + str(i))):
                i = i + 1
            reverted_dirs.append(join(d, REVERTED + str(i)))

        # zip everything up
        all_dirs = zip(archive_dirs, dirs, reverted_dirs)

        # Walk the directories and put together paths
        paths = []
        for archive_dir, d, reverted_dir in all_dirs:
            for root, walk_dirs, files in walk(archive_dir):
                reverted_dirs = [x for x in walk_dirs if x.startswith(REVERTED)]
                for reverted_dir in reverted_dirs:
                    walk_dirs.remove(reverted_dir)                
                for archive_name in files:
                    # Collect all the paths
                    archive_path = join(root, archive_name)
                    path = archive_path.replace(archive_dir, d)
                    reverted_path = archive_path.replace(archive_dir,
                                                         reverted_dir)
                    paths.append([archive_path, path, reverted_path])

        # Make the moves
        for archive_path, path, reverted_path in paths:
            # Create the directories
            d = dirname(path)
            if not exists(d): makedirs(d)
            d = dirname(reverted_path)
            if not exists(d): makedirs(d)

            move(path, reverted_path)
            move(archive_path, path)

        # Delete the archive folder
        for d in archive_dirs:
            rmtree(d)
