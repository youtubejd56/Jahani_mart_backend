from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='api_home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/suggested/', views.suggested_products, name='suggested_products'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:category_id>/products/', views.products_by_category, name='products_by_category'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('me/', views.current_user, name='current_user'),
    path('profile/', views.profile_details, name='profile_details'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('cart/', views.cart, name='cart'),
    path('cart/<int:item_id>/', views.cart_item, name='cart_item'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/<int:address_id>/', views.address_detail, name='address_detail'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<str:order_id>/', views.order_detail, name='order_detail'),
    path('wallet/', views.wallet_details, name='wallet_details'),
    path('wallet/add-money/', views.add_money, name='add_money'),
    # Admin URLs
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/orders/<str:order_id>/', views.update_order_status, name='update_order_status'),
    path('admin/users/', views.admin_all_users, name='admin_all_users'),
    # Admin Categories
    path('admin/categories/', views.admin_categories, name='admin_categories'),
    path('admin/categories/<int:category_id>/', views.admin_category_detail, name='admin_category_detail'),
    # Admin Products
    path('admin/products/', views.admin_products, name='admin_products'),
    path('admin/products/<int:product_id>/', views.admin_product_detail, name='admin_product_detail'),
    # Reviews
    path('reviews/', views.reviews, name='reviews'),
    path('reviews/<int:review_id>/', views.review_detail, name='review_detail'),
    path('products/<int:product_id>/reviews/', views.product_reviews, name='product_reviews'),
    # Admin Reviews
    path('admin/reviews/', views.admin_reviews, name='admin_reviews'),
    # Wishlist
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    # Support & Help
    path('support/tickets/', views.support_tickets, name='support_tickets'),
    path('support/tickets/<str:ticket_id>/', views.support_ticket_detail, name='support_ticket_detail'),
    path('support/tickets/<str:ticket_id>/reply/', views.ticket_reply, name='ticket_reply'),
    path('support/create/', views.create_support_ticket, name='create_support_ticket'),
    path('faqs/', views.faq_list, name='faq_list'),
    # Admin Support
    path('admin/support/tickets/', views.admin_all_tickets, name='admin_all_tickets'),
    path('admin/support/tickets/<str:ticket_id>/', views.admin_ticket_detail, name='admin_ticket_detail'),
    path('admin/support/tickets/<str:ticket_id>/reply/', views.admin_ticket_reply, name='admin_ticket_reply'),
    path('admin/support/tickets/<str:ticket_id>/status/', views.admin_update_ticket_status, name='admin_update_ticket_status'),
    # Admin Story Sections
    path('admin/stories/', views.admin_story_sections, name='admin_story_sections'),
    path('admin/stories/<int:section_id>/', views.admin_story_section_detail, name='admin_story_section_detail'),
    # Admin Blog Posts
    path('admin/blog/', views.admin_blog_posts, name='admin_blog_posts'),
    path('admin/blog/<int:post_id>/', views.admin_blog_post_detail, name='admin_blog_post_detail'),
    # Public Blog Posts
    path('blog/', views.public_blog_posts, name='public_blog_posts'),
]
