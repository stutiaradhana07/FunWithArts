from django.contrib import admin
from .models import UserProfile, WishlistItem


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ('product', 'added_at')
    # WishlistItem is linked to User via UserProfile.user (OneToOne),
    # so we use the raw FK: user__profile is not a direct FK.
    # The inline is placed on WishlistItemAdmin only; profile shows count separately.


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'state', 'pincode')
    search_fields = ('user__username', 'user__email', 'phone', 'city', 'pincode')
    list_filter = ('state',)

    def wishlist_count(self, obj):
        return WishlistItem.objects.filter(user=obj.user).count()
    wishlist_count.short_description = 'Wishlist Items'
    readonly_fields = ('wishlist_count',)


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'product__name')
