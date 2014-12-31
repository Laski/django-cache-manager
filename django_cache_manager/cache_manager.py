# -*- coding: utf-8 -*-
import logging

from django.db import models
from django.db.models.query import QuerySet

from .mixins import (
    CacheBackendMixin,
    CacheInvalidateMixin,
    CacheKeyMixin,
)

logger = logging.getLogger(__name__)


class CacheManager(models.Manager, CacheInvalidateMixin):

    # Use this manager when accessing objects that are related to from some other model.
    # Works only for one-to-one relationships not for many-to-many or foreign keys. See https://code.djangoproject.com/ticket/14891
    # so post_save, post_delete signals are used for cache invalidation. Signals can be removed when this bug is fixed.
    use_for_related_fields = True

    def get_query_set(self):
        return CachingQuerySet(self.model, using=self._db)


class CachingQuerySet(QuerySet, CacheBackendMixin, CacheKeyMixin, CacheInvalidateMixin):

    def iterator(self):
        key = self.generate_key()
        result_set = self.cache_backend.get(key)
        if not result_set:
            logger.debug('cache miss for key {0}'.format(key))
            result_set = list(super(CachingQuerySet, self).iterator())
            self.cache_backend.set(key, result_set)
        for result in result_set:
            yield result

    def bulk_create(self, *args, **kwargs):
        self.invalidate_model_cache()
        return super(CachingQuerySet, self).bulk_create(*args, **kwargs)

    def update(self, **kwargs):
        self.invalidate_model_cache()
        return super(CachingQuerySet, self).update(**kwargs)