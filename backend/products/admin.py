from django.contrib import admin

from .models import Product, ProductQuestion, Review


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'stock', 'is_available', 'is_new', 'created_at')
    list_filter = ('category', 'is_available', 'is_new', 'created_at')
    search_fields = ('name', 'category__name', 'description')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'product__name', 'comment')
    raw_id_fields = ('user', 'product')


@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'asker_name', 'is_answered', 'answered_by', 'created_at')
    list_filter = ('created_at', 'answered_at')
    search_fields = ('product__name', 'asker_name', 'question', 'answer_text')
    raw_id_fields = ('product', 'user', 'answered_by')
