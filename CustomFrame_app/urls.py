from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from CustomFrame_app import views
from CustomFrame_app.views import FrameListCreateView, UserDetailView, UserListView, \
    ColorVariantDetailView, SizeVariantDetailView, FinishingVariantDetailView, HangingVariantDetailView, UserManageView, \
    FrameDetailView, BulkVariantCreateView, UploadCroppedImageView, AddToCartView, CartDetailView, CartItemDetailView, \
    upload_image

urlpatterns = [
    path('api/user_registration/', views.user_registration, name='user_registration'),
    path('api/user_login/', views.user_login, name='user_login'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
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
    path('cart/', CartDetailView.as_view(), name='cart_detail'),
    path('cart/items/<int:item_id>/', CartItemDetailView.as_view(), name='cart_item_detail'),
]
