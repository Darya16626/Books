from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Импортируем обычные views
from .views import (
    login_view, logout_view, register_view,
    admin_page, manager_page, client_page,
    admin_users_list, admin_user_create, admin_user_edit,
    admin_user_delete, admin_user_toggle_block,
    book_catalog, book_create, book_edit, book_delete, book_detail,
    promotions_list, promotion_create, promotion_edit, promotion_delete,
    promotion_books_select, promotion_books_list,
    client_book_catalog, add_to_cart, add_to_favorites,
    client_promotion_books, clients_book_detail, favorites_view,
    client_profile_view, balance_view, clear_balance_history,
    ajax_get_user_cards, manager_order_edit, order_checkout_view,
    cart_view, export_excel, client_support_chat, manager_support_page,
    manager_chat_detail, delete_chat, delete_message, edit_message,
    mark_as_read, restore_login_view, set_new_password_view,
    manager_order_list, manager_order_delete, client_order_history,
    clear_order_history, manager_order_analytics, analytics_view,
    admin_design  # Добавлен недостающий импорт
)

# Импортируем API ViewSets
from .views import BookViewSet, OrderViewSet, PromotionViewSet

# API роутер
router = DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'promotions', PromotionViewSet)

urlpatterns = [
    # API - ПЕРВЫМ!
    path('api/', include(router.urls)),
    
    # Админка: акции
    path('admin/promotions/', promotions_list, name='promotions_list'),
    path('admin/promotions/add/', promotion_create, name='promotion_create'),
    path('admin/promotions/<int:promotion_id>/edit/', promotion_edit, name='promotion_edit'),
    path('admin/promotions/<int:promotion_id>/delete/', promotion_delete, name='promotion_delete'),
    path('admin/promotions/<int:promotion_id>/books/select/', promotion_books_select, name='promotion_books_select'),
    path('admin/promotions/<int:promotion_id>/books/', promotion_books_list, name='promotion_books_list'),
    path('admin/design/', views.admin_design, name='admin_design'),

    # Админка: книги
    path('admin/books/', book_catalog, name='book_catalog'),
    path('admin/books/add/', book_create, name='book_create'),
    path('admin/books/<int:book_id>/edit/', book_edit, name='book_edit'),
    path('admin/books/<int:book_id>/delete/', book_delete, name='book_delete'),
    path('admin/books/<int:book_id>/', book_detail, name='book_detail'),

    # Админка: пользователи
    path('admin/users/', admin_users_list, name='admin_users_list'),
    path('admin/users/add/', admin_user_create, name='admin_user_create'),
    path('admin/users/<int:user_id>/edit/', admin_user_edit, name='admin_user_edit'),
    path('admin/users/<int:user_id>/delete/', admin_user_delete, name='admin_user_delete'),
    path('admin/users/<int:user_id>/toggle-block/', admin_user_toggle_block, name='admin_user_toggle_block'),

    # Авторизация и базовые страницы
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register_view, name="register"),
    path("admin/", admin_page, name="admin_page"),
    path("manager/", manager_page, name="manager_page"),
    path("client/", client_page, name="client_page"),

    # Каталог и корзина
    path('catalog/', client_book_catalog, name='client_book_catalog'),
    path('catalog/book/<int:book_id>/', book_detail, name='book_detail'),
    path('catalog/add-to-cart/<int:book_id>/', add_to_cart, name='add_to_cart'),
    path('catalog/add-to-favorites/<int:book_id>/', add_to_favorites, name='add_to_favorites'),
    path('cart/', views.cart_view, name='cart_view'),

    # Избранное, профиль, баланс и пр.
    path('favorites/', favorites_view, name='favorites_view'),
    path('catalog/promotion/<int:promotion_id>/', client_promotion_books, name='client_promotion_books'),
    path('catalog/book/client/<int:book_id>/', clients_book_detail, name='clients_book_detail'),
    path('profile/', client_profile_view, name='client_profile'),
    path('balance/', balance_view, name='balance'),
    path('balance/clear-history/', clear_balance_history, name='clear_balance_history'),
    path('ajax/get_user_cards/', views.ajax_get_user_cards, name='ajax_get_user_cards'),
    path('export/excel/', views.export_excel, name='export_excel'),

    # Поддержка и чат
    path('support/chat/', views.client_support_chat, name='client_support_chat'),
    path('manager/support/', views.manager_support_page, name='manager_support_page'),
    path('manager/support/chat/<int:chat_id>/', views.manager_chat_detail, name='manager_chat_detail'),
    path('support/chat/delete/<int:chat_id>/', views.delete_chat, name='delete_chat'),
    path('support/message/delete/<int:message_id>/', views.delete_message, name='delete_message'),
    path('support/message/edit/<int:message_id>/', views.edit_message, name='edit_message'),
    path('support/message/mark-as-read/', views.mark_as_read, name='mark_as_read'),
    path('restore-login/', views.restore_login_view, name='restore_login'),
    path('set-new-password/<str:email>/', views.set_new_password_view, name='set_new_password'),
    path('order/checkout/', order_checkout_view, name='order_checkout'),

    path('manager/orders/', views.manager_order_list, name='manager_order_list'),
    path('manager/orders/new/', views.manager_order_edit, name='manager_order_edit'),  # создание заказа без order_id
    path('manager/orders/<int:order_id>/edit/', views.manager_order_edit, name='manager_order_edit'),
    path('manager/orders/<int:order_id>/delete/', views.manager_order_delete, name='manager_order_delete'),

    path('client/order-history/', views.client_order_history, name='client_order_history'),
    path('client/order-history/clear/', views.clear_order_history, name='clear_order_history'),
    path('manager/orders/analytics/', views.manager_order_analytics, name='manager_order_analytics'),
    path('admin/analytics/', views.analytics_view, name='admin_analytics'),
    path('manager/orders/new/', manager_order_edit, name='manager_order_edit_new'),  # создание нового заказа
    path('manager/orders/<int:order_id>/edit/', manager_order_edit, name='manager_order_edit'),
]
