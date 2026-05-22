from django.contrib import admin
from .models import Order, OrderItem, PincodeRule, ShippingZone


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'unit_price', 'quantity', 'line_total')


class PincodeRuleInline(admin.TabularInline):
    model = PincodeRule
    extra = 1


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'is_serviceable',
        'min_delivery_days',
        'max_delivery_days',
        'region_digit',
        'is_default_region',
    )
    list_filter = ('is_serviceable', 'is_default_region')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PincodeRuleInline]


@admin.register(PincodeRule)
class PincodeRuleAdmin(admin.ModelAdmin):
    list_display = ('value', 'rule_type', 'zone', 'priority')
    list_filter = ('rule_type', 'zone')
    search_fields = ('value', 'zone__name')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact_email', 'payment_method', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('contact_email', 'contact_phone', 'shipping_pincode')
    inlines = [OrderItemInline]
