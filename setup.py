#!/usr/bin/env python
from distutils.core import setup
import codecs

long_description = codecs.open('README.rst', 'r', 'utf-8').read()

setup(name='django-template-minimizer',
      version='0.1.7',
      description=('Minimize your Django templates so that '
                   'your HTML is served up already minimized.'), 
      long_description=long_description,
      author='Charles Kaminski',
      author_email='CharlesKaminski@gmail.com',
      url='https://github.com/Charles-Kaminski/django-template-minimizer',
      license='MIT',
      py_modules=['tmin.__init__',
                  'tmin.management.__init__',
                  'tmin.management.commands.__init__',
                  'tmin.management.commands.minimizetemplates',
                  'tmin.management.commands._cssmin',
                  'tmin.management.commands._JavascriptMinify',
                  'tmin.management.commands._ManageMinimizers',
                  'tmin.management.commands._SimpleHTMLParser',
                  'tmin.management.commands._TemplateTextMinimizer',],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Django',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.5',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Internet :: WWW/HTTP :: WSGI',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Utilities',
      ] 
)