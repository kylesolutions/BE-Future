from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from CustomFrame_app import views
from CustomFrame_app.views import UserDetailView, UserListView, \
    ColorVariantDetailView, SizeVariantDetailView, FinishingVariantDetailView, HangingVariantDetailView, UserManageView, \
    FrameDetailView, BulkVariantCreateView, UploadCroppedImageView, AddToCartView, \
    upload_image, UserRegistrationView, FrameCategoriesListCreateView, \
    FrameListCreateView, FrameCategoriesDetailView, SavedItemView, MackBoardListCreateView, MackBoardDetailView, \
    CurrentUserView, MugListCreateView, CapListCreateView, TshirtListCreateView, TileListCreateView, PenListCreateView, \
    MackBoardColorVariantListCreateView, PrintTypeView, PrintSizeView, PaperTypeView, \
    LaminationTypeView, update_document_print_orders_status, \
    update_gift_orders_status, update_saved_items_status, \
    DocumentPrintOrderView, DocumentPrintOrderDetailView, TshirtDetailView, \
    TshirtBulkVariantCreateView, TshirtColorVariantDetailView, TshirtSizeVariantDetailView, GiftOrderCreateView, \
    GiftOrderListView, OrderView, OrderDetailView, GiftOrderDetailView, MackBoardColorVariantDetailView, MugDetailView, \
    TileDetailView, CapDetailView, PenDetailView, ThemeListCreateView, ThemeDetailView, BackgroundListCreateView, \
    BackgroundDetailView, StickerListCreateView, StickerDetailView, PhotoBookPapersListCreateView, \
    PhotoBookPapersDetailView, PhotoBookOrderCreateView, ImageUploadView, PhotoBookOrderListView, \
    PhotoBookOrderDeleteView

