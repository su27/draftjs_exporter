from __future__ import absolute_import, unicode_literals

from draftjs_exporter.dom import DOM
from draftjs_exporter.error import ExporterException


class EntityException(ExporterException):
    pass


class EntityState:
    def __init__(self, entity_decorators, entity_map):
        self.entity_decorators = entity_decorators
        self.entity_map = entity_map

        self.entity_stack = []

    def apply(self, command):
        if command.name == 'start_entity':
            self.start_command(command)
        elif command.name == 'stop_entity':
            self.stop_command(command)

    def get_entity_details(self, command):
        key = str(command.data)
        details = self.entity_map.get(key)

        if details is None:
            raise EntityException('Entity "%s" does not exist in the entityMap' % key)

        return details

    def get_entity_decorator(self, entity_details):
        type_ = entity_details.get('type')
        decorator = self.entity_decorators.get(type_)

        if decorator is None:
            raise EntityException('Decorator "%s" does not exist in entity_decorators' % type_)

        return decorator

    def start_command(self, command):
        entity_details = self.get_entity_details(command)
        self.entity_stack.append(entity_details)

    def stop_command(self, command):
        entity_details = self.get_entity_details(command)
        expected_entity_details = self.entity_stack[-1]

        if expected_entity_details != entity_details:
            raise EntityException('Expected {0}, got {1}'.format(expected_entity_details, entity_details))

        self.entity_stack.pop()

    def render_entitities(self, root_element, style_nodes):
        element_stack = []

        if len(self.entity_stack) == 0:
            for node in style_nodes:
                DOM.append_child(root_element, node)
            return root_element

        else:
            for entity_details in self.entity_stack:
                decorator = self.get_entity_decorator(entity_details)

                entity_details['children'] = style_nodes

                new_element = decorator.render(entity_details)
                if not element_stack:
                    DOM.append_child(root_element, new_element)
                    element_stack = [new_element]
                else:
                    DOM.append_child(element_stack[-1], new_element)
                element_stack.append(new_element)

            return new_element
