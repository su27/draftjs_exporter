from __future__ import absolute_import, unicode_literals

import inspect
import re

from lxml import etree, html

# Python 2/3 unicode compatibility hack.
# See http://stackoverflow.com/questions/6812031/how-to-make-unicode-string-with-python3
XLINK = 'http://www.w3.org/1999/xlink'

try:
    UNICODE_EXISTS = bool(type(unicode))
except NameError:
    def unicode(s):
        return str(s)


def clean_str(string):
    # See http://stackoverflow.com/questions/8733233/filtering-out-certain-bytes-in-python
    return re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\u10000-\u10FFFF]+', '', string)


class DOM(object):
    """
    Wrapper around our HTML building library to facilitate changes.
    """
    @staticmethod
    def create_tag(type_, attributes=None):
        return etree.Element(type_, attrib=attributes)

    @staticmethod
    def create_element(type_=None, props=None, *children):
        """
        Signature inspired by React.createElement.
        createElement(
          string/ReactClass type,
          [object props],
          [children ...]
        )
        https://facebook.github.io/react/docs/top-level-api.html#react.createelement
        """
        if not type_:
            return DOM.create_document_fragment()

        if len(children) and isinstance(children[0], (list, tuple)):
            children = children[0]

        props = props or {}

        if 'className' in props:
            props['class'] = props.pop('className')

        if 'xlink:href' in props:
            props['{%s}href' % XLINK] = props.pop('xlink:href')

        if inspect.isclass(type_):
            elt = type_().render(props)
        else:
            attributes = {k: str(v) for k, v in props.items() if v is not None}
            elt = DOM.create_tag(type_, attributes)

        for child in children:
            DOM.append_child(elt, child)

        return elt

    @staticmethod
    def create_document_fragment():
        return DOM.create_tag('fragment')

    @staticmethod
    def create_text_node(text):
        elt = DOM.create_tag('textnode')
        DOM.set_text_content(elt, text)
        return elt

    @staticmethod
    def parse_html(markup):
        return html.fromstring(markup)

    @staticmethod
    def append_child(elt, child):
        if child not in (None, ''):
            if hasattr(child, 'tag'):
                elt.append(child)
            else:
                elt_text = DOM.get_text_content(elt) or ''
                DOM.set_text_content(elt, "%s%s" % (elt_text, child))

    @staticmethod
    def set_attribute(elt, attr, value):
        elt.set(attr, value)

    @staticmethod
    def get_tag_name(elt):
        return elt.tag

    @staticmethod
    def get_class_list(elt):
        class_name = elt.get('class')
        return re.split('\ +', class_name) if class_name else []

    @staticmethod
    def get_text_content(elt):
        return ''.join(elt.itertext())

    @staticmethod
    def set_text_content(elt, text):
        try:
            elt.text = text
        except ValueError:
            elt.text = clean_str(text)

    @staticmethod
    def get_children(elt):
        return elt.getchildren()

    @staticmethod
    def render(elt):
        """
        Removes the fragments that should not have HTML tags. Caveat of lxml.
        Dirty, but quite easy to understand.
        """
        return re.sub(r'</?(fragment|textnode)>', '',
                      etree.tostring(elt, method='html').decode('utf-8'))

    @staticmethod
    def pretty_print(markup):
        """
        Convenience method.
        Pretty print the element, removing the top-level node that lxml needs.
        """
        return re.sub(r'</?doc>', '',
                      etree.tostring(
                          html.fromstring('<doc>%s</doc>' % markup),
                          encoding='unicode',
                          pretty_print=True))
