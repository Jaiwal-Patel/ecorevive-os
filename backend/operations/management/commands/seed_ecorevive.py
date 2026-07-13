import os

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from impact.models import ImpactMetric
from operations.models import ItemCategory

CATEGORIES = [
    ("Computers & laptops", "Desktop computers, laptops, and related computing devices"),
    ("Monitors & televisions", "Computer displays, televisions, and screens"),
    ("Mobile devices", "Phones, tablets, smart watches, and accessories"),
    ("Printers & scanners", "Home and office printing equipment"),
    ("Networking equipment", "Routers, switches, access points, and modems"),
    ("Small household appliances", "Toasters, kettles, mixers, and similar devices"),
    ("Large household appliances", "Microwaves and larger electrical appliances"),
    ("Audio & entertainment", "Speakers, home theatre systems, and media devices"),
    ("Batteries", "Loose batteries and embedded battery devices"),
    ("Cables & accessories", "Chargers, keyboards, cables, and peripherals"),
    ("Other electronics", "Electronic items not covered by another category"),
]

METRICS = [
    ("ewaste_kg", "Electronic waste collected for responsible recycling", "kg", "IMPACT_EWASTE_KG", "2000"),
    ("paper_kg", "Paper waste recycled", "kg", "IMPACT_PAPER_KG", "358"),
    ("plastic_glass_kg", "Plastic and glass waste recycled", "kg", "IMPACT_PLASTIC_GLASS_KG", "97"),
    ("households", "Participating households", "households", "IMPACT_HOUSEHOLDS", "150"),
    ("collections", "Completed collections", "collections", "IMPACT_COLLECTIONS", "250"),
]


class Command(BaseCommand):
    help = "Seed item categories and configurable impact metrics."

    def handle(self, *args, **options):
        for name, description in CATEGORIES:
            ItemCategory.objects.update_or_create(
                slug=slugify(name),
                defaults={"name": name, "description": description, "active": True},
            )
        for key, label, unit, env_name, default in METRICS:
            ImpactMetric.objects.get_or_create(
                key=key,
                defaults={
                    "label": label,
                    "unit": unit,
                    "value": os.getenv(env_name, default),
                    "public": True,
                    "source_note": "Initial configurable EcoRevive public metric",
                },
            )
        self.stdout.write(self.style.SUCCESS("EcoRevive seed data is ready."))
