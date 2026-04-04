from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.utils import timezone
from django.db import models
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Category, Product, Profile, CartItem, Address, Order, OrderItem, Wallet, WalletTransaction, Review, Wishlist, SupportTicket, TicketReply, FAQ, StorySection, BlogPost, OTPVerification, ProductReturn, ProductCancellation, WholesaleApplication
from .serializers import CategorySerializer, ProductSerializer, CartItemSerializer, AddressSerializer, OrderSerializer, WalletSerializer, ReviewSerializer, WishlistSerializer, SupportTicketSerializer, TicketReplySerializer, FAQSerializer, StorySectionSerializer, BlogPostSerializer, ProductReturnSerializer, ProductCancellationSerializer, ProductReturnAdminSerializer, ProductCancellationAdminSerializer, WholesaleApplicationSerializer
import random
import string
import secrets
import os
import json
from urllib import parse, request as urllib_request, error as urllib_error
from datetime import timedelta
from .views_support import support_tickets, support_ticket_detail, ticket_reply, faq_list, create_support_ticket, admin_all_tickets, admin_ticket_detail, admin_ticket_reply, admin_update_ticket_status


def normalize_mobile_for_msg91(mobile):
    """MSG91 expects digits-only international format, e.g. 919876543210."""
    return ''.join(ch for ch in mobile if ch.isdigit())


def send_msg91_password_reset_otp(mobile, otp):
    """
    Send forgot-password OTP via MSG91.
    Returns (success, error_message).
    """
    api_key = os.environ.get('MSG91_API_KEY', '').strip()
    if not api_key:
        return False, 'MSG91 API key is not configured.'

    recipient_mobile = normalize_mobile_for_msg91(mobile)
    if not recipient_mobile:
        return False, 'Invalid mobile number for SMS delivery.'

    sender_id = os.environ.get('MSG91_SENDER_ID', '').strip()
    route = os.environ.get('MSG91_ROUTE', '4').strip() or '4'
    message_template = os.environ.get(
        'MSG91_OTP_MESSAGE',
        'Your Jahani International password reset OTP is {otp}. It is valid for 10 minutes.'
    )
    message = message_template.format(otp=otp)

    payload = {
        'authkey': api_key,
        'mobiles': recipient_mobile,
        'message': message,
        'route': route,
    }
    if sender_id:
        payload['sender'] = sender_id

    encoded_payload = parse.urlencode(payload).encode('utf-8')
    req = urllib_request.Request(
        'https://api.msg91.com/api/sendhttp.php',
        data=encoded_payload,
        method='POST',
    )

    try:
        with urllib_request.urlopen(req, timeout=10) as response:
            raw_body = response.read().decode('utf-8', errors='replace').strip()
    except urllib_error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='replace').strip()
        return False, f'MSG91 HTTP {exc.code}: {error_body or "Unknown error"}'
    except urllib_error.URLError as exc:
        return False, f'Unable to reach MSG91: {exc.reason}'
    except Exception as exc:
        return False, f'Unexpected SMS error: {str(exc)}'

    if not raw_body:
        return False, 'MSG91 returned an empty response.'

    if raw_body.upper() == 'OK':
        return True, ''

    try:
        parsed_body = json.loads(raw_body)
    except json.JSONDecodeError:
        parsed_body = None

    if isinstance(parsed_body, dict):
        response_type = str(parsed_body.get('type', '')).lower()
        if response_type == 'success':
            return True, ''

        error_message = (
            parsed_body.get('message')
            or parsed_body.get('error')
            or parsed_body.get('description')
            or raw_body
        )
        return False, f'MSG91 rejected the SMS request: {error_message}'

    return False, f'MSG91 rejected the SMS request: {raw_body}'

def home(request):
    return JsonResponse({'message': 'Welcome to Jahani International API'})

