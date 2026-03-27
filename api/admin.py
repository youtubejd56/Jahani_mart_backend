from django.contrib import admin
from .models import Category, Product, Review, Wishlist, ProductReturn, ProductCancellation

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'icon']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'category', 'stock', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock', 'is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('price', 'original_price', 'discount')
        }),
        ('Media', {
            'fields': ('image', 'image_url')
        }),
        ('Inventory', {
            'fields': ('stock', 'is_active')
        }),
        ('Additional', {
            'fields': ('rating',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('rating', 'created_at', 'updated_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'user', 'rating', 'title', 'is_verified_purchase', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__username', 'title', 'comment']
    readonly_fields = ('user', 'product', 'is_verified_purchase', 'helpful_count', 'created_at', 'updated_at')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ('user', 'product', 'created_at')


@admin.register(ProductReturn)
class ProductReturnAdmin(admin.ModelAdmin):
    list_display = ['return_id', 'user', 'order', 'product_name', 'reason', 'status', 'refund_amount', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['return_id', 'user__username', 'order__order_id', 'order_item__product__name']
    readonly_fields = ['user', 'order', 'order_item', 'return_id', 'refund_amount', 'created_at', 'updated_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Return Information', {
            'fields': ('return_id', 'user', 'order', 'order_item', 'reason', 'description')
        }),
        ('Status & Refund', {
            'fields': ('status', 'refund_amount', 'refund_method')
        }),
        ('Pickup Details', {
            'fields': ('pickup_date', 'pickup_address')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',)
        }),
    )
    
    def product_name(self, obj):
        return obj.order_item.product.name
    product_name.short_description = 'Product'


@admin.register(ProductCancellation)
class ProductCancellationAdmin(admin.ModelAdmin):
    list_display = ['cancellation_id', 'user', 'order', 'product_name', 'reason', 'status', 'refund_amount', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['cancellation_id', 'user__username', 'order__order_id', 'order_item__product__name']
    readonly_fields = ['user', 'order', 'order_item', 'cancellation_id', 'refund_amount', 'created_at', 'updated_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Cancellation Information', {
            'fields': ('cancellation_id', 'user', 'order', 'order_item', 'reason', 'description')
        }),
        ('Status & Refund', {
            'fields': ('status', 'refund_amount', 'refund_method')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',)
        }),
    )
    
    def product_name(self, obj):
        return obj.order_item.product.name
    product_name.short_description = 'Product'
