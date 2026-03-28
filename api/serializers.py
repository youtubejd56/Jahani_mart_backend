from rest_framework import serializers
from .models import Category, Product, ProductImage, CartItem, Address, Order, OrderItem, Wallet, WalletTransaction, Review, Wishlist, SupportTicket, TicketReply, FAQ, StorySection, BlogPost, ProductReturn, ProductCancellation, WholesaleApplication


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
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'quantity', 'price']
    
    def get_product_image(self, obj):
        try:
            if obj.product.image:
                return obj.product.image.url
        except Exception:
            pass
        return obj.product.image_url or None


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
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'image', 'image_url']
        
    def get_image_url(self, obj):
        try:
            if obj.image:
                return obj.image.url
        except Exception:
            pass
        return obj.image_url or None

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url']
        
    def get_image_url(self, obj):
        try:
            if obj.image:
                return obj.image.url
        except Exception:
            pass
        return obj.image_url or None


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    discount = serializers.IntegerField(source='discount_percentage', read_only=True)
    image_url = serializers.SerializerMethodField()
    additional_images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'original_price', 
            'discount', 'rating', 'category', 'category_name', 
            'image', 'image_url', 'additional_images',
            'specifications', 'warranty', 'manufacturer', 'in_the_box',
            'stock', 'is_active', 'created_at'
        ]
    
    def get_image_url(self, obj):
        try:
            if obj.image:
                return obj.image.url
        except Exception:
            pass
        return obj.image_url or None


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
        try:
            if obj.product.image:
                return obj.product.image.url
        except Exception:
            pass
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
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_price', 'product_image', 'quantity', 'created_at']
    
    def get_product_image(self, obj):
        try:
            if obj.product.image:
                return obj.product.image.url
        except Exception:
            pass
        return obj.product.image_url or None


class TicketReplySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = TicketReply
        fields = ['id', 'user', 'user_name', 'message', 'is_admin_reply', 'created_at']
        read_only_fields = ['user', 'is_admin_reply', 'created_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['order_id', 'status', 'total_amount', 'payment_method', 
                  'shipping_name', 'shipping_phone', 'shipping_address', 
                  'shipping_city', 'shipping_state', 'shipping_pincode', 'items']
    
    def get_items(self, obj):
        items = obj.items.all()
        return [{'product_name': item.product.name, 'quantity': item.quantity, 'price': str(item.price)} for item in items]


class SupportTicketSerializer(serializers.ModelSerializer):
    replies = TicketReplySerializer(many=True, read_only=True)
    order_id = serializers.CharField(source='order.order_id', read_only=True)
    order_details = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_id', 'ticket_type', 'subject', 'description', 
            'order', 'order_id', 'order_details', 'priority', 'status', 'replies',
            'user_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'ticket_id', 'status', 'created_at', 'updated_at']
    
    def get_order_details(self, obj):
        if obj.order:
            return OrderDetailSerializer(obj.order).data
        return None


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'category', 'order', 'is_active', 'created_at']


class StorySectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorySection
        fields = ['id', 'title', 'description', 'image_url', 'order', 'is_reversed', 'created_at', 'updated_at']


class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'excerpt', 'content', 'category', 'image_url', 'date', 'is_published', 'created_at', 'updated_at']


class ProductReturnSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='order_item.product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    order_id = serializers.CharField(source='order.order_id', read_only=True)
    quantity = serializers.IntegerField(source='order_item.quantity', read_only=True)
    item_price = serializers.DecimalField(source='order_item.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ProductReturn
        fields = [
            'id', 'return_id', 'order', 'order_id', 'order_item', 'product_name', 'product_image',
            'quantity', 'item_price', 'reason', 'description', 'status', 'refund_amount',
            'refund_method', 'pickup_date', 'pickup_address', 'admin_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'return_id', 'status', 'refund_amount', 'admin_notes', 'created_at', 'updated_at']
    
    def get_product_image(self, obj):
        try:
            if obj.order_item.product.image:
                return obj.order_item.product.image.url
        except Exception:
            pass
        return obj.order_item.product.image_url or None


class ProductCancellationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='order_item.product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    order_id = serializers.CharField(source='order.order_id', read_only=True)
    quantity = serializers.IntegerField(source='order_item.quantity', read_only=True)
    item_price = serializers.DecimalField(source='order_item.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ProductCancellation
        fields = [
            'id', 'cancellation_id', 'order', 'order_id', 'order_item', 'product_name', 'product_image',
            'quantity', 'item_price', 'reason', 'description', 'status', 'refund_amount',
            'refund_method', 'admin_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'cancellation_id', 'status', 'refund_amount', 'admin_notes', 'created_at', 'updated_at']
    
    def get_product_image(self, obj):
        try:
            if obj.order_item.product.image:
                return obj.order_item.product.image.url
        except Exception:
            pass
        return obj.order_item.product.image_url or None


class ProductReturnAdminSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='order_item.product.name', read_only=True)
    order_id = serializers.CharField(source='order.order_id', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    quantity = serializers.IntegerField(source='order_item.quantity', read_only=True)
    item_price = serializers.DecimalField(source='order_item.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ProductReturn
        fields = [
            'id', 'return_id', 'order', 'order_id', 'order_item', 'product_name',
            'user', 'user_name', 'user_email', 'customer_name', 'customer_email',
            'quantity', 'item_price', 'reason', 'description', 'status', 'refund_amount',
            'refund_method', 'pickup_date', 'pickup_address', 'admin_notes', 'created_at', 'updated_at'
        ]
    
    def get_customer_name(self, obj):
        if obj.user:
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else obj.user.username
        return None
    
    def get_customer_email(self, obj):
        return obj.user.email if obj.user else None


class ProductCancellationAdminSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='order_item.product.name', read_only=True)
    order_id = serializers.CharField(source='order.order_id', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    quantity = serializers.IntegerField(source='order_item.quantity', read_only=True)
    item_price = serializers.DecimalField(source='order_item.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ProductCancellation
        fields = [
            'id', 'cancellation_id', 'order', 'order_id', 'order_item', 'product_name',
            'user', 'user_name', 'user_email', 'customer_name', 'customer_email',
            'quantity', 'item_price', 'reason', 'description', 'status', 'refund_amount',
            'refund_method', 'admin_notes', 'created_at', 'updated_at'
        ]
    
    def get_customer_name(self, obj):
        if obj.user:
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else obj.user.username
        return None
    
    def get_customer_email(self, obj):
        return obj.user.email if obj.user else None

class WholesaleApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholesaleApplication
        fields = '__all__'
        read_only_fields = ['status', 'created_at', 'updated_at']
