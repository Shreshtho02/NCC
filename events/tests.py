from django.test import TestCase
from django.urls import reverse
from django.apps import apps
import json

from .models import Eligibility, Event, EventSeg, Participant


class EventDetailTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name='Test Carnival',
            slug='test-carnival',
            banner='banners/test.png',
            description='A test event.',
            date='2026-09-11',
        )
        eligibility = Eligibility.objects.create(
            event=self.event,
            name='Everyone',
            start='c01',
            end='c13',
        )
        EventSeg.objects.create(
            event=self.event,
            eligibility=eligibility,
            name='Art',
            format='offline',
            fee=150,
            subcategories='Sketching',
        )
        EventSeg.objects.create(
            event=self.event,
            eligibility=eligibility,
            name='Photography',
            format='online',
            fee=200,
            subcategories='Mobile, DSLR',
        )
        EventSeg.objects.create(
            event=self.event,
            eligibility=eligibility,
            name='Group Dance',
            format='offline',
            fee=400,
            is_group=True,
            team_size=5,
            group_label='Cultural Fusion',
        )

    def test_detail_renders_ticket_cards_for_every_segment_category(self):
        response = self.client.get(reverse('event_detail', args=[self.event.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<article class="ticket-card"', count=3)
        self.assertContains(response, 'Offline')
        self.assertContains(response, 'Online')
        self.assertContains(response, '৳150')
        self.assertContains(response, 'ticket-card__tag')
        self.assertContains(response, 'Mobile')
        self.assertContains(response, 'DSLR')
        self.assertContains(response, 'Team of 5 · Cultural Fusion')

    def test_campus_ambassador_urls_and_models_are_removed(self):
        self.assertEqual(self.client.get(f'/events/{self.event.slug}/ca_reg/').status_code, 404)
        self.assertEqual(
            self.client.get(f'/events/{self.event.slug}/ca_reg/success/unused-token/').status_code,
            404,
        )
        with self.assertRaises(LookupError):
            apps.get_model('events', 'CABatch')
        with self.assertRaises(LookupError):
            apps.get_model('events', 'CampusAmbassador')

    def test_registration_uses_segment_cards_after_institution_and_persists_options(self):
        art = EventSeg.objects.get(event=self.event, name='Art')
        response = self.client.get(reverse('event_register', args=[self.event.slug]))
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('segment-choice', content)
        self.assertIn('segment-card-data', content)
        self.assertLess(content.index('name="institution"'), content.index('segment-selector'))

        response = self.client.post(
            reverse('event_register', args=[self.event.slug]),
            {
                'segment': [art.pk],
                'segment_selections': json.dumps({str(art.pk): 'Sketching'}),
                'name': 'Test Participant',
                'email': 'participant@example.com',
                'phone': '01700000000',
                'institution': 'Test College',
                'trxid': 'test-transaction-id',
                'paymeth': 'bkash',
                'paynum': '01700000000',
            },
        )

        self.assertEqual(response.status_code, 302)
        registration = Participant.objects.get(trxid='test-transaction-id')
        self.assertEqual(registration.selected_subcategories, {str(art.pk): 'Sketching'})