@api_view(['GET'])
def product_list(request):
    try:
        products = Product.objects.filter(is_active=True)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(f"Error in product_list: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk, is_active=True)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def suggested_products(request, pk):
    try:
        product = Product.objects.get(pk=pk, is_active=True)
        suggested_ids = []
        
        # 1. Market Basket Analysis (Collaborative Filtering)
        # Find exactly what other customers bought in the same orders as this product
        co_orders = OrderItem.objects.filter(product=product).values_list('order', flat=True)
        co_products = OrderItem.objects.filter(order__in=co_orders)\
            .exclude(product=product)\
            .values('product')\
            .annotate(purchase_count=models.Count('product'))\
            .order_by('-purchase_count')[:4]
            
        suggested_ids.extend([item['product'] for item in co_products])
        
        # 2. Content-Based Filtering (Category + Best Rated)
        if len(suggested_ids) < 4:
            needed = 4 - len(suggested_ids)
            category_match = Product.objects.filter(
                category=product.category, 
                is_active=True
            ).exclude(pk=pk).exclude(pk__in=suggested_ids).order_by('-rating')[:needed]
            suggested_ids.extend([p.pk for p in category_match])
            
        # 3. Fallback: Global Trending (Highest Rated Items overall)
        if len(suggested_ids) < 4:
            needed = 4 - len(suggested_ids)
            global_popular = Product.objects.filter(is_active=True)\
                .exclude(pk=pk).exclude(pk__in=suggested_ids).order_by('-rating')[:needed]
            suggested_ids.extend([p.pk for p in global_popular])
            
        # Fetch the objects in the exact algorithmic order calculated above
        suggested = []
        for sid in suggested_ids:
            try:
                suggested.append(Product.objects.get(pk=sid))
            except Product.DoesNotExist:
                pass
                
        serializer = ProductSerializer(suggested, many=True)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def category_list(request):
    try:
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(f"Error in category_list: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def products_by_category(request, category_id):
    try:
        category = Category.objects.get(pk=category_id)
        products = Product.objects.filter(category=category, is_active=True)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

# Admin views
from rest_framework_simplejwt.tokens import RefreshToken

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user is not None and user.is_staff:
        login(request, user)
        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Admin login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name
            },
            'token': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        })
    else:
        return Response({'error': 'Invalid credentials or not an admin'}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    print(f"Admin dashboard - User: {request.user}, Auth: {request.auth}, Is staff: {request.user.is_staff if request.user.is_authenticated else 'N/A'}")
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get all orders with user details
    orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')
    
    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'order_id': order.order_id,
            'status': order.status,
            'payment_method': order.payment_method,
            'total_amount': float(order.total_amount),
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
            'customer': {
                'id': order.user.id,
                'name': f"{order.user.first_name} {order.user.last_name}".strip() or order.user.username,
                'email': order.user.email,
                'username': order.user.username
            },
            'shipping': {
                'name': order.shipping_name,
                'phone': order.shipping_phone,
                'address': order.shipping_address,
                'city': order.shipping_city,
                'state': order.shipping_state,
                'pincode': order.shipping_pincode
            },
            'items_count': order.items.count(),
            'items': [{
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': float(item.price)
            } for item in order.items.all()]
        })
    
    # Stats
    total_orders = orders.count()
    pending_orders = orders.filter(status='Pending').count()
    processing_orders = orders.filter(status='Processing').count()
    shipped_orders = orders.filter(status='Shipped').count()
    delivered_orders = orders.filter(status='Delivered').count()
    total_revenue = sum(float(o.total_amount) for o in orders)
    
    return Response({
        'stats': {
            'total_orders': total_orders,
            'pending': pending_orders,
            'processing': processing_orders,
            'shipped': shipped_orders,
            'delivered': delivered_orders,
            'total_revenue': total_revenue
        },
        'orders': orders_data
    })


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    new_status = request.data.get('status')
    if new_status not in ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    order.status = new_status
    order.save()
    
    return Response({
        'message': 'Order status updated',
        'order': {
            'order_id': order.order_id,
            'status': order.status
        }
    })