urlpatterns = [
    path('api/user_registration/', UserRegistrationView.as_view(), name='user_registration'),
    path('api/user_login/', views.user_login, name='user_login'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/current-user/', CurrentUserView.as_view(), name='current_user'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('mack_boards/', MackBoardListCreateView.as_view(), name='mack_board-list-create'),
    path('mack_boards/<int:pk>/', MackBoardDetailView.as_view(), name='mack_board-detail'),
    path('mack_board_color_variants/', MackBoardColorVariantListCreateView.as_view(), name='mack_board_color_variant-list-create'),
    path('mack_board_color_variants/<int:variant_id>/', MackBoardColorVariantDetailView.as_view(), name='mack_board_color_variant-detail'),
    path('categories/', FrameCategoriesListCreateView.as_view(), name='categories-list-create'),
    path('categories/<int:pk>/', FrameCategoriesDetailView.as_view(), name='categories-detail'),
    path('frames/', FrameListCreateView.as_view(), name='frame-list-create'),
    path('frames/<int:frame_id>/', FrameDetailView.as_view(), name='frame-detail'),
    path('frames/<int:frame_id>/variants/', BulkVariantCreateView.as_view(), name='variant-create'),
    path('variants/color/<int:variant_id>/', ColorVariantDetailView.as_view(), name='color-variant-detail'),
    path('variants/size/<int:variant_id>/', SizeVariantDetailView.as_view(), name='size-variant-detail'),
    path('variants/finish/<int:variant_id>/', FinishingVariantDetailView.as_view(), name='finish-variant-detail'),
    path('variants/hanging/<int:variant_id>/', HangingVariantDetailView.as_view(), name='hanging-variant-detail'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:user_id>/', UserManageView.as_view(), name='user-manage'),
    path('upload-image/', upload_image, name='upload_image'),
    path('upload-cropped-image/', UploadCroppedImageView.as_view(), name='upload-cropped-image'),
    path('add-to-cart/', AddToCartView.as_view(), name='add_to_cart'),
    path('save-items/', SavedItemView.as_view(), name='save_items'),
    path('save-items/<int:pk>/', SavedItemView.as_view(), name='save_item_detail'),
    path('mugs/', MugListCreateView.as_view(), name='mug-list-create'),
    path('mugs/<int:pk>/', MugDetailView.as_view(), name='mug-detail'),
    path('caps/', CapListCreateView.as_view(), name='cap-list-create'),
    path('caps/<int:pk>/', CapDetailView.as_view(), name='cap-detail'),
    path('tshirts/', TshirtListCreateView.as_view(), name='tshirt-list-create'),
    path('tshirts/<int:tshirt_id>/', TshirtDetailView.as_view(), name='tshirt-detail'),
    path('tshirts/<int:tshirt_id>/variants/', TshirtBulkVariantCreateView.as_view(), name='tshirt-bulk-variant-create'),
    path('tshirt_color_variants/<int:variant_id>/', TshirtColorVariantDetailView.as_view(), name='tshirt-color-variant-detail'),
    path('tshirt_size_variants/<int:variant_id>/', TshirtSizeVariantDetailView.as_view(), name='tshirt-size-variant-detail'),
    path('tiles/', TileListCreateView.as_view(), name='tile-list-create'),
    path('tiles/<int:pk>/', TileDetailView.as_view(), name='tile-detail'),
    path('pens/', PenListCreateView.as_view(), name='pen-list-create'),
    path('pens/<int:pk>/', PenDetailView.as_view(), name='pen-detail'),
    path('gift-orders/', GiftOrderCreateView.as_view(), name='gift-order-create'),
    path('gift-orders/list/', GiftOrderListView.as_view(), name='gift-order-list'),
    path('gift-orders/<int:pk>/', GiftOrderDetailView.as_view(), name='gift-order-detail'),
    path('api/orders/', OrderView.as_view(), name='order_create'),
    path('api/orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('api/print-types/', PrintTypeView.as_view(), name='print_type_list_create'),
    path('api/print-types/<int:pk>/', PrintTypeView.as_view(), name='print_type_detail'),
    path('api/print-sizes/', PrintSizeView.as_view(), name='print_size_list_create'),
    path('api/print-sizes/<int:pk>/', PrintSizeView.as_view(), name='print_size_detail'),
    path('api/paper-types/', PaperTypeView.as_view(), name='paper_type_list_create'),
    path('api/paper-types/<int:pk>/', PaperTypeView.as_view(), name='paper_type_detail'),
    path('api/lamination-types/', LaminationTypeView.as_view(), name='lamination_type_list_create'),
    path('api/lamination-types/<int:pk>/', LaminationTypeView.as_view(), name='lamination_type_detail'),
    path('api/document-print-orders/', DocumentPrintOrderView.as_view(), name='document_print_order_create'),
    path('api/document-print-orders/<int:pk>/', DocumentPrintOrderDetailView.as_view(), name='document_print_order_detail'),
    path('send-order-confirmation/', views.send_order_confirmation, name='send_order_confirmation'),
    path('update-saved-items-status/', views.update_saved_items_status, name='update_saved_items_status'),
    path('update-gift-orders-status/', views.update_gift_orders_status, name='update_gift_orders_status'),
    path('update-document-print-orders-status/', views.update_document_print_orders_status, name='update_document_print_orders_status'),
    path('update-simple-document-orders-status/', views.update_simple_document_orders_status, name='update_simple_document_orders_status'),
    path('themes/', ThemeListCreateView.as_view(), name='theme-list-create'),
    path('themes/<int:pk>/', ThemeDetailView.as_view(), name='theme-detail'),
    path('backgrounds/', BackgroundListCreateView.as_view(), name='background-list-create'),
    path('backgrounds/<int:pk>/', BackgroundDetailView.as_view(), name='background-detail'),
    path('stickers/', StickerListCreateView.as_view(), name='sticker-list-create'),
    path('stickers/<int:pk>/', StickerDetailView.as_view(), name='sticker-detail'),
    path('photobook-papers/', PhotoBookPapersListCreateView.as_view(), name='photobook-papers-list-create'),
    path('photobook-papers/<int:pk>/', PhotoBookPapersDetailView.as_view(), name='photobook-papers-detail'),
    path('orders/', PhotoBookOrderListView.as_view(), name='order-list'),
    path('orders/create/', PhotoBookOrderCreateView.as_view(), name='order-create'),
    path('orders/<int:order_id>/', PhotoBookOrderDeleteView.as_view(), name='order-delete'),
    path('upload-images/', ImageUploadView.as_view(), name='image-upload'),
]







