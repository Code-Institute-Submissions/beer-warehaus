from django.contrib import admin
from .models import Product, Producer, Style, Category


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'sku',
        'producer',
        'name',
        'volume',
    )

    ordering = ('sku',)


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'friendly_name',
    )

    ordering = ('friendly_name',)


class StyleAdmin(admin.ModelAdmin):
    list_display = (
        'friendly_name',
        'category',
    )

    ordering = ('category', 'name')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Style, StyleAdmin)
admin.site.register(Producer)
admin.site.register(Product, ProductAdmin)
