import unittest

from django.template import Context, Template  # TemplateSyntaxError

from mock import Mock, sentinel

from exam.decorators import fixture, around
from exam.cases import Exam

from chimera.client.models import Switch
import chimera.client.singleton


class TempateTagTest(Exam, unittest.TestCase):

    @around
    def maintain_manager_state(self):
        self.chimera.register(self.switch)
        yield
        self.chimera.flush()

    @around
    def patch_singleton(self):
        old_active = self.chimera.active
        self.chimera.active = Mock(return_value=False)
        yield
        self.chimera.active = old_active

    @property
    def chimera(self):
        return chimera.client.singleton.chimera

    @fixture
    def switch(self):
        return Switch('test', state=Switch.states.GLOBAL)

    @fixture
    def ifswitch(self):
        return Template(
            """
            {% load chimera %}
            {% ifswitch test %}
            switch active!
            {% endifswitch %}
            """
        )

    @fixture
    def ifswitch_with_else(self):
        return Template(
            """
            {% load chimera %}
            {% ifswitch test %}
            switch active!
            {% else %}
            switch not active!
            {% endifswitch %}
            """
        )

    @fixture
    def ifswitch_with_input(self):
        return Template(
            """
            {% load chimera %}
            {% ifswitch test input %}
            switch active!
            {% endifswitch %}
            """
        )

    def render(self, template):
        return template.render(Context({'input': sentinel.input}))

    def assertContentInTemplate(self, content, template):
        rendered = self.render(template)
        self.assertIn(content, rendered)

    def assertContentNotInTemplate(self, content, template):
        rendered = self.render(template)
        self.assertNotIn(content, rendered)

    def test_renders_content_inside_if_enabled_switch(self):
        self.assertContentNotInTemplate('switch active', self.ifswitch)
        self.chimera.active.return_value = True
        self.assertContentInTemplate('switch active', self.ifswitch)

    def test_works_with_else_switch(self):
        self.assertContentInTemplate(
            'switch not active',
            self.ifswitch_with_else
        )
        self.chimera.active.return_value = True
        self.assertContentInTemplate(
            'switch active',
            self.ifswitch_with_else
        )

    def test_calls_chimera_active_for_inputs_passed_in(self):
        self.render(self.ifswitch_with_input)
        self.chimera.active.assert_called_once_with('test', sentinel.input)

