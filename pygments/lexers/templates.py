# -*- coding: utf-8 -*-
"""
    pygments.lexers.templates
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Lexers for various template engines' markup.

    :copyright: Copyright 2006-2009 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
try:
    set
except NameError:
    from sets import Set as set

from pygments.lexers.web import \
     PhpLexer, HtmlLexer, XmlLexer, JavascriptLexer, CssLexer
from pygments.lexers.agile import PythonLexer
from pygments.lexers.compiled import JavaLexer
from pygments.lexer import Lexer, DelegatingLexer, RegexLexer, bygroups, \
     include, using, this
from pygments.token import Error, Punctuation, \
     Text, Comment, Operator, Keyword, Name, String, Number, Other, Token
from pygments.util import html_doctype_matches, looks_like_xml

__all__ = ['HtmlPhpLexer', 'XmlPhpLexer', 'CssPhpLexer',
           'JavascriptPhpLexer', 'ErbLexer', 'RhtmlLexer',
           'XmlErbLexer', 'CssErbLexer', 'JavascriptErbLexer',
           'SmartyLexer', 'HtmlSmartyLexer', 'XmlSmartyLexer',
           'CssSmartyLexer', 'JavascriptSmartyLexer', 'DjangoLexer',
           'HtmlDjangoLexer', 'CssDjangoLexer', 'XmlDjangoLexer',
           'JavascriptDjangoLexer', 'GenshiLexer', 'HtmlGenshiLexer',
           'GenshiTextLexer', 'CssGenshiLexer', 'JavascriptGenshiLexer',
           'MyghtyLexer', 'MyghtyHtmlLexer', 'MyghtyXmlLexer',
           'MyghtyCssLexer', 'MyghtyJavascriptLexer', 'MakoLexer',
           'MakoHtmlLexer', 'MakoXmlLexer', 'MakoJavascriptLexer',
           'MakoCssLexer', 'JspLexer', 'CheetahLexer', 'CheetahHtmlLexer',
           'CheetahXmlLexer', 'CheetahJavascriptLexer',
           'EvoqueLexer', 'EvoqueHtmlLexer', 'EvoqueXmlLexer']


class ErbLexer(Lexer):
    """
    Generic `ERB <http://ruby-doc.org/core/classes/ERB.html>`_ (Ruby Templating)
    lexer.

    Just highlights ruby code between the preprocessor directives, other data
    is left untouched by the lexer.

    All options are also forwarded to the `RubyLexer`.
    """

    name = 'ERB'
    aliases = ['erb']
    mimetypes = ['application/x-ruby-templating']

    _block_re = re.compile(r'(<%%|%%>|<%=|<%#|<%-|<%|-%>|%>|^%[^%].*?$)', re.M)

    def __init__(self, **options):
        from pygments.lexers.agile import RubyLexer
        self.ruby_lexer = RubyLexer(**options)
        Lexer.__init__(self, **options)

    def get_tokens_unprocessed(self, text):
        """
        Since ERB doesn't allow "<%" and other tags inside of ruby
        blocks we have to use a split approach here that fails for
        that too.
        """
        tokens = self._block_re.split(text)
        tokens.reverse()
        state = idx = 0
        try:
            while True:
                # text
                if state == 0:
                    val = tokens.pop()
                    yield idx, Other, val
                    idx += len(val)
                    state = 1
                # block starts
                elif state == 1:
                    tag = tokens.pop()
                    # literals
                    if tag in ('<%%', '%%>'):
                        yield idx, Other, tag
                        idx += 3
                        state = 0
                    # comment
                    elif tag == '<%#':
                        yield idx, Comment.Preproc, tag
                        val = tokens.pop()
                        yield idx + 3, Comment, val
                        idx += 3 + len(val)
                        state = 2
                    # blocks or output
                    elif tag in ('<%', '<%=', '<%-'):
                        yield idx, Comment.Preproc, tag
                        idx += len(tag)
                        data = tokens.pop()
                        r_idx = 0
                        for r_idx, r_token, r_value in \
                            self.ruby_lexer.get_tokens_unprocessed(data):
                            yield r_idx + idx, r_token, r_value
                        idx += len(data)
                        state = 2
                    elif tag in ('%>', '-%>'):
                        yield idx, Error, tag
                        idx += len(tag)
                        state = 0
                    # % raw ruby statements
                    else:
                        yield idx, Comment.Preproc, tag[0]
                        r_idx = 0
                        for r_idx, r_token, r_value in \
                            self.ruby_lexer.get_tokens_unprocessed(tag[1:]):
                            yield idx + 1 + r_idx, r_token, r_value
                        idx += len(tag)
                        state = 0
                # block ends
                elif state == 2:
                    tag = tokens.pop()
                    if tag not in ('%>', '-%>'):
                        yield idx, Other, tag
                    else:
                        yield idx, Comment.Preproc, tag
                    idx += len(tag)
                    state = 0
        except IndexError:
            return

    def analyse_text(text):
        if '<%' in text and '%>' in text:
            return 0.4


class SmartyLexer(RegexLexer):
    """
    Generic `Smarty <http://smarty.php.net/>`_ template lexer.

    Just highlights smarty code between the preprocessor directives, other
    data is left untouched by the lexer.
    """

    name = 'Smarty'
    aliases = ['smarty']
    filenames = ['*.tpl']
    mimetypes = ['application/x-smarty']

    flags = re.MULTILINE | re.DOTALL

    tokens = {
        'root': [
            (r'[^{]+', Other),
            (r'(\{)(\*.*?\*)(\})',
             bygroups(Comment.Preproc, Comment, Comment.Preproc)),
            (r'(\{php\})(.*?)(\{/php\})',
             bygroups(Comment.Preproc, using(PhpLexer, startinline=True),
                      Comment.Preproc)),
            (r'(\{)(/?[a-zA-Z_][a-zA-Z0-9_]*)(\s*)',
             bygroups(Comment.Preproc, Name.Function, Text), 'smarty'),
            (r'\{', Comment.Preproc, 'smarty')
        ],
        'smarty': [
            (r'\s+', Text),
            (r'\}', Comment.Preproc, '#pop'),
            (r'#[a-zA-Z_][a-zA-Z0-9_]*#', Name.Variable),
            (r'\$[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z0-9_]+)*', Name.Variable),
            (r'[~!%^&*()+=|\[\]:;,.<>/?{}@-]', Operator),
            ('(true|false|null)\b', Keyword.Constant),
            (r"[0-9](\.[0-9]*)?(eE[+-][0-9])?[flFLdD]?|"
             r"0[xX][0-9a-fA-F]+[Ll]?", Number),
            (r'"(\\\\|\\"|[^"])*"', String.Double),
            (r"'(\\\\|\\'|[^'])*'", String.Single),
            (r'[a-zA-Z_][a-zA-Z0-9_]*', Name.Attribute)
        ]
    }

    def analyse_text(text):
        rv = 0.0
        if re.search('\{if\s+.*?\}.*?\{/if\}', text):
            rv += 0.15
        if re.search('\{include\s+file=.*?\}', text):
            rv += 0.15
        if re.search('\{foreach\s+.*?\}.*?\{/foreach\}', text):
            rv += 0.15
        if re.search('\{\$.*?\}', text):
            rv += 0.01
        return rv


class DjangoLexer(RegexLexer):
    """
    Generic `django <http://www.djangoproject.com/documentation/templates/>`_
    and `jinja <http://wsgiarea.pocoo.org/jinja/>`_ template lexer.

    It just highlights django/jinja code between the preprocessor directives,
    other data is left untouched by the lexer.
    """

    name = 'Django/Jinja'
    aliases = ['django', 'jinja']
    mimetypes = ['application/x-django-templating', 'application/x-jinja']

    flags = re.M | re.S

    tokens = {
        'root': [
            (r'[^{]+', Other),
            (r'\{\{', Comment.Preproc, 'var'),
            # jinja/django comments
            (r'\{[*#].*?[*#]\}', Comment),
            # django comments
            (r'(\{%)(-?\s*)(comment)(\s*-?)(%\})(.*?)'
             r'(\{%)(-?\s*)(endcomment)(\s*-?)(%\})',
             bygroups(Comment.Preproc, Text, Keyword, Text, Comment.Preproc,
                      Comment, Comment.Preproc, Text, Keyword, Text,
                      Comment.Preproc)),
            # raw jinja blocks
            (r'(\{%)(-?\s*)(raw)(\s*-?)(%\})(.*?)'
             r'(\{%)(-?\s*)(endraw)(\s*-?)(%\})',
             bygroups(Comment.Preproc, Text, Keyword, Text, Comment.Preproc,
                      Text, Comment.Preproc, Text, Keyword, Text,
                      Comment.Preproc)),
            # filter blocks
            (r'(\{%)(-?\s*)(filter)(\s+)([a-zA-Z_][a-zA-Z0-9_]*)',
             bygroups(Comment.Preproc, Text, Keyword, Text, Name.Function),
             'block'),
            (r'(\{%)(-?\s*)([a-zA-Z_][a-zA-Z0-9_]*)',
             bygroups(Comment.Preproc, Text, Keyword), 'block'),
            (r'\{', Other)
        ],
        'varnames': [
            (r'(\|)(\s*)([a-zA-Z_][a-zA-Z0-9_]*)',
             bygroups(Operator, Text, Name.Function)),
            (r'(is)(\s+)(not)?(\s+)?([a-zA-Z_][a-zA-Z0-9_]*)',
             bygroups(Keyword, Text, Keyword, Text, Name.Function)),
            (r'(_|true|false|none|True|False|None)\b', Keyword.Pseudo),
            (r'(in|as|reversed|recursive|not|and|or|is|if|else|import|'
             r'with(?:(?:out)?\s*context)?)\b', Keyword),
            (r'(loop|block|super|forloop)\b', Name.Builtin),
            (r'[a-zA-Z][a-zA-Z0-9_]*', Name.Variable),
            (r'\.[a-zA-Z0-9_]+', Name.Variable),
            (r':?"(\\\\|\\"|[^"])*"', String.Double),
            (r":?'(\\\\|\\'|[^'])*'", String.Single),
            (r'([{}()\[\]+\-*/,:]|[><=]=?)', Operator),
            (r"[0-9](\.[0-9]*)?(eE[+-][0-9])?[flFLdD]?|"
             r"0[xX][0-9a-fA-F]+[Ll]?", Number),
        ],
        'var': [
            (r'\s+', Text),
            (r'(-?)(\}\})', bygroups(Text, Comment.Preproc), '#pop'),
            include('varnames')
        ],
        'block': [
            (r'\s+', Text),
            (r'(-?)(%\})', bygroups(Text, Comment.Preproc), '#pop'),
            include('varnames'),
            (r'.', Punctuation)
        ]
    }

    def analyse_text(text):
        rv = 0.0
        if re.search(r'\{%\s*(block|extends)', text) is not None:
            rv += 0.4
        if re.search(r'\{%\s*if\s*.*?%\}', text) is not None:
            rv += 0.1
        if re.search(r'\{\{.*?\}\}', text) is not None:
            rv += 0.1
        return rv


class MyghtyLexer(RegexLexer):
    """
    Generic `myghty templates`_ lexer. Code that isn't Myghty
    markup is yielded as `Token.Other`.

    *New in Pygments 0.6.*

    .. _myghty templates: http://www.myghty.org/
    """

    name = 'Myghty'
    aliases = ['myghty']
    filenames = ['*.myt', 'autodelegate']
    mimetypes = ['application/x-myghty']

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'(<%(def|method))(\s*)(.*?)(>)(.*?)(</%\2\s*>)(?s)',
             bygroups(Name.Tag, None, Text, Name.Function, Name.Tag,
                      using(this), Name.Tag)),
            (r'(<%(\w+))(.*?)(>)(.*?)(</%\2\s*>)(?s)',
             bygroups(Name.Tag, None, Name.Function, Name.Tag,
                      using(PythonLexer), Name.Tag)),
            (r'(<&[^|])(.*?)(,.*?)?(&>)',
             bygroups(Name.Tag, Name.Function, using(PythonLexer), Name.Tag)),
            (r'(<&\|)(.*?)(,.*?)?(&>)(?s)',
             bygroups(Name.Tag, Name.Function, using(PythonLexer), Name.Tag)),
            (r'</&>', Name.Tag),
            (r'(<%!?)(.*?)(%>)(?s)',
             bygroups(Name.Tag, using(PythonLexer), Name.Tag)),
            (r'(?<=^)#[^\n]*(\n|\Z)', Comment),
            (r'(?<=^)(%)([^\n]*)(\n|\Z)',
             bygroups(Name.Tag, using(PythonLexer), Other)),
            (r"""(?sx)
                 (.+?)               # anything, followed by:
                 (?:
                  (?<=\n)(?=[%#]) |  # an eval or comment line
                  (?=</?[%&]) |      # a substitution or block or
                                     # call start or end
                                     # - don't consume
                  (\\\n) |           # an escaped newline
                  \Z                 # end of string
                 )""", bygroups(Other, Operator)),
        ]
    }


class MyghtyHtmlLexer(DelegatingLexer):
    """
    Subclass of the `MyghtyLexer` that highlights unlexer data
    with the `HtmlLexer`.

    *New in Pygments 0.6.*
    """

    name = 'HTML+Myghty'
    aliases = ['html+myghty']
    mimetypes = ['text/html+myghty']

    def __init__(self, **options):
        super(MyghtyHtmlLexer, self).__init__(HtmlLexer, MyghtyLexer,
                                              **options)


class MyghtyXmlLexer(DelegatingLexer):
    """
    Subclass of the `MyghtyLexer` that highlights unlexer data
    with the `XmlLexer`.

    *New in Pygments 0.6.*
    """

    name = 'XML+Myghty'
    aliases = ['xml+myghty']
    mimetypes = ['application/xml+myghty']

    def __init__(self, **options):
        super(MyghtyXmlLexer, self).__init__(XmlLexer, MyghtyLexer,
                                             **options)


class MyghtyJavascriptLexer(DelegatingLexer):
    """
    Subclass of the `MyghtyLexer` that highlights unlexer data
    with the `JavascriptLexer`.

    *New in Pygments 0.6.*
    """

    name = 'JavaScript+Myghty'
    aliases = ['js+myghty', 'javascript+myghty']
    mimetypes = ['application/x-javascript+myghty',
                 'text/x-javascript+myghty',
                 'text/javascript+mygthy']

    def __init__(self, **options):
        super(MyghtyJavascriptLexer, self).__init__(JavascriptLexer,
                                                    MyghtyLexer, **options)


class MyghtyCssLexer(DelegatingLexer):
    """
    Subclass of the `MyghtyLexer` that highlights unlexer data
    with the `CssLexer`.

    *New in Pygments 0.6.*
    """

    name = 'CSS+Myghty'
    aliases = ['css+myghty']
    mimetypes = ['text/css+myghty']

    def __init__(self, **options):
        super(MyghtyCssLexer, self).__init__(CssLexer, MyghtyLexer,
                                             **options)


class MakoLexer(RegexLexer):
    """
    Generic `mako templates`_ lexer. Code that isn't Mako
    markup is yielded as `Token.Other`.

    *New in Pygments 0.7.*

    .. _mako templates: http://www.makotemplates.org/
    """

    name = 'Mako'
    aliases = ['mako']
    filenames = ['*.mao']
    mimetypes = ['application/x-mako']

    tokens = {
        'root': [
            (r'(\s*)(%)(\s*end(?:\w+))(\n|\Z)',
             bygroups(Text, Comment.Preproc, Keyword, Other)),
            (r'(\s*)(%)([^\n]*)(\n|\Z)',
             bygroups(Text, Comment.Preproc, using(PythonLexer), Other)),
            (r'(\s*)(##[^\n]*)(\n|\Z)',
             bygroups(Text, Comment.Preproc, Other)),
            (r'(?s)<%doc>.*?</%doc>', Comment.Preproc),
            (r'(<%)([\w\.\:]+)',
             bygroups(Comment.Preproc, Name.Builtin), 'tag'),
            (r'(</%)([\w\.\:]+)(>)',
             bygroups(Comment.Preproc, Name.Builtin, Comment.Preproc)),
            (r'<%(?=([\w\.\:]+))', Comment.Preproc, 'ondeftags'),
            (r'(<%(?:!?))(.*?)(%>)(?s)',
             bygroups(Comment.Preproc, using(PythonLexer), Comment.Preproc)),
            (r'(\$\{)(.*?)(\})',
             bygroups(Comment.Preproc, using(PythonLexer), Comment.Preproc)),
            (r'''(?sx)
                (.+?)                # anything, followed by:
                (?:
<<<<<<< local
                 (?<=\n)(?=%|\#\#) |# an eval or comment line
                 (?=\#\*) |         # multiline comment
                 (?=</?%) |         # a python block
                                    # call start or end
                 (?=\$\{) |         # a substitution
=======
                 (?<=\n)(?=%|\#\#) | # an eval or comment line
                 (?=\#\*) |          # multiline comment
                 (?=</?%) |          # a python block
                                     # call start or end
                 (?=\$\{) |          # a substitution
>>>>>>> other
                 (?<=\n)(?=\s*%) |
                                     # - don't consume
                 (\\\n) |            # an escaped newline
                 \Z                  # end of string
                )
            ''', bygroups(Other, Operator)),
            (r'\s+', Text),
        ],
        'ondeftags': [
            (r'<%', Comment.Preproc),
            (r'(?<=<%)(include|inherit|namespace|page)', Name.Builtin),
            include('tag'),
        ],
        'tag': [
            (r'((?:\w+)\s*=)\s*(".*?")',
             bygroups(Name.Attribute, String)),
            (r'/?\s*>', Comment.Preproc, '#pop'),
            (r'\s+', Text),
        ],
        'attr': [
            ('".*?"', String, '#pop'),
            ("'.*?'", String, '#pop'),
            (r'[^\s>]+', String, '#pop'),
        ],
    }


class MakoHtmlLexer(DelegatingLexer):
    """
    Subclass of the `MakoLexer` that highlights unlexed data
    with the `HtmlLexer`.

    *New in Pygments 0.7.*
    """

    name = 'HTML+Mako'
    aliases = ['html+mako']
    mimetypes = ['text/html+mako']

    def __init__(self, **options):
        super(MakoHtmlLexer, self).__init__(HtmlLexer, MakoLexer,
                                              **options)

class MakoXmlLexer(DelegatingLexer):
    """
    Subclass of the `MakoLexer` that highlights unlexer data
    with the `XmlLexer`.

    *New in Pygments 0.7.*
    """

    name = 'XML+Mako'
    aliases = ['xml+mako']
    mimetypes = ['application/xml+mako']

    def __init__(self, **options):
        super(MakoXmlLexer, self).__init__(XmlLexer, MakoLexer,
                                             **options)

class MakoJavascriptLexer(DelegatingLexer):
    """
    Subclass of the `MakoLexer` that highlights unlexer data
    with the `JavascriptLexer`.

    *New in Pygments 0.7.*
    """

    name = 'JavaScript+Mako'
    aliases = ['js+mako', 'javascript+mako']
    mimetypes = ['application/x-javascript+mako',
                 'text/x-javascript+mako',
                 'text/javascript+mako']

    def __init__(self, **options):
        super(MakoJavascriptLexer, self).__init__(JavascriptLexer,
                                                    MakoLexer, **options)

class MakoCssLexer(DelegatingLexer):
    """
    Subclass of the `MakoLexer` that highlights unlexer data
    with the `CssLexer`.

    *New in Pygments 0.7.*
    """

    name = 'CSS+Mako'
    aliases = ['css+mako']
    mimetypes = ['text/css+mako']

    def __init__(self, **options):
        super(MakoCssLexer, self).__init__(CssLexer, MakoLexer,
                                             **options)


# Genshi and Cheetah lexers courtesy of Matt Good.

class CheetahPythonLexer(Lexer):
    """
    Lexer for handling Cheetah's special $ tokens in Python syntax.
    """

    def get_tokens_unprocessed(self, text):
        pylexer = PythonLexer(**self.options)
        for pos, type_, value in pylexer.get_tokens_unprocessed(text):
            if type_ == Token.Error and value == '$':
                type_ = Comment.Preproc
            yield pos, type_, value


class CheetahLexer(RegexLexer):
    """
    Generic `cheetah templates`_ lexer. Code that isn't Cheetah
    markup is yielded as `Token.Other`.  This also works for
    `spitfire templates`_ which use the same syntax.

    .. _cheetah templates: http://www.cheetahtemplate.org/
    .. _spitfire templates: http://code.google.com/p/spitfire/
    """

    name = 'Cheetah'
    aliases = ['cheetah', 'spitfire']
    filenames = ['*.tmpl', '*.spt']
    mimetypes = ['application/x-cheetah', 'application/x-spitfire']

    tokens = {
        'root': [
            (r'(##[^\n]*)$',
             (bygroups(Comment))),
            (r'#[*](.|\n)*?[*]#', Comment),
            (r'#end[^#\n]*(?:#|$)', Comment.Preproc),
            (r'#slurp$', Comment.Preproc),
            (r'(#[a-zA-Z]+)([^#\n]*)(#|$)',
             (bygroups(Comment.Preproc, using(CheetahPythonLexer),
                       Comment.Preproc))),
            # TODO support other Python syntax like $foo['bar']
            (r'(\$)([a-zA-Z_][a-zA-Z0-9_\.]*[a-zA-Z0-9_])',
             bygroups(Comment.Preproc, using(CheetahPythonLexer))),
            (r'(\$\{!?)(.*?)(\})(?s)',
             bygroups(Comment.Preproc, using(CheetahPythonLexer),
                      Comment.Preproc)),
            (r'''(?sx)
                (.+?)               # anything, followed by:
                (?:
                 (?=[#][#a-zA-Z]*) |   # an eval comment
                 (?=\$[a-zA-Z_{]) | # a substitution
                 \Z                 # end of string
                )
            ''', Other),
            (r'\s+', Text),
        ],
    }


class CheetahHtmlLexer(DelegatingLexer):
    """
    Subclass of the `CheetahLexer` that highlights unlexer data
    with the `HtmlLexer`.
    """

    name = 'HTML+Cheetah'
    aliases = ['html+cheetah', 'html+spitfire']
    mimetypes = ['text/html+cheetah', 'text/html+spitfire']

    def __init__(self, **options):
        super(CheetahHtmlLexer, self).__init__(HtmlLexer, CheetahLexer,
                                               **options)


class CheetahXmlLexer(DelegatingLexer):
    """
    Subclass of the `CheetahLexer` that highlights unlexer data
    with the `XmlLexer`.
    """

    name = 'XML+Cheetah'
    aliases = ['xml+cheetah', 'xml+spitfire']
    mimetypes = ['application/xml+cheetah', 'application/xml+spitfire']

    def __init__(self, **options):
        super(CheetahXmlLexer, self).__init__(XmlLexer, CheetahLexer,
                                              **options)


class CheetahJavascriptLexer(DelegatingLexer):
    """
    Subclass of the `CheetahLexer` that highlights unlexer data
    with the `JavascriptLexer`.
    """

    name = 'JavaScript+Cheetah'
    aliases = ['js+cheetah', 'javascript+cheetah',
               'js+spitfire', 'javascript+spitfire']
    mimetypes = ['application/x-javascript+cheetah',
                 'text/x-javascript+cheetah',
                 'text/javascript+cheetah',
                 'application/x-javascript+spitfire',
                 'text/x-javascript+spitfire',
                 'text/javascript+spitfire']

    def __init__(self, **options):
        super(CheetahJavascriptLexer, self).__init__(JavascriptLexer,
                                                     CheetahLexer, **options)


class GenshiTextLexer(RegexLexer):
    """
    A lexer that highlights `genshi <http://genshi.edgewall.org/>`_ text
    templates.
    """

    name = 'Genshi Text'
    aliases = ['genshitext']
    mimetypes = ['application/x-genshi-text', 'text/x-genshi']

    tokens = {
        'root': [
            (r'[^#\$\s]+', Other),
            (r'^(\s*)(##.*)$', bygroups(Text, Comment)),
            (r'^(\s*)(#)', bygroups(Text, Comment.Preproc), 'directive'),
            include('variable'),
            (r'[#\$\s]', Other),
        ],
        'directive': [
            (r'\n', Text, '#pop'),
            (r'(?:def|for|if)\s+.*', using(PythonLexer), '#pop'),
            (r'(choose|when|with)([^\S\n]+)(.*)',
             bygroups(Keyword, Text, using(PythonLexer)), '#pop'),
            (r'(choose|otherwise)\b', Keyword, '#pop'),
            (r'(end\w*)([^\S\n]*)(.*)', bygroups(Keyword, Text, Comment), '#pop'),
        ],
        'variable': [
            (r'(?<!\$)(\$\{)(.+?)(\})',
             bygroups(Comment.Preproc, using(PythonLexer), Comment.Preproc)),
            (r'(?<!\$)(\$)([a-zA-Z_][a-zA-Z0-9_\.]*)',
             Name.Variable),
        ]
    }


class GenshiMarkupLexer(RegexLexer):
    """
    Base lexer for Genshi markup, used by `HtmlGenshiLexer` and
    `GenshiLexer`.
    """

    flags = re.DOTALL

    tokens = {
        'root': [
            (r'[^<\$]+', Other),
            (r'(<\?python)(.*?)(\?>)',
             bygroups(Comment.Preproc, using(PythonLexer), Comment.Preproc)),
            # yield style and script blocks as Other
            (r'<\s*(script|style)\s*.*?>.*?<\s*/\1\s*>', Other),
            (r'<\s*py:[a-zA-Z0-9]+', Name.Tag, 'pytag'),
            (r'<\s*[a-zA-Z0-9:]+', Name.Tag, 'tag'),
            include('variable'),
            (r'[<\$]', Other),
        ],
        'pytag': [
            (r'\s+', Text),
            (r'[a-zA-Z0-9_:-]+\s*=', Name.Attribute, 'pyattr'),
            (r'/?\s*>', Name.Tag, '#pop'),
        ],
        'pyattr': [
            ('(")(.*?)(")', bygroups(String, using(PythonLexer), String), '#pop'),
            ("(')(.*?)(')", bygroups(String, using(PythonLexer), String), '#pop'),
            (r'[^\s>]+', String, '#pop'),
        ],
        'tag': [
            (r'\s+', Text),
            (r'py:[a-zA-Z0-9_-]+\s*=', Name.Attribute, 'pyattr'),
            (r'[a-zA-Z0-9_:-]+\s*=', Name.Attribute, 'attr'),
            (r'/?\s*>', Name.Tag, '#pop'),
        ],
        'attr': [
            ('"', String, 'attr-dstring'),
            ("'", String, 'attr-sstring'),
            (r'[^\s>]*', String, '#pop')
        ],
        'attr-dstring': [
            ('"', String, '#pop'),
            include('strings'),
            ("'", String)
        ],
        'attr-sstring': [
            ("'", String, '#pop'),
            include('strings'),
            ("'", String)
        ],
        'strings': [
            ('[^"\'$]+', String),
            include('variable')
        ],
        'variable': [
            (r'(?<!\$)(\$\{)(.+?)(\})',
             bygroups(Comment.Preproc, using(PythonLexer), Comment.Preproc)),
            (r'(?<!\$)(\$)([a-zA-Z_][a-zA-Z0-9_\.]*)',
             Name.Variable),
        ]
    }


class HtmlGenshiLexer(DelegatingLexer):
    """
    A lexer that highlights `genshi <http://genshi.edgewall.org/>`_ and
    `kid <http://kid-templating.org/>`_ kid HTML templates.
    """

    name = 'HTML+Genshi'
    aliases = ['html+genshi', 'html+kid']
    alias_filenames = ['*.html', '*.htm', '*.xhtml']
    mimetypes = ['text/html+genshi']

    def __init__(self, **options):
        super(HtmlGenshiLexer, self).__init__(HtmlLexer, GenshiMarkupLexer,
                                              **options)

    def analyse_text(text):
        rv = 0.0
        if re.search('\$\{.*?\}', text) is not None:
            rv += 0.2
        if re.search('py:(.*?)=["\']', text) is not None:
            rv += 0.2
        return rv + HtmlLexer.analyse_text(text) - 0.01


class GenshiLexer(DelegatingLexer):
    """
    A lexer that highlights `genshi <http://genshi.edgewall.org/>`_ and
    `kid <http://kid-templating.org/>`_ kid XML templates.
    """

    name = 'Genshi'
    aliases = ['genshi', 'kid', 'xml+genshi', 'xml+kid']
    filenames = ['*.kid']
    alias_filenames = ['*.xml']
    mimetypes = ['application/x-genshi', 'application/x-kid']

    def __init__(self, **options):
        super(GenshiLexer, self).__init__(XmlLexer, GenshiMarkupLexer,
                                          **options)

    def analyse_text(text):
        rv = 0.0
        if re.search('\$\{.*?\}', text) is not None:
            rv += 0.2
        if re.search('py:(.*?)=["\']', text) is not None:
            rv += 0.2
        return rv + XmlLexer.analyse_text(text) - 0.01


class JavascriptGenshiLexer(DelegatingLexer):
    """
    A lexer that highlights javascript code in genshi text templates.
    """

    name = 'JavaScript+Genshi Text'
    aliases = ['js+genshitext', 'js+genshi', 'javascript+genshitext',
               'javascript+genshi']
    alias_filenames = ['*.js']
    mimetypes = ['application/x-javascript+genshi',
                 'text/x-javascript+genshi',
                 'text/javascript+genshi']

    def __init__(self, **options):
        super(JavascriptGenshiLexer, self).__init__(JavascriptLexer,
                                                    GenshiTextLexer,
                                                    **options)

    def analyse_text(text):
        return GenshiLexer.analyse_text(text) - 0.05


class CssGenshiLexer(DelegatingLexer):
    """
    A lexer that highlights CSS definitions in genshi text templates.
    """

    name = 'CSS+Genshi Text'
    aliases = ['css+genshitext', 'css+genshi']
    alias_filenames = ['*.css']
    mimetypes = ['text/css+genshi']

    def __init__(self, **options):
        super(CssGenshiLexer, self).__init__(CssLexer, GenshiTextLexer,
                                             **options)

    def analyse_text(text):
        return GenshiLexer.analyse_text(text) - 0.05


class RhtmlLexer(DelegatingLexer):
    """
    Subclass of the ERB lexer that highlights the unlexed data with the
    html lexer.

    Nested Javascript and CSS is highlighted too.
    """

    name = 'RHTML'
    aliases = ['rhtml', 'html+erb', 'html+ruby']
    filenames = ['*.rhtml']
    alias_filenames = ['*.html', '*.htm', '*.xhtml']
    mimetypes = ['text/html+ruby']

    def __init__(self, **options):
        super(RhtmlLexer, self).__init__(HtmlLexer, ErbLexer, **options)

    def analyse_text(text):
        rv = ErbLexer.analyse_text(text) - 0.01
        if html_doctype_matches(text):
            # one more than the XmlErbLexer returns
            rv += 0.5
        return rv


class XmlErbLexer(DelegatingLexer):
    """
    Subclass of `ErbLexer` which highlights data outside preprocessor
    directives with the `XmlLexer`.
    """

    name = 'XML+Ruby'
    aliases = ['xml+erb', 'xml+ruby']
    alias_filenames = ['*.xml']
    mimetypes = ['application/xml+ruby']

    def __init__(self, **options):
        super(XmlErbLexer, self).__init__(XmlLexer, ErbLexer, **options)

    def analyse_text(text):
        rv = ErbLexer.analyse_text(text) - 0.01
        if looks_like_xml(text):
            rv += 0.4
        return rv


class CssErbLexer(DelegatingLexer):
    """
    Subclass of `ErbLexer` which highlights unlexed data with the `CssLexer`.
    """

    name = 'CSS+Ruby'
    aliases = ['css+erb', 'css+ruby']
    alias_filenames = ['*.css']
    mimetypes = ['text/css+ruby']

    def __init__(self, **options):
        super(CssErbLexer, self).__init__(CssLexer, ErbLexer, **options)

    def analyse_text(text):
        return ErbLexer.analyse_text(text) - 0.05


class JavascriptErbLexer(DelegatingLexer):
    """
    Subclass of `ErbLexer` which highlights unlexed data with the
    `JavascriptLexer`.
    """

    name = 'JavaScript+Ruby'
    aliases = ['js+erb', 'javascript+erb', 'js+ruby', 'javascript+ruby']
    alias_filenames = ['*.js']
    mimetypes = ['application/x-javascript+ruby',
                 'text/x-javascript+ruby',
                 'text/javascript+ruby']

    def __init__(self, **options):
        super(JavascriptErbLexer, self).__init__(JavascriptLexer, ErbLexer,
                                                 **options)

    def analyse_text(text):
        return ErbLexer.analyse_text(text) - 0.05


class HtmlPhpLexer(DelegatingLexer):
    """
    Subclass of `PhpLexer` that highlights unhandled data with the `HtmlLexer`.

    Nested Javascript and CSS is highlighted too.
    """

    name = 'HTML+PHP'
    aliases = ['html+php']
    filenames = ['*.phtml']
    alias_filenames = ['*.php', '*.html', '*.htm', '*.xhtml',
                       '*.php[345]']
    mimetypes = ['application/x-php',
                 'application/x-httpd-php', 'application/x-httpd-php3',
                 'application/x-httpd-php4', 'application/x-httpd-php5']

    def __init__(self, **options):
        super(HtmlPhpLexer, self).__init__(HtmlLexer, PhpLexer, **options)

    def analyse_text(text):
        rv = PhpLexer.analyse_text(text) - 0.01
        if html_doctype_matches(text):
            rv += 0.5
        return rv


class XmlPhpLexer(DelegatingLexer):
    """
    Subclass of `PhpLexer` that higlights unhandled data with the `XmlLexer`.
    """

    name = 'XML+PHP'
    aliases = ['xml+php']
    alias_filenames = ['*.xml', '*.php', '*.php[345]']
    mimetypes = ['application/xml+php']

    def __init__(self, **options):
        super(XmlPhpLexer, self).__init__(XmlLexer, PhpLexer, **options)

    def analyse_text(text):
        rv = PhpLexer.analyse_text(text) - 0.01
        if looks_like_xml(text):
            rv += 0.4
        return rv


class CssPhpLexer(DelegatingLexer):
    """
    Subclass of `PhpLexer` which highlights unmatched data with the `CssLexer`.
    """

    name = 'CSS+PHP'
    aliases = ['css+php']
    alias_filenames = ['*.css']
    mimetypes = ['text/css+php']

    def __init__(self, **options):
        super(CssPhpLexer, self).__init__(CssLexer, PhpLexer, **options)

    def analyse_text(text):
        return PhpLexer.analyse_text(text) - 0.05


class JavascriptPhpLexer(DelegatingLexer):
    """
    Subclass of `PhpLexer` which highlights unmatched data with the
    `JavascriptLexer`.
    """

    name = 'JavaScript+PHP'
    aliases = ['js+php', 'javascript+php']
    alias_filenames = ['*.js']
    mimetypes = ['application/x-javascript+php',
                 'text/x-javascript+php',
                 'text/javascript+php']

    def __init__(self, **options):
        super(JavascriptPhpLexer, self).__init__(JavascriptLexer, PhpLexer,
                                                 **options)

    def analyse_text(text):
        return PhpLexer.analyse_text(text)


class HtmlSmartyLexer(DelegatingLexer):
    """
    Subclass of the `SmartyLexer` that highighlights unlexed data with the
    `HtmlLexer`.

    Nested Javascript and CSS is highlighted too.
    """

    name = 'HTML+Smarty'
    aliases = ['html+smarty']
    alias_filenames = ['*.html', '*.htm', '*.xhtml', '*.tpl']
    mimetypes = ['text/html+smarty']

    def __init__(self, **options):
        super(HtmlSmartyLexer, self).__init__(HtmlLexer, SmartyLexer, **options)

    def analyse_text(text):
        rv = SmartyLexer.analyse_text(text) - 0.01
        if html_doctype_matches(text):
            rv += 0.5
        return rv


class XmlSmartyLexer(DelegatingLexer):
    """
    Subclass of the `SmartyLexer` that highlights unlexed data with the
    `XmlLexer`.
    """

    name = 'XML+Smarty'
    aliases = ['xml+smarty']
    alias_filenames = ['*.xml', '*.tpl']
    mimetypes = ['application/xml+smarty']

    def __init__(self, **options):
        super(XmlSmartyLexer, self).__init__(XmlLexer, SmartyLexer, **options)

    def analyse_text(text):
        rv = SmartyLexer.analyse_text(text) - 0.01
        if looks_like_xml(text):
            rv += 0.4
        return rv


class CssSmartyLexer(DelegatingLexer):
    """
    Subclass of the `SmartyLexer` that highlights unlexed data with the
    `CssLexer`.
    """

    name = 'CSS+Smarty'
    aliases = ['css+smarty']
    alias_filenames = ['*.css', '*.tpl']
    mimetypes = ['text/css+smarty']

    def __init__(self, **options):
        super(CssSmartyLexer, self).__init__(CssLexer, SmartyLexer, **options)

    def analyse_text(text):
        return SmartyLexer.analyse_text(text) - 0.05


class JavascriptSmartyLexer(DelegatingLexer):
    """
    Subclass of the `SmartyLexer` that highlights unlexed data with the
    `JavascriptLexer`.
    """

    name = 'JavaScript+Smarty'
    aliases = ['js+smarty', 'javascript+smarty']
    alias_filenames = ['*.js', '*.tpl']
    mimetypes = ['application/x-javascript+smarty',
                 'text/x-javascript+smarty',
                 'text/javascript+smarty']

    def __init__(self, **options):
        super(JavascriptSmartyLexer, self).__init__(JavascriptLexer, SmartyLexer,
                                                    **options)

    def analyse_text(text):
        return SmartyLexer.analyse_text(text) - 0.05


class HtmlDjangoLexer(DelegatingLexer):
    """
    Subclass of the `DjangoLexer` that highighlights unlexed data with the
    `HtmlLexer`.

    Nested Javascript and CSS is highlighted too.
    """

    name = 'HTML+Django/Jinja'
    aliases = ['html+django', 'html+jinja']
    alias_filenames = ['*.html', '*.htm', '*.xhtml']
    mimetypes = ['text/html+django', 'text/html+jinja']

    def __init__(self, **options):
        super(HtmlDjangoLexer, self).__init__(HtmlLexer, DjangoLexer, **options)

    def analyse_text(text):
        rv = DjangoLexer.analyse_text(text) - 0.01
        if html_doctype_matches(text):
            rv += 0.5
        return rv


class XmlDjangoLexer(DelegatingLexer):
    """
    Subclass of the `DjangoLexer` that highlights unlexed data with the
    `XmlLexer`.
    """

    name = 'XML+Django/Jinja'
    aliases = ['xml+django', 'xml+jinja']
    alias_filenames = ['*.xml']
    mimetypes = ['application/xml+django', 'application/xml+jinja']

    def __init__(self, **options):
        super(XmlDjangoLexer, self).__init__(XmlLexer, DjangoLexer, **options)

    def analyse_text(text):
        rv = DjangoLexer.analyse_text(text) - 0.01
        if looks_like_xml(text):
            rv += 0.4
        return rv


class CssDjangoLexer(DelegatingLexer):
    """
    Subclass of the `DjangoLexer` that highlights unlexed data with the
    `CssLexer`.
    """

    name = 'CSS+Django/Jinja'
    aliases = ['css+django', 'css+jinja']
    alias_filenames = ['*.css']
    mimetypes = ['text/css+django', 'text/css+jinja']

    def __init__(self, **options):
        super(CssDjangoLexer, self).__init__(CssLexer, DjangoLexer, **options)

    def analyse_text(text):
        return DjangoLexer.analyse_text(text) - 0.05


class JavascriptDjangoLexer(DelegatingLexer):
    """
    Subclass of the `DjangoLexer` that highlights unlexed data with the
    `JavascriptLexer`.
    """

    name = 'JavaScript+Django/Jinja'
    aliases = ['js+django', 'javascript+django',
               'js+jinja', 'javascript+jinja']
    alias_filenames = ['*.js']
    mimetypes = ['application/x-javascript+django',
                 'application/x-javascript+jinja',
                 'text/x-javascript+django',
                 'text/x-javascript+jinja',
                 'text/javascript+django',
                 'text/javascript+jinja']

    def __init__(self, **options):
        super(JavascriptDjangoLexer, self).__init__(JavascriptLexer, DjangoLexer,
                                                    **options)

    def analyse_text(text):
        return DjangoLexer.analyse_text(text) - 0.05


class JspRootLexer(RegexLexer):
    """
    Base for the `JspLexer`. Yields `Token.Other` for area outside of
    JSP tags.

    *New in Pygments 0.7.*
    """

    tokens = {
        'root': [
            (r'<%\S?', Keyword, 'sec'),
            # FIXME: I want to make these keywords but still parse attributes.
            (r'</?jsp:(forward|getProperty|include|plugin|setProperty|useBean).*?>',
             Keyword),
            (r'[^<]+', Other),
            (r'<', Other),
        ],
        'sec': [
            (r'%>', Keyword, '#pop'),
            # note: '\w\W' != '.' without DOTALL.
            (r'[\w\W]+?(?=%>|\Z)', using(JavaLexer)),
        ],
    }


class JspLexer(DelegatingLexer):
    """
    Lexer for Java Server Pages.

    *New in Pygments 0.7.*
    """
    name = 'Java Server Page'
    aliases = ['jsp']
    filenames = ['*.jsp']
    mimetypes = ['application/x-jsp']

    def __init__(self, **options):
        super(JspLexer, self).__init__(XmlLexer, JspRootLexer, **options)

    def analyse_text(text):
        rv = JavaLexer.analyse_text(text) - 0.01
        if looks_like_xml(text):
            rv += 0.4
        if '<%' in text and '%>' in text:
            rv += 0.1
        return rv


class EvoqueLexer(RegexLexer):
    """
    For files using the Evoque templating system.

    *New in Pygments 1.1.*
    """
    name = 'Evoque'
    aliases = ['evoque']
    filenames = ['*.evoque']
    mimetypes = ['application/x-evoque']

    flags = re.DOTALL

    tokens = {
        'root': [
            (r'[^#$]+', Other),
            (r'#\[', Comment.Multiline, 'comment'),
            (r'\$\$', Other),
            # svn keywords
            (r'\$\w+:[^$\n]*\$', Comment.Multiline),
            # directives: begin, end
            (r'(\$)(begin|end)(\{(%)?)(.*?)((?(4)%)\})',
             bygroups(Punctuation, Name.Builtin, Punctuation, None,
                      String, Punctuation, None)),
            # directives: evoque, overlay
            # see doc for handling first name arg: /directives/evoque/
            #+ minor inconsistency: the "name" in e.g. $overlay{name=site_base}
            # should be using(PythonLexer), not passed out as String
            (r'(\$)(evoque|overlay)(\{(%)?)(\s*[#\w\-"\'.]+[^=,%}]+?)?'
             r'(.*?)((?(4)%)\})',
             bygroups(Punctuation, Name.Builtin, Punctuation, None,
                      String, using(PythonLexer), Punctuation, None)),
            # directives: if, for, prefer, test
            (r'(\$)(\w+)(\{(%)?)(.*?)((?(4)%)\})',
             bygroups(Punctuation, Name.Builtin, Punctuation, None,
                      using(PythonLexer), Punctuation, None)),
            # directive clauses (no {} expression)
            (r'(\$)(else|rof|fi)', bygroups(Punctuation, Name.Builtin)),
            # expressions
            (r'(\$\{(%)?)(.*?)((!)(.*?))?((?(2)%)\})',
             bygroups(Punctuation, None, using(PythonLexer),
                      Name.Builtin, None, None, Punctuation, None)),
            (r'#', Other),
        ],
        'comment': [
            (r'[^\]#]', Comment.Multiline),
            (r'#\[', Comment.Multiline, '#push'),
            (r'\]#', Comment.Multiline, '#pop'),
            (r'[\]#]', Comment.Multiline)
        ],
    }

class EvoqueHtmlLexer(DelegatingLexer):
    """
    Subclass of the `EvoqueLexer` that highlights unlexed data with the
    `HtmlLexer`.

    *New in Pygments 1.1.*
    """
    name = 'HTML+Evoque'
    aliases = ['html+evoque']
    filenames = ['*.html']
    mimetypes = ['text/html+evoque']

    def __init__(self, **options):
        super(EvoqueHtmlLexer, self).__init__(HtmlLexer, EvoqueLexer,
                                              **options)

class EvoqueXmlLexer(DelegatingLexer):
    """
    Subclass of the `EvoqueLexer` that highlights unlexed data with the
    `XmlLexer`.

    *New in Pygments 1.1.*
    """
    name = 'XML+Evoque'
    aliases = ['xml+evoque']
    filenames = ['*.xml']
    mimetypes = ['application/xml+evoque']

    def __init__(self, **options):
        super(EvoqueXmlLexer, self).__init__(XmlLexer, EvoqueLexer,
                                             **options)
