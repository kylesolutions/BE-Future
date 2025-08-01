import logging
import os
from django.conf import settings
from django.core.files.storage import default_storage, FileSystemStorage
from django.core.mail import send_mail
from django.db.models import ProtectedError
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from rest_framework import status, generics, views, serializers, viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken
from CustomFrame_app.forms import UserRegister
from CustomFrame_app.models import Frame, Login, ColorVariant, SizeVariant, FinishingVariant, FrameHangVariant, Cart, \
    CartItem, FrameCategories, SavedItem, MackBoard, Mug, Cap, Tshirt, Tile, Pens, GiftOrder, MackBoardColorVariant
from CustomFrame_app.serializer import (
    FrameSerializer, ColorVariantSerializer, SizeVariantSerializer,
    FinishingVariantSerializer, HangingsVariantSerializer, UserDetails_Serializer, CartItemCreateSerializer,
    CartItemSerializer, CartItemUpdateSerializer, FrameCategoriesSerializer, MackBoardSerializer, SavedItemSerializer,
    MugSerializer, CapSerializer, TshirtSerializer, TileSerializer, PenSerializer, GiftOrderSerializer,
    MackBoardColorVariantSerializer,
)
import json

def index(request):
    return HttpResponse("Welcome to the Custom Photo Frame App!")

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access

    def post(self, request):
        form = UserRegister(request.data)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            # user.is_user = True  # Already set in UserRegister form
            user.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'result': True,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_201_CREATED)
        else:
            error_dict = {field: errors[0] for field, errors in form.errors.items()}
            return Response({
                'result': False,
                'errors': error_dict
            }, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def user_login(request):
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
            except json.JSONDecodeError:
                return JsonResponse({'status': False, 'result': 'Invalid JSON'}, status=400)
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')

        print(f"Username: {username}, Password: {password}")  # Debugging
        user = authenticate(request, username=username, password=password)
        print(f"User: {user}")  # Debugging

        if user is not None:
            if user.is_blocked:
                return JsonResponse({'status': False, 'result': 'User is blocked'}, status=403)
            login(request, user)
            user_type = 'user' if user.is_user else 'manager' if user.is_employee else 'admin' if user.is_staff else 'unknown'
            data = {
                'status': True,
                'result': {
                    'id': user.id,
                    'name': user.name,
                    'username': user.username,
                    'type': user_type,
                    'phone': user.phone,
                    'email': user.email,
                    'is_blocked': user.is_blocked,
                },
            }
            return JsonResponse(data)
        else:
            return JsonResponse({'status': False, 'result': 'Invalid username or password'}, status=400)
    return JsonResponse({'status': False, 'result': 'Invalid request method'}, status=405)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'name': user.name,
            'phone': user.phone,
            'type': user.role,  # Map role to type
            'is_blocked': user.is_blocked,
        })

class FrameCategoriesListCreateView(generics.ListCreateAPIView):
    queryset = FrameCategories.objects.all()
    serializer_class = FrameCategoriesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class FrameCategoriesDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FrameCategories.objects.all()
    serializer_class = FrameCategoriesSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can update categories")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can delete categories")
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError("Cannot delete category with associated frames")

