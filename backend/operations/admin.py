from django.contrib import admin

from .models import (
    CollectionItem,
    CollectionRequest,
    HandoverBatch,
    HandoverRequest,
    ItemCategory,
    PickupAssignment,
    StatusTransition,
    VolunteerProfile,
)

admin.site.register(ItemCategory)
admin.site.register(CollectionRequest)
admin.site.register(CollectionItem)
admin.site.register(VolunteerProfile)
admin.site.register(PickupAssignment)
admin.site.register(StatusTransition)
admin.site.register(HandoverBatch)
admin.site.register(HandoverRequest)
