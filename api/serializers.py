from rest_framework import serializers
from .models import Category, Product, CartItem, Address, Order, OrderItem, Wallet, WalletTransaction, Review, Wishlist, SupportTicket, TicketReply, FAQ


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'transaction_type', 'amount', 'description', 'created_at']


class WalletSerializer(serializers.ModelSerializer):
    transactions = WalletTransactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'transactions', 'created_at', 'updated_at']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'name', 'phone', 'address', 'city', 'state', 'pincode', 'address_type', 'is_default', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.URLField(source='product.image', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_id', 'status', 'payment_method', 'payment_status', 
                  'card_last_four', 'upi_id', 'total_amount', 
                  'shipping_name', 'shipping_phone', 'shipping_address', 
                  'shipping_city', 'shipping_state', 'shipping_pincode', 
                  'items', 'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'image']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    discount = serializers.IntegerField(source='discount_percentage', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'original_price', 
            'discount', 'rating', 'category', 'category_name', 
            'image', 'image_url', 'stock', 'is_active', 'created_at'
        ]
    
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        elif obj.image_url:
            return obj.image_url
        return None


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'product', 'product_name', 'user', 'user_name', 'user_username',
            'rating', 'title', 'comment', 'is_verified_purchase',
            'helpful_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'is_verified_purchase', 'helpful_count', 'created_at', 'updated_at']


class WishlistSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.SerializerMethodField()
    product_original_price = serializers.DecimalField(source='product.original_price', max_digits=10, decimal_places=2, read_only=True)
    product_discount = serializers.IntegerField(source='product.discount', read_only=True)
    product_stock = serializers.IntegerField(source='product.stock', read_only=True)
    
    def get_product_image(self, obj):
        # Return image URL or external URL
        if obj.product.image:
            return obj.product.image.url
        return obj.product.image_url or None
    
    class Meta:
        model = Wishlist
        fields = [
            'id', 'product', 'product_name', 'product_price', 'product_image',
            'product_original_price', 'product_discount', 'product_stock', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.URLField(source='product.image', read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_price', 'product_image', 'quantity', 'created_at']


class TicketReplySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = TicketReply
        fields = ['id', 'user', 'user_name', 'message', 'is_admin_reply', 'created_at']
        read_only_fields = ['user', 'is_admin_reply', 'created_at']


class SupportTicketSerializer(serializers.ModelSerializer):
    replies = TicketReplySerializer(many=True, read_only=True)
    order_id = serializers.CharField(source='order.order_id', read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_id', 'ticket_type', 'subject', 'description', 
            'order', 'order_id', 'priority', 'status', 'replies', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'ticket_id', 'status', 'created_at', 'updated_at']


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'category', 'order', 'is_active', 'created_at']