class FrameListCreateView(generics.ListCreateAPIView):
    serializer_class = FrameSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Frame.objects.all()
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            return Response(
                {"error": "Only admins can create frames"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save(created_by=self.request.user)

class FrameDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, frame_id):
        try:
            frame = Frame.objects.get(id=frame_id)
            serializer = FrameSerializer(frame, context={'request': request})
            return Response(serializer.data)
        except Frame.DoesNotExist:
            return Response({"error": "Frame not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, frame_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can update frames"}, status=status.HTTP_403_FORBIDDEN)
        try:
            frame = Frame.objects.get(id=frame_id)
            print("Received data:", request.data)  # Debug: Log incoming data
            serializer = FrameSerializer(frame, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            print("Serializer errors:", serializer.errors)  # Debug: Log validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Frame.DoesNotExist:
            return Response({"error": "Frame not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, frame_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can delete frames"}, status=status.HTTP_403_FORBIDDEN)
        try:
            frame = Frame.objects.get(id=frame_id)
            frame.delete()
            return Response({"message": "Frame deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Frame.DoesNotExist:
            return Response({"error": "Frame not found"}, status=status.HTTP_404_NOT_FOUND)

class BulkVariantCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, frame_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can create variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            frame = Frame.objects.get(id=frame_id)
        except Frame.DoesNotExist:
            return Response({"error": "Frame not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get variants data, handling both list and JSON string
        variants_data = request.data.get('variants', [])
        if isinstance(variants_data, str):
            try:
                variants_data = json.loads(variants_data)
            except json.JSONDecodeError:
                return Response({"error": "Variants must be a valid JSON list"}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(variants_data, list):
            return Response({"error": "Variants must be provided as a list"}, status=status.HTTP_400_BAD_REQUEST)

        created_variants = []
        errors = []

        for variant_data in variants_data:
            variant_type = variant_data.get('variant_type')
            variant_form_data = request.FILES.get(variant_data.get('image_key')) if variant_data.get('image_key') else None
            variant_corner_form_data = request.FILES.get(f"{variant_data.get('image_key')}_corner") if variant_data.get('image_key') else None
            if variant_form_data:
                variant_data['image'] = variant_form_data
            if variant_corner_form_data and variant_type != 'hanging':
                variant_data['corner_image'] = variant_corner_form_data

            if not variant_type:
                errors.append({"error": "variant_type is required"})
                continue

            if variant_type == 'color':
                serializer = ColorVariantSerializer(data=variant_data, context={'request': request})
            elif variant_type == 'size':
                serializer = SizeVariantSerializer(data=variant_data, context={'request': request})
            elif variant_type == 'finish':
                serializer = FinishingVariantSerializer(data=variant_data, context={'request': request})
            elif variant_type == 'hanging':
                serializer = HangingsVariantSerializer(data=variant_data, context={'request': request})
            else:
                errors.append({"error": f"Invalid variant type: {variant_type}"})
                continue

            if serializer.is_valid():
                try:
                    instance = serializer.save(frame=frame)
                    created_variants.append(serializer.data)
                except ValidationError as e:
                    errors.append({"error": str(e)})
            else:
                errors.append(serializer.errors)

        if errors:
            return Response({"created": created_variants, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(created_variants, status=status.HTTP_201_CREATED)

class ColorVariantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can update variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = ColorVariant.objects.get(id=variant_id)
            serializer = ColorVariantSerializer(variant, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ColorVariant.DoesNotExist:
            return Response({"error": "Color variant not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can delete variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = ColorVariant.objects.get(id=variant_id)
            variant.delete()
            return Response({"message": "Color variant deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except ColorVariant.DoesNotExist:
            return Response({"error": "Color variant not found"}, status=status.HTTP_404_NOT_FOUND)

class SizeVariantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can update variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = SizeVariant.objects.get(id=variant_id)
            serializer = SizeVariantSerializer(variant, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SizeVariant.DoesNotExist:
            return Response({"error": "Size variant not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can delete variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = SizeVariant.objects.get(id=variant_id)
            variant.delete()
            return Response({"message": "Size variant deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except SizeVariant.DoesNotExist:
            return Response({"error": "Size variant not found"}, status=status.HTTP_404_NOT_FOUND)

class FinishingVariantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can update variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = FinishingVariant.objects.get(id=variant_id)
            serializer = FinishingVariantSerializer(variant, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except FinishingVariant.DoesNotExist:
            return Response({"error": "Finishing variant not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can delete variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = FinishingVariant.objects.get(id=variant_id)
            variant.delete()
            return Response({"message": "Finishing variant deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except FinishingVariant.DoesNotExist:
            return Response({"error": "Finishing variant not found"}, status=status.HTTP_404_NOT_FOUND)

class HangingVariantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can update variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = FrameHangVariant.objects.get(id=variant_id)
            serializer = HangingsVariantSerializer(variant, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except FrameHangVariant.DoesNotExist:
            return Response({"error": "Hanging variant not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can delete variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = FrameHangVariant.objects.get(id=variant_id)
            variant.delete()
            return Response({"message": "Hanging variant deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except FrameHangVariant.DoesNotExist:
            return Response({"error": "Hanging variant not found"}, status=status.HTTP_404_NOT_FOUND)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        serializer = UserDetails_Serializer(user)
        return Response(serializer.data)

class UserListView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        users = Login.objects.filter(is_user=True)
        serializer = UserDetails_Serializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserManageView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, user_id):
        try:
            user = Login.objects.get(id=user_id)
            serializer = UserDetails_Serializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Login.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, user_id):
        try:
            user = Login.objects.get(id=user_id)
            user.delete()
            return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Login.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def upload_image(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    original_image = request.FILES.get('original_image')
    if not original_image:
        return JsonResponse({'error': 'No image provided'}, status=400)
    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'cart/original'))
    filename = fs.save(original_image.name, original_image)
    original_url = request.build_absolute_uri(f"{settings.MEDIA_URL}cart/original/{filename}")
    return JsonResponse({'original_url': original_url})

class CroppedImageUploadSerializer(serializers.Serializer):
    cropped_image = serializers.ImageField()

    def validate_cropped_image(self, value):
        if not value:
            raise serializers.ValidationError("Cropped image is required.")
        return value

class UploadCroppedImageView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CroppedImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            cropped_image = serializer.validated_data['cropped_image']
            file_path = f"cart/cropped/{cropped_image.name}"
            saved_path = default_storage.save(file_path, cropped_image)
            cropped_url = request.build_absolute_uri(f"/media/{saved_path}")
            return Response({"cropped_url": cropped_url}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            frame = serializer.validated_data['frame']
            for variant_type in ['color_variant', 'size_variant', 'finish_variant', 'hanging_variant']:
                variant = serializer.validated_data.get(variant_type)
                if variant and variant.frame != frame:
                    return Response({"error": f"{variant_type} does not belong to the selected frame"},
                                    status=status.HTTP_400_BAD_REQUEST)
            cart_item = serializer.save(cart=cart)
            return Response(CartItemSerializer(cart_item, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MackBoardListCreateView(generics.ListCreateAPIView):
    queryset = MackBoard.objects.all()
    serializer_class = MackBoardSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can create MackBoards")
        serializer.save()


class MackBoardColorVariantListCreateView(generics.ListCreateAPIView):
    queryset = MackBoardColorVariant.objects.all()
    serializer_class = MackBoardColorVariantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can create MackBoardColorVariants")
        serializer.save()

class MackBoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MackBoard.objects.all()
    serializer_class = MackBoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can update MackBoards")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can delete MackBoards")
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError("Cannot delete MackBoard with associated dependencies")

class CartDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()
        serializer = CartItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            serializer = CartItemUpdateSerializer(cart_item, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                cart_item.save()  # Recalculate total_price
                return Response(CartItemSerializer(cart_item, context={'request': request}).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, item_id):
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart_item.delete()
            return Response({"message": "Cart item deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class SavedItemView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        try:
            if request.user.is_staff or request.user.is_superuser:
                items = SavedItem.objects.all()
            else:
                items = SavedItem.objects.filter(user=request.user)

            serializer = SavedItemSerializer(items, many=True, context={'request': request})
            logger.debug(f"Fetched {len(items)} saved items for user {request.user.username}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in GET /save-items/: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        logger.debug(f"POST request data: {request.data}")
        serializer = SavedItemSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            item = serializer.save()
            logger.debug(f"SavedItem created: {item.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response({"error": "Invalid data", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, *args, **kwargs):
        logger.debug(f"PUT request data for pk {pk}: {request.data}")
        try:
            instance = SavedItem.objects.get(pk=pk)
        except SavedItem.DoesNotExist:
            logger.error(f"SavedItem {pk} not found")
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = SavedItemSerializer(instance, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            item = serializer.save()
            logger.debug(f"SavedItem {pk} updated")
            return Response(serializer.data)
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response({"error": "Invalid data", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            if request.user.is_staff or request.user.is_superuser:
                item = SavedItem.objects.get(pk=pk)
            else:
                item = SavedItem.objects.get(pk=pk, user=request.user)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SavedItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

from django.http import JsonResponse
from django.core.mail import send_mail
from rest_framework.decorators import api_view
from rest_framework import status
from .models import SavedItem, GiftOrder
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
def send_order_confirmation(request):
    try:
        data = request.data
        customer_email = data.get('customerEmail')
        customer_name = data.get('customerName')
        customer_phone = data.get('customerPhone')
        order_details = data.get('orderDetails')
        total_cost = data.get('totalCost')
        sender_email = data.get('senderEmail', 'jayalakshmikyle@gmail.com')
        custom_message = data.get('customMessage', '')

        if not all([customer_email, customer_name, order_details, total_cost]):
            logger.error("Missing required fields in send_order_confirmation")
            return JsonResponse(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Plain text email for fallback
        plain_message = f"Dear {customer_name},\n\nYour order has been confirmed!\n\nOrder Details:\n"
        for item in order_details:
            if item.get('type') == 'gift':
                plain_message += f"- Gift Item: {item['content_type']} (ID: {item['object_id']}), Price: ${item['price']}\n"
            else:
                plain_message += (
                    f"- Frame: {item['frame']}, "
                    f"Print Size: {item['printSize']}, "
                    f"Media Type: {item['mediaType']}, "
                    f"Paper Type: {item['paperType']}, "
                    f"Fit: {item['fit']}, "
                    f"Mack Boards: {item['mackBoards']}, "
                    f"Price: ${item['price']}\n"
                )
        plain_message += f"\nTotal Cost: ${total_cost}\nPhone: {customer_phone}\n"
        if custom_message:
            plain_message += f"\nCustom Message: {custom_message}\n"
        plain_message += "\nThank you for your order!"

        # HTML email template
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                    <h2 style="color: #2c3e50; text-align: center;">Order Confirmation</h2>
                    <p>Dear {customer_name},</p>
                    <p>Thank you for your order! Below are the details of your purchase:</p>
                    <h3 style="color: #2c3e50;">Order Details</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #f2f2f2;">
                                <th style="border: 1px solid #ddd; padding: 8px;">Item</th>
                                <th style="border: 1px solid #ddd; padding: 8px;">Details</th>
                                <th style="border: 1px solid #ddd; padding: 8px;">Price</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([
                                f"""
                                <tr>
                                    <td style="border: 1px solid #ddd; padding: 8px;">
                                        {"Gift Item" if item['type'] == 'gift' else "Framed Item"}
                                    </td>
                                    <td style="border: 1px solid #ddd; padding: 8px;">
                                        {"<strong>Type:</strong> " + item['content_type'] + "<br><strong>ID:</strong> " + str(item['object_id']) if item['type'] == 'gift' else (
                                            f"<strong>Frame:</strong> {item['frame']}<br>"
                                            f"<strong>Print Size:</strong> {item['printSize']}<br>"
                                            f"<strong>Media Type:</strong> {item['mediaType']}<br>"
                                            f"<strong>Paper Type:</strong> {item['paperType']}<br>"
                                            f"<strong>Fit:</strong> {item['fit']}<br>"
                                            f"<strong>Border Depth:</strong> {item['borderDepth']}<br>"
                                            f"<strong>Border Color:</strong> {item['borderColor']}<br>"
                                            f"<strong>Frame Depth:</strong> {item['frameDepth']}<br>"
                                            f"<strong>Color Variant:</strong> {item['color']}<br>"
                                            f"<strong>Size Variant:</strong> {item['size']}<br>"
                                            f"<strong>Finish Variant:</strong> {item['finish']}<br>"
                                            f"<strong>Hanging Variant:</strong> {item['hanging']}<br>"
                                            f"<strong>Mack Boards:</strong> {item['mackBoards']}"
                                        )}
                                    </td>
                                    <td style="border: 1px solid #ddd; padding: 8px;">${item['price']}</td>
                                </tr>
                                """ for item in order_details
                            ])}
                        </tbody>
                    </table>
                    <p><strong>Total Cost:</strong> ${total_cost}</p>
                    <p><strong>Phone:</strong> {customer_phone}</p>
                    {"<p><strong>Custom Message:</strong> " + custom_message + "</p>" if custom_message else ""}
                    <p style="text-align: center; margin-top: 20px;">
                        Thank you for choosing us! If you have any questions, please contact us at {sender_email}.
                    </p>
                    <p style="text-align: center; font-size: 12px; color: #777;">
                        &copy; 2025 Your Company Name. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """

        # Send email
        send_mail(
            subject=f"Order Confirmation for {customer_name}",
            message=plain_message,
            from_email=sender_email,
            recipient_list=[customer_email],
            html_message=html_message,
            fail_silently=False,
        )

        # Update status of all user's saved items and gift orders to 'paid'
        SavedItem.objects.filter(user=request.user).update(status='paid')
        GiftOrder.objects.filter(user=request.user).update(status='paid')

        logger.info(f"Order confirmation email sent to {customer_email}")
        return JsonResponse({'message': 'Order confirmation sent and status updated'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error sending order confirmation: {str(e)}")
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def update_saved_items_status(request):
    try:
        SavedItem.objects.filter(user=request.user).update(status='paid')
        return JsonResponse({'message': 'Saved items status updated to paid'}, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateGiftOrdersStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            order_ids = request.data.get('orderIds', [])
            if not order_ids:
                return Response({"error": "No order IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
            GiftOrder.objects.filter(id__in=order_ids, user=request.user).update(status='paid')
            logger.info(f"Updated status to 'paid' for GiftOrder IDs {order_ids} for user {request.user.username}")
            return Response({"message": "Gift order statuses updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error updating gift order statuses: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class MugListCreateView(generics.ListCreateAPIView):
    queryset = Mug.objects.all()
    serializer_class = MugSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can create Mugs")
        serializer.save()

class MugDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Mug.objects.all()
    serializer_class = MugSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can update Mugs")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can delete Mugs")
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError("Cannot delete Mug with associated dependencies")

class CapListCreateView(generics.ListCreateAPIView):
    queryset = Cap.objects.all()
    serializer_class = CapSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can create Caps")
        serializer.save()

class CapDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cap.objects.all()
    serializer_class = CapSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can update Caps")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can delete Caps")
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError("Cannot delete Cap with associated dependencies")

class TshirtListCreateView(generics.ListCreateAPIView):
    queryset = Tshirt.objects.all()
    serializer_class = TshirtSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can create Tshirts")
        serializer.save()

class TshirtDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tshirt.objects.all()
    serializer_class = TshirtSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can update Tshirts")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can delete Tshirts")
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError("Cannot delete Tshirt with associated dependencies")

class TileListCreateView(generics.ListCreateAPIView):
    queryset = Tile.objects.all()
    serializer_class = TileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can create Tiles")
        serializer.save()

class TileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tile.objects.all()
    serializer_class = TileSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can update Tiles")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can delete Tiles")
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError("Cannot delete Tile with associated dependencies")

class PenListCreateView(generics.ListCreateAPIView):
    queryset = Pens.objects.all()
    serializer_class = PenSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can create Pens")
        serializer.save()

class PenDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Pens.objects.all()
    serializer_class = PenSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can update Pens")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can delete Pens")
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError("Cannot delete Pen with associated dependencies")


class GiftOrderCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        logger.debug(f"Received POST data: {request.data}")
        serializer = GiftOrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            logger.info(f"GiftOrder created successfully for user {request.user.username}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            if request.user.is_staff or request.user.is_superuser:
                item = GiftOrder.objects.get(pk=pk)
            else:
                item = GiftOrder.objects.get(pk=pk, user=request.user)
            item.delete()
            logger.info(f"GiftOrder {pk} deleted by user {request.user.username}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except GiftOrder.DoesNotExist:
            logger.error(f"GiftOrder {pk} not found")
            return Response({"error": "Gift order not found"}, status=status.HTTP_404_NOT_FOUND)

class GiftOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GiftOrderSerializer

    def get_queryset(self):
        logger.debug(f"Fetching gift orders for user {self.request.user.username}")
        if self.request.user.is_staff or self.request.user.is_superuser:
            return GiftOrder.objects.all().order_by('-created_at')
        return GiftOrder.objects.filter(user=self.request.user, status='pending').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        logger.info(f"Retrieved {len(queryset)} gift orders for user {request.user.username}")
        return Response(serializer.data)