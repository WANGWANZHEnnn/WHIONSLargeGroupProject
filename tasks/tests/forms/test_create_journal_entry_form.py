"""Unit tests of the create journal entry form"""
from django.test import TestCase
from tasks.models import User, JournalEntry
from tasks.forms import JournalEntryForm
from datetime import datetime

class CreateJournalEntryFormTestCase(TestCase):
    """Unit tests of the create journal entry form"""
    
    fixtures = ['tasks/tests/fixtures/default_user.json']

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.form_input = {
            "title": "New entry", 
            "text": "This is a new journal entry",
            "mood": 3
        }

    def test_form_has_necessary_fields(self):
        form = JournalEntryForm(user=self.user, data=self.form_input, text="template")
        self.assertIn('title', form.fields)
        self.assertIn('text', form.fields)

    def test_valid_form(self):
        form = JournalEntryForm(user=self.user, data=self.form_input, text="template")
        self.assertTrue(form.is_valid())

    def test_title_cannot_be_blank(self):
        self.form_input['title'] = ''
        form = JournalEntryForm(user=self.user, data=self.form_input, text="template")
        self.assertFalse(form.is_valid())

    def test_text_cannot_be_blank(self):
        self.form_input['text'] = ''
        form = JournalEntryForm(user=self.user, data=self.form_input, text="template")
        self.assertFalse(form.is_valid())

    def test_form_must_save_correctly(self):
        form = JournalEntryForm(user=self.user, data=self.form_input, text="template")
        before_count = JournalEntry.objects.count()
        form.save()
        after_count = JournalEntry.objects.count()
        self.assertEqual(before_count + 1, after_count)
        entry = JournalEntry.objects.get(title='New entry')
        self.assertTrue(entry.text == 'This is a new journal entry')