@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_all_users(request):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    from django.contrib.auth.models import User
    users = User.objects.filter(is_staff=False).order_by('-date_joined')
    
    users_data = []
    for user in users:
        order_count = Order.objects.filter(user=user).count()
        addresses = Address.objects.filter(user=user)
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined.strftime('%Y-%m-%d'),
            'order_count': order_count,
            'addresses': [{
                'name': addr.name,
                'phone': addr.phone,
                'address': addr.address,
                'city': addr.city,
                'state': addr.state,
                'pincode': addr.pincode
            } for addr in addresses]
        })
    
    return Response(users_data)


# Admin Categories API
@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_categories(request):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_category_detail(request, category_id):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = CategorySerializer(category)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Admin Products API
@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_products(request):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        products = Product.objects.all().order_by('-created_at')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_product_detail(request, product_id):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Reviews API
@api_view(['GET'])
def product_reviews(request, product_id):
    """Get all reviews for a product"""
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    reviews = Review.objects.filter(product=product).select_related('user')
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def reviews(request):
    """Get all reviews or create a review"""
    if request.method == 'GET':
        reviews = Review.objects.all().select_related('user', 'product')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Check if user already reviewed this product
        product_id = request.data.get('product')
        existing_review = Review.objects.filter(
            user=request.user, 
            product_id=product_id
        ).first()
        
        if existing_review:
            return Response(
                {'error': 'You have already reviewed this product'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user purchased the product (for verified badge)
        has_purchased = Order.objects.filter(
            user=request.user,
            items__product_id=product_id,
            status='Delivered'
        ).exists()
        
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, is_verified_purchase=has_purchased)
            # Update product rating
            product = Product.objects.get(id=product_id)
            avg_rating = Review.objects.filter(product=product).aggregate(models.Avg('rating'))['rating__avg']
            product.rating = round(avg_rating, 1) if avg_rating else 0
            product.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def review_detail(request, review_id):
    """Get, update or delete a specific review"""
    try:
        review = Review.objects.get(id=review_id, user=request.user)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ReviewSerializer(review)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Update product rating
            product = review.product
            avg_rating = Review.objects.filter(product=product).aggregate(models.Avg('rating'))['rating__avg']
            product.rating = round(avg_rating, 1) if avg_rating else 0
            product.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        product = review.product
        review.delete()
        # Update product rating
        avg_rating = Review.objects.filter(product=product).aggregate(models.Avg('rating'))['rating__avg']
        product.rating = round(avg_rating, 1) if avg_rating else 0
        product.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Admin Reviews API
@csrf_exempt
@api_view(['GET', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_reviews(request):
    """Admin: Get all reviews or delete a review"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        reviews = Review.objects.all().select_related('user', 'product').order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


# Wishlist views
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def wishlist(request):
    """Get user's wishlist, add to wishlist, or remove from wishlist"""
    if request.method == 'GET':
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
        serializer = WishlistSerializer(wishlist_items, many=True)
        return Response(serializer.data)
    
    if request.method == 'POST':
        product_id = request.data.get('product')
        if not product_id:
            return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already in wishlist
        if Wishlist.objects.filter(user=request.user, product=product).exists():
            return Response({'message': 'Product already in wishlist'})
        
        wishlist_item = Wishlist.objects.create(user=request.user, product=product)
        serializer = WishlistSerializer(wishlist_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    if request.method == 'DELETE':
        product_id = request.data.get('product')
        if not product_id:
            return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            wishlist_item = Wishlist.objects.get(user=request.user, product_id=product_id)
            wishlist_item.delete()
            return Response({'message': 'Removed from wishlist'})
        except Wishlist.DoesNotExist:
            return Response({'error': 'Item not in wishlist'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_wishlist(request, product_id):
    """Toggle wishlist status for a product"""
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
    
    if wishlist_item:
        wishlist_item.delete()
        return Response({'in_wishlist': False, 'message': 'Removed from wishlist'})
    else:
        Wishlist.objects.create(user=request.user, product=product)
        return Response({'in_wishlist': True, 'message': 'Added to wishlist'})


# User registration
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    email = request.data.get('email', '')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    mobile = request.data.get('mobile', '')
    
    if not mobile or not password:
        return Response({'error': 'Mobile number and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate mobile (allow leading + then digits)
    clean_mobile = mobile.replace(' ', '').replace('-', '')
    is_valid_format = clean_mobile.isdigit() or (clean_mobile.startswith('+') and clean_mobile[1:].isdigit())
    
    if not is_valid_format or len(clean_mobile) < 7:
        return Response({'error': 'Enter a valid mobile number (e.g. +91 9999999999)'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if mobile already exists in Profile
    if Profile.objects.filter(mobile=clean_mobile).exists():
        return Response({'error': 'This mobile number is already registered. Please login instead.'}, status=status.HTTP_400_BAD_REQUEST)

    # Also check if username exists (since we use mobile as username)
    if User.objects.filter(username=clean_mobile).exists():
        return Response({'error': 'This number is already in use. Please login.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check email uniqueness
    if email and User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered. Please use a different email.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Use clean_mobile as username
    user = User.objects.create_user(
        username=clean_mobile,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    
    # Create user profile with mobile number
    Profile.objects.create(user=user, mobile=clean_mobile)
    
    return Response({
        'message': 'User registered successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'mobile': mobile
        }
    }, status=status.HTTP_201_CREATED)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Mobile number and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        login(request, user)
        mobile = ''
        if hasattr(user, 'profile'):
            mobile = user.profile.mobile
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'mobile': mobile
            }
        })
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    logout(request)
    return Response({'message': 'Logout successful'})



@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """Send OTP to registered mobile number for password reset"""
    mobile = request.data.get('mobile', '').strip()

    if not mobile:
        return Response({'error': 'Mobile number is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if mobile is registered
    if not Profile.objects.filter(mobile=mobile).exists():
        return Response({'error': 'No account found with this mobile number'}, status=status.HTTP_404_NOT_FOUND)

    # Delete old unverified OTPs for this mobile
    OTPVerification.objects.filter(mobile=mobile, is_verified=False).delete()

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    expires_at = timezone.now() + timedelta(minutes=10)

    OTPVerification.objects.create(
        mobile=mobile,
        otp=otp,
        expires_at=expires_at
    )

    sms_sent, sms_error = send_msg91_password_reset_otp(mobile, otp)

    response_data = {
        'message': 'OTP sent successfully' if sms_sent else 'OTP generated successfully',
        'expires_in': 600
    }

    if sms_sent:
        return Response(response_data)

    if settings.DEBUG:
        response_data.update({
            'message': 'MSG91 delivery failed, using debug OTP response.',
            'demo_otp': otp,
            'sms_error': sms_error,
        })
        return Response(response_data)

    OTPVerification.objects.filter(mobile=mobile, otp=otp, is_verified=False).delete()
    return Response(
        {'error': sms_error or 'Failed to send OTP. Please try again later.'},
        status=status.HTTP_503_SERVICE_UNAVAILABLE
    )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP and return a short-lived reset token"""
    mobile = request.data.get('mobile', '').strip()
    otp = request.data.get('otp', '').strip()

    if not mobile or not otp:
        return Response({'error': 'Mobile and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        otp_obj = OTPVerification.objects.filter(
            mobile=mobile,
            otp=otp,
            is_verified=False
        ).latest('created_at')

        if timezone.now() > otp_obj.expires_at:
            otp_obj.delete()
            return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark verified and generate reset token
        reset_token = secrets.token_urlsafe(32)
        otp_obj.is_verified = True
        otp_obj.reset_token = reset_token
        otp_obj.save()

        return Response({
            'message': 'OTP verified successfully',
            'reset_token': reset_token
        })

    except OTPVerification.DoesNotExist:
        return Response({'error': 'Invalid OTP. Please check and try again.'}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password using verified OTP reset token"""
    mobile = request.data.get('mobile', '').strip()
    new_password = request.data.get('new_password', '')
    reset_token = request.data.get('reset_token', '').strip()

    if not all([mobile, new_password, reset_token]):
        return Response({'error': 'Mobile, reset token, and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if len(new_password) < 6:
        return Response({'error': 'Password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)

    # Verify reset token
    try:
        otp_obj = OTPVerification.objects.get(
            mobile=mobile,
            reset_token=reset_token,
            is_verified=True
        )
        # Allow 30-min window after OTP expiry to complete reset
        if timezone.now() > otp_obj.expires_at + timedelta(minutes=30):
            otp_obj.delete()
            return Response({'error': 'Session expired. Please start again.'}, status=status.HTTP_400_BAD_REQUEST)

    except OTPVerification.DoesNotExist:
        return Response({'error': 'Invalid or expired session. Please verify OTP again.'}, status=status.HTTP_400_BAD_REQUEST)

    # Reset the password
    try:
        profile = Profile.objects.get(mobile=mobile)
        user = profile.user
        user.set_password(new_password)
        user.save()
        otp_obj.delete()  # Invalidate token after use
        return Response({'message': 'Password reset successfully'})
    except Profile.DoesNotExist:
        return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user
    mobile = ''
    if hasattr(user, 'profile'):
        mobile = user.profile.mobile
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'mobile': mobile
        }
    })


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cart(request):
    if request.method == 'GET':
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        serializer = CartItemSerializer(cart_items, many=True)
        total_items = sum(item.quantity for item in cart_items)
        total_price = sum(item.quantity * item.product.price for item in cart_items)
        return Response({
            'items': serializer.data,
            'total_items': total_items,
            'total_price': float(total_price)
        })
    
    elif request.method == 'POST':
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += int(quantity)
            cart_item.save()
        
        return Response({'message': 'Item added to cart', 'cart_item': CartItemSerializer(cart_item).data}, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        cart_item.delete()
        return Response({'message': 'Item removed from cart'})
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        quantity = request.data.get('quantity')
        
        if quantity and int(quantity) > 0:
            cart_item.quantity = int(quantity)
            cart_item.save()
            return Response({'message': 'Cart updated', 'cart_item': CartItemSerializer(cart_item).data})
        else:
            return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def address_list(request):
    if request.method == 'GET':
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if request.data.get('is_default', False) or not Address.objects.filter(user=request.user).exists():
            Address.objects.filter(user=request.user).update(is_default=False)
        
        address = Address.objects.create(
            user=request.user,
            name=request.data.get('name'),
            phone=request.data.get('phone'),
            address=request.data.get('address'),
            city=request.data.get('city'),
            state=request.data.get('state'),
            pincode=request.data.get('pincode'),
            address_type=request.data.get('address_type', 'Home'),
            is_default=request.data.get('is_default', False)
        )
        serializer = AddressSerializer(address)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def address_detail(request, address_id):
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = AddressSerializer(address)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if request.data.get('is_default'):
            Address.objects.filter(user=request.user).update(is_default=False)
        
        address.name = request.data.get('name', address.name)
        address.phone = request.data.get('phone', address.phone)
        address.address = request.data.get('address', address.address)
        address.city = request.data.get('city', address.city)
        address.state = request.data.get('state', address.state)
        address.pincode = request.data.get('pincode', address.pincode)
        address.address_type = request.data.get('address_type', address.address_type)
        address.is_default = request.data.get('is_default', address.is_default)
        address.save()
        serializer = AddressSerializer(address)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        address.delete()
        return Response({'message': 'Address deleted'})


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
        serializer = OrderSerializer(order)
        
        # Create tracking timeline based on order status
        timeline = []
        status_flow = ['Pending', 'Processing', 'Shipped', 'Delivered']
        
        # Add completed steps
        for status in status_flow:
            timeline.append({
                'status': status,
                'completed': status_flow.index(status) <= status_flow.index(order.status),
                'current': status == order.status,
                'date': order.updated_at.strftime('%Y-%m-%d') if status_flow.index(status) <= status_flow.index(order.status) else None
            })
        
        response_data = serializer.data
        response_data['timeline'] = timeline
        response_data['estimated_delivery'] = None
        
        return Response(response_data)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


import random
import string

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    
    if not cart_items.exists():
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    address_id = request.data.get('address_id')
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)
    
    order_id = 'ORD-' + ''.join(random.choices(string.digits, k=6))
    total_amount = sum(item.quantity * item.product.price for item in cart_items)
    
    payment_method = request.data.get('payment_method', 'COD')
    payment_status = 'Pending' if payment_method == 'COD' else 'Paid'  # For demo, assume paid for Card/UPI
    
    order = Order.objects.create(
        user=request.user,
        order_id=order_id,
        payment_method=payment_method,
        payment_status=payment_status,
        card_last_four=request.data.get('card_last_four'),
        upi_id=request.data.get('upi_id'),
        total_amount=total_amount,
        shipping_name=address.name,
        shipping_phone=address.phone,
        shipping_address=address.address,
        shipping_city=address.city,
        shipping_state=address.state,
        shipping_pincode=address.pincode
    )
    
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )
    
    cart_items.delete()
    
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_details(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    addresses = Address.objects.filter(user=user)
    order_count = Order.objects.filter(user=user).count()
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'mobile': profile.mobile
        },
        'addresses': AddressSerializer(addresses, many=True).data,
        'stats': {
            'orders': order_count,
            'addresses': addresses.count(),
            'wishlist': 0,
            'wallet': 0
        }
    })


@csrf_exempt
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    
    first_name = request.data.get('first_name', user.first_name)
    last_name = request.data.get('last_name', user.last_name)
    email = request.data.get('email', user.email)
    mobile = request.data.get('mobile', profile.mobile)
    
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.save()
    
    profile.mobile = mobile
    profile.save()
    
    return Response({
        'message': 'Profile updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'mobile': profile.mobile
        }
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    if not current_password or not new_password or not confirm_password:
        return Response({'error': 'All password fields are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not user.check_password(current_password):
        return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
    
    if new_password != confirm_password:
        return Response({'error': 'New passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(new_password) < 6:
        return Response({'error': 'Password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    user.save()
    
    return Response({'message': 'Password changed successfully'})


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wallet_details(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')[:10]
    serializer = WalletSerializer(wallet)
    return Response(serializer.data)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_money(request):
    amount = request.data.get('amount')
    
    if not amount:
        return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        amount = float(amount)
    except ValueError:
        return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)
    
    if amount <= 0:
        return Response({'error': 'Amount must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)
    
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    wallet.balance += amount
    wallet.save()
    
    # Create transaction record
    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type='Credit',
        amount=amount,
        description='Money added to wallet'
    )
    
    return Response({
        'message': 'Money added successfully',
        'balance': float(wallet.balance)
    })


# ─── Story Section API ───────────────────────────────────────────────
@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_story_sections(request):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        stories = StorySection.objects.all().order_by('order')
        serializer = StorySectionSerializer(stories, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = StorySectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_story_section_detail(request, section_id):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        story = StorySection.objects.get(id=section_id)
    except StorySection.DoesNotExist:
        return Response({'error': 'Story section not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(StorySectionSerializer(story).data)

    elif request.method == 'PUT':
        serializer = StorySectionSerializer(story, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        story.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Blog Post API ───────────────────────────────────────────────────
@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_blog_posts(request):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        posts = BlogPost.objects.all()
        serializer = BlogPostSerializer(posts, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = BlogPostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_blog_post_detail(request, post_id):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        post = BlogPost.objects.get(id=post_id)
    except BlogPost.DoesNotExist:
        return Response({'error': 'Blog post not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(BlogPostSerializer(post).data)

    elif request.method == 'PUT':
        serializer = BlogPostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Public Blog Posts API (for Blog.jsx page) ───────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def public_blog_posts(request):
    posts = BlogPost.objects.filter(is_published=True)
    serializer = BlogPostSerializer(posts, many=True)
    return Response(serializer.data)


# ─── Product Return API ───────────────────────────────────────────────
@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def product_returns(request):
    """Get user's returns or create a new return request"""
    if request.method == 'GET':
        returns = ProductReturn.objects.filter(user=request.user).select_related('order', 'order_item', 'order_item__product')
        serializer = ProductReturnSerializer(returns, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        order_item_id = request.data.get('order_item')
        reason = request.data.get('reason')
        description = request.data.get('description', '')
        
        if not order_item_id or not reason:
            return Response({'error': 'Order item and reason are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order_item = OrderItem.objects.get(id=order_item_id, order__user=request.user)
        except OrderItem.DoesNotExist:
            return Response({'error': 'Order item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if order is delivered
        if order_item.order.status != 'Delivered':
            return Response({'error': 'Returns can only be requested for delivered orders'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if return already exists for this item
        if ProductReturn.objects.filter(order_item=order_item).exists():
            return Response({'error': 'Return request already exists for this item'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate return ID
        return_id = 'RET' + ''.join(random.choices(string.digits, k=8))
        
        return_request = ProductReturn.objects.create(
            user=request.user,
            order=order_item.order,
            order_item=order_item,
            return_id=return_id,
            reason=reason,
            description=description,
            refund_amount=order_item.price * order_item.quantity
        )
        
        serializer = ProductReturnSerializer(return_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def product_return_detail(request, return_id):
    """Get details of a specific return request"""
    try:
        return_request = ProductReturn.objects.get(return_id=return_id, user=request.user)
        serializer = ProductReturnSerializer(return_request)
        return Response(serializer.data)
    except ProductReturn.DoesNotExist:
        return Response({'error': 'Return request not found'}, status=status.HTTP_404_NOT_FOUND)


# ─── Product Cancellation API ─────────────────────────────────────────
@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def product_cancellations(request):
    """Get user's cancellations or create a new cancellation request"""
    if request.method == 'GET':
        cancellations = ProductCancellation.objects.filter(user=request.user).select_related('order', 'order_item', 'order_item__product')
        serializer = ProductCancellationSerializer(cancellations, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        order_item_id = request.data.get('order_item')
        reason = request.data.get('reason')
        description = request.data.get('description', '')
        
        if not order_item_id or not reason:
            return Response({'error': 'Order item and reason are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order_item = OrderItem.objects.get(id=order_item_id, order__user=request.user)
        except OrderItem.DoesNotExist:
            return Response({'error': 'Order item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if order can be cancelled (not delivered or already cancelled)
        if order_item.order.status in ['Delivered', 'Cancelled']:
            return Response({'error': 'This order cannot be cancelled'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if cancellation already exists for this item
        if ProductCancellation.objects.filter(order_item=order_item).exists():
            return Response({'error': 'Cancellation request already exists for this item'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate cancellation ID
        cancellation_id = 'CAN' + ''.join(random.choices(string.digits, k=8))
        
        cancellation = ProductCancellation.objects.create(
            user=request.user,
            order=order_item.order,
            order_item=order_item,
            cancellation_id=cancellation_id,
            reason=reason,
            description=description,
            refund_amount=order_item.price * order_item.quantity
        )
        
        serializer = ProductCancellationSerializer(cancellation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def product_cancellation_detail(request, cancellation_id):
    """Get details of a specific cancellation request"""
    try:
        cancellation = ProductCancellation.objects.get(cancellation_id=cancellation_id, user=request.user)
        serializer = ProductCancellationSerializer(cancellation)
        return Response(serializer.data)
    except ProductCancellation.DoesNotExist:
        return Response({'error': 'Cancellation request not found'}, status=status.HTTP_404_NOT_FOUND)


# ─── Admin Return/Cancellation Management API ─────────────────────────
@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_all_returns(request):
    """Admin: Get all return requests"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    returns = ProductReturn.objects.all().select_related('user', 'order', 'order_item', 'order_item__product').order_by('-created_at')
    serializer = ProductReturnAdminSerializer(returns, many=True)
    return Response(serializer.data)


@csrf_exempt
@api_view(['GET', 'PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_return_detail(request, return_id):
    """Admin: Get or update a return request"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        return_request = ProductReturn.objects.get(id=return_id)
    except ProductReturn.DoesNotExist:
        return Response({'error': 'Return request not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ProductReturnAdminSerializer(return_request)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        status_val = request.data.get('status')
        admin_notes = request.data.get('admin_notes', '')
        pickup_date = request.data.get('pickup_date')
        pickup_address = request.data.get('pickup_address', '')
        
        if status_val:
            return_request.status = status_val
        if admin_notes:
            return_request.admin_notes = admin_notes
        if pickup_date:
            return_request.pickup_date = pickup_date
        if pickup_address:
            return_request.pickup_address = pickup_address
        
        return_request.save()
        
        # If refunded, credit to wallet
        if status_val == 'Refunded' and return_request.refund_amount:
            wallet, created = Wallet.objects.get_or_create(user=return_request.user)
            wallet.balance += return_request.refund_amount
            wallet.save()
            
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='Credit',
                amount=return_request.refund_amount,
                description=f'Refund for return #{return_request.return_id}'
            )
        
        serializer = ProductReturnAdminSerializer(return_request)
        return Response(serializer.data)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_all_cancellations(request):
    """Admin: Get all cancellation requests"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    cancellations = ProductCancellation.objects.all().select_related('user', 'order', 'order_item', 'order_item__product').order_by('-created_at')
    serializer = ProductCancellationAdminSerializer(cancellations, many=True)
    return Response(serializer.data)


@csrf_exempt
@api_view(['GET', 'PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_cancellation_detail(request, cancellation_id):
    """Admin: Get or update a cancellation request"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        cancellation = ProductCancellation.objects.get(id=cancellation_id)
    except ProductCancellation.DoesNotExist:
        return Response({'error': 'Cancellation request not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ProductCancellationAdminSerializer(cancellation)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        status_val = request.data.get('status')
        admin_notes = request.data.get('admin_notes', '')
        
        if status_val:
            cancellation.status = status_val
        if admin_notes:
            cancellation.admin_notes = admin_notes
        
        cancellation.save()
        
        # If refunded, credit to wallet
        if status_val == 'Refunded' and cancellation.refund_amount:
            wallet, created = Wallet.objects.get_or_create(user=cancellation.user)
            wallet.balance += cancellation.refund_amount
            wallet.save()
            
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='Credit',
                amount=cancellation.refund_amount,
                description=f'Refund for cancellation #{cancellation.cancellation_id}'
            )
        
        serializer = ProductCancellationAdminSerializer(cancellation)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def wholesale_apply(request):
    serializer = WholesaleApplicationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Application submitted successfully!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_wholesale_applications(request):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    applications = WholesaleApplication.objects.all().order_by('-created_at')
    serializer = WholesaleApplicationSerializer(applications, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_wholesale_status(request, pk):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        app = WholesaleApplication.objects.get(pk=pk)
        app.status = request.data.get('status', app.status)
        app.save()
        return Response(WholesaleApplicationSerializer(app).data)
    except WholesaleApplication.DoesNotExist:
        return Response({'error': 'Application not found'}, status=404)
