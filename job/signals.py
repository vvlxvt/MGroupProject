from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .context_processors import MENU_CATEGORIES_CACHE_KEY
from .models import Category


def invalidate_menu_categories_cache():
    cache.delete(MENU_CATEGORIES_CACHE_KEY)


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def schedule_menu_cache_invalidation(**kwargs):
    transaction.on_commit(invalidate_menu_categories_cache)
