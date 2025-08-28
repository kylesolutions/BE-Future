import logging
import os
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
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
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken
from CustomFrame_app.forms import UserRegister
from CustomFrame_app.models import Frame, Login, ColorVariant, SizeVariant, FinishingVariant, FrameHangVariant, Cart, \
    CartItem, FrameCategories, SavedItem, MackBoard, Mug, Cap, Tshirt, Tile, Pens, MackBoardColorVariant, \
    LaminationType, PaperType, PrintSize, PrintType, DocumentPrintOrder, TshirtSizeVariant, TshirtColorVariant, \
    GiftOrder, DocOrder, Order
from CustomFrame_app.serializer import (
    FrameSerializer, ColorVariantSerializer, SizeVariantSerializer,
    FinishingVariantSerializer, HangingsVariantSerializer, UserDetails_Serializer, CartItemCreateSerializer,
    CartItemSerializer, CartItemUpdateSerializer, FrameCategoriesSerializer, MackBoardSerializer, SavedItemSerializer,
    MugSerializer, CapSerializer, TileSerializer, PenSerializer,
    MackBoardColorVariantSerializer, DocumentPrintOrderSerializer, LaminationTypeSerializer, PaperTypeSerializer,
    PrintSizeSerializer, PrintTypeSerializer, TshirtSizeVariantSerializer, TshirtColorVariantSerializer,
    TshirtSerializer, GiftOrderSerializer, OrderSerializer,
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
                    'is_staff': user.is_staff,  # Add is_staff
                },
                'access': 'your_jwt_access_token',  # Replace with actual JWT token
                'refresh': 'your_jwt_refresh_token',  # Replace with actual JWT token
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
            'is_staff': user.is_staff,
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
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.debug(f"Received order_details: {order_details}")  # Debug log

        # Plain text email for fallback
        plain_message = f"Dear {customer_name},\n\nYour order has been confirmed!\n\nOrder Details:\n"
        for item in order_details:
            if item.get('type') == 'gift':
                object_id = item.get('object_id', 'N/A')  # Fallback for object_id
                plain_message += f"- Gift Item: {item.get('content_type', 'N/A')} (ID: {object_id}), Price: ${item.get('price', '0.00')}\n"
                if item.get('imageUrl'):
                    plain_message += f" Image: {item['imageUrl']}\n"
            elif item.get('type') == 'document':
                plain_message += (
                    f"- Document Print:\n"
                    f" Print Type: {item.get('print_type', 'N/A')}\n"
                    f" Print Size: {item.get('print_size', 'N/A')}\n"
                    f" Paper Type: {item.get('paper_type', 'N/A')}\n"
                    f" Quantity: {item.get('quantity', 'N/A')}\n"
                    f" Lamination: {item.get('lamination', 'No')}\n"
                    f" Lamination Type: {item.get('lamination_type', 'N/A')}\n"
                    f" Delivery Method: {item.get('delivery_method', 'N/A')}\n"
                    f" Delivery Charge: ${item.get('delivery_charge', '0.00')}\n"
                    f" Price: ${item.get('price', '0.00')}\n"
                )
                if item.get('imageUrl'):
                    plain_message += f" Image: {item['imageUrl']}\n"
            elif item.get('type') == 'simple_document':
                plain_message += (
                    f"- Simple Document Print:\n"
                    f" Print Type: {item.get('print_type', 'N/A')}\n"
                    f" Print Size: {item.get('print_size', 'N/A')}\n"
                    f" Paper Type: {item.get('paper_type', 'N/A')}\n"
                    f" Quantity: {item.get('quantity', 'N/A')}\n"
                    f" Lamination: {item.get('lamination', 'No')}\n"
                    f" Lamination Type: {item.get('lamination_type', 'N/A')}\n"
                    f" Delivery Option: {item.get('delivery_option', 'N/A')}\n"
                    f" Address: {item.get('address', 'N/A')}\n"
                    f" Files: {', '.join(item.get('files', [])) if item.get('files') else 'None'}\n"
                    f" Price: ${item.get('price', '0.00')}\n"
                )
                if item.get('imageUrl'):
                    plain_message += f" Image: {item['imageUrl']}\n"
            else:
                plain_message += (
                    f"- Frame: {item.get('frame', 'None')}, "
                    f"Print Size: {item.get('printSize', 'N/A')}, "
                    f"Media Type: {item.get('mediaType', 'None')}, "
                    f"Paper Type: {item.get('paperType', 'None')}, "
                    f"Fit: {item.get('fit', 'None')}, "
                    f"Mack Boards: {item.get('mackBoards', 'None')}, "
                    f"Price: ${item.get('price', '0.00')}\n"
                )
                if item.get('imageUrl'):
                    plain_message += f" Image: {item['imageUrl']}\n"
        plain_message += f"\nTotal Cost: ${total_cost}\nPhone: {customer_phone}\n"
        if custom_message:
            plain_message += f"\nCustom Message: {custom_message}\n"
        plain_message += "\nThank you for your order!"

        # HTML email template
        html_rows = ""
        for item in order_details:
            image_html = ""
            if item.get('imageUrl') and item['imageUrl'] != 'https://via.placeholder.com/100x100?text=Image+Not+Found':
                image_html = f'<img src="{item["imageUrl"]}" alt="Item Image" style="max-width: 100px; max-height: 100px; object-fit: cover;" />'
            if item.get('type') == 'gift':
                object_id = item.get('object_id', 'N/A')  # Fallback for object_id
                html_rows += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">{image_html or 'Gift Item'}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">
                            <strong>Type:</strong> {item.get('content_type', 'N/A')}<br>
                            <strong>ID:</strong> {object_id}
                        </td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${item.get('price', '0.00')}</td>
                    </tr>
                """
            elif item.get('type') == 'document':
                html_rows += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">{image_html or 'Document Print'}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">
                            <strong>Print Type:</strong> {item.get('print_type', 'N/A')}<br>
                            <strong>Print Size:</strong> {item.get('print_size', 'N/A')}<br>
                            <strong>Paper Type:</strong> {item.get('paper_type', 'N/A')}<br>
                            <strong>Quantity:</strong> {item.get('quantity', 'N/A')}<br>
                            <strong>Lamination:</strong> {item.get('lamination', 'No')}<br>
                            <strong>Lamination Type:</strong> {item.get('lamination_type', 'N/A')}<br>
                            <strong>Delivery Method:</strong> {item.get('delivery_method', 'N/A')}<br>
                            <strong>Delivery Charge:</strong> ${item.get('delivery_charge', '0.00')}
                        </td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${item.get('price', '0.00')}</td>
                    </tr>
                """
            elif item.get('type') == 'simple_document':
                html_rows += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">{image_html or 'Simple Document Print'}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">
                            <strong>Print Type:</strong> {item.get('print_type', 'N/A')}<br>
                            <strong>Print Size:</strong> {item.get('print_size', 'N/A')}<br>
                            <strong>Paper Type:</strong> {item.get('paper_type', 'N/A')}<br>
                            <strong>Quantity:</strong> {item.get('quantity', 'N/A')}<br>
                            <strong>Lamination:</strong> {item.get('lamination', 'No')}<br>
                            <strong>Lamination Type:</strong> {item.get('lamination_type', 'N/A')}<br>
                            <strong>Delivery Option:</strong> {item.get('delivery_option', 'N/A')}<br>
                            <strong>Address:</strong> {item.get('address', 'N/A')}<br>
                            <strong>Files:</strong> {', '.join(item.get('files', [])) if item.get('files') else 'None'}
                        </td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${item.get('price', '0.00')}</td>
                    </tr>
                """
            else:
                html_rows += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">{image_html or 'Framed Item'}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">
                            <strong>Frame:</strong> {item.get('frame', 'None')}<br>
                            <strong>Print Size:</strong> {item.get('printSize', 'N/A')}<br>
                            <strong>Media Type:</strong> {item.get('mediaType', 'None')}<br>
                            <strong>Paper Type:</strong> {item.get('paperType', 'None')}<br>
                            <strong>Fit:</strong> {item.get('fit', 'None')}<br>
                            <strong>Border Depth:</strong> {item.get('borderDepth', 'None')}<br>
                            <strong>Border Color:</strong> {item.get('borderColor', 'None')}<br>
                            <strong>Frame Depth:</strong> {item.get('frameDepth', 'None')}<br>
                            <strong>Color Variant:</strong> {item.get('color', 'None')}<br>
                            <strong>Size Variant:</strong> {item.get('size', 'None')}<br>
                            <strong>Finish Variant:</strong> {item.get('finish', 'None')}<br>
                            <strong>Hanging Variant:</strong> {item.get('hanging', 'None')}<br>
                            <strong>Mack Boards:</strong> {item.get('mackBoards', 'None')}
                        </td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${item.get('price', '0.00')}</td>
                    </tr>
                """

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
                            {html_rows}
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

        # Update status of all user's orders to 'paid'
        SavedItem.objects.filter(user=request.user).update(status='paid')
        GiftOrder.objects.filter(user=request.user).update(status='paid')
        DocumentPrintOrder.objects.filter(user=request.user).update(status='paid')
        DocOrder.objects.filter(user=request.user).update(status='paid')

        logger.info(f"Order confirmation email sent to {customer_email}")
        return Response({'message': 'Order confirmation sent and status updated'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error sending order confirmation: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def update_saved_items_status(request):
    try:
        order_ids = request.data.get('orderIds', [])
        if not order_ids:
            return Response({'error': 'No order IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        SavedItem.objects.filter(user=request.user, id__in=order_ids).update(status='paid')
        return Response({'message': 'Saved items status updated to paid'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error updating saved items status: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def update_gift_orders_status(request):
    try:
        order_ids = request.data.get('orderIds', [])
        if not order_ids:
            return Response({'error': 'No order IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        GiftOrder.objects.filter(user=request.user, id__in=order_ids).update(status='paid')
        return Response({'message': 'Gift orders status updated to paid'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error updating gift orders status: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def update_document_print_orders_status(request):
    try:
        order_ids = request.data.get('orderIds', [])
        if not order_ids:
            return Response({'error': 'No order IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        DocumentPrintOrder.objects.filter(user=request.user, id__in=order_ids).update(status='paid')
        return Response({'message': 'Document print orders status updated to paid'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error updating document print orders status: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def update_simple_document_orders_status(request):
    try:
        order_ids = request.data.get('orderIds', [])
        if not order_ids:
            return Response({'error': 'No order IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        DocOrder.objects.filter(user=request.user, id__in=order_ids).update(status='paid')  # Use DocOrder
        return Response({'message': 'Simple document orders status updated to paid'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error updating simple document orders status: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


logger = logging.getLogger(__name__)

class TshirtListCreateView(generics.ListCreateAPIView):
    queryset = Tshirt.objects.all()
    serializer_class = TshirtSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            return Response(
                {"error": "Only admins can create T-shirts"},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            login_instance = Login.objects.get(username=self.request.user.username)
        except Login.DoesNotExist:
            return Response({"error": "No Login record for this user"}, status=400)
        serializer.save(created_by=login_instance)


class TshirtDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, tshirt_id):
        try:
            tshirt = Tshirt.objects.get(id=tshirt_id)
            serializer = TshirtSerializer(tshirt, context={'request': request})
            return Response(serializer.data)
        except Tshirt.DoesNotExist:
            return Response({"error": "T-shirt not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, tshirt_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can update T-shirts"}, status=status.HTTP_403_FORBIDDEN)
        try:
            tshirt = Tshirt.objects.get(id=tshirt_id)
            serializer = TshirtSerializer(tshirt, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Tshirt.DoesNotExist:
            return Response({"error": "T-shirt not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, tshirt_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can delete T-shirts"}, status=status.HTTP_403_FORBIDDEN)
        try:
            tshirt = Tshirt.objects.get(id=tshirt_id)
            tshirt.delete()
            return Response({"message": "T-shirt deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Tshirt.DoesNotExist:
            return Response({"error": "T-shirt not found"}, status=status.HTTP_404_NOT_FOUND)

class TshirtBulkVariantCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, tshirt_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can create variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            tshirt = Tshirt.objects.get(id=tshirt_id)
        except Tshirt.DoesNotExist:
            return Response({"error": "T-shirt not found"}, status=status.HTTP_404_NOT_FOUND)

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
            if variant_form_data:
                variant_data['image'] = variant_form_data

            if not variant_type:
                errors.append({"error": "variant_type is required"})
                continue

            if variant_type == 'color':
                serializer = TshirtColorVariantSerializer(data=variant_data, context={'request': request})
            elif variant_type == 'size':
                serializer = TshirtSizeVariantSerializer(data=variant_data, context={'request': request})
            else:
                errors.append({"error": f"Invalid variant type: {variant_type}"})
                continue

            if serializer.is_valid():
                try:
                    instance = serializer.save(tshirt=tshirt)
                    created_variants.append(serializer.data)
                except ValidationError as e:
                    errors.append({"error": str(e)})
            else:
                errors.append(serializer.errors)

        if errors:
            return Response({"created": created_variants, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(created_variants, status=status.HTTP_201_CREATED)

class TshirtColorVariantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can update variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = TshirtColorVariant.objects.get(id=variant_id)
            serializer = TshirtColorVariantSerializer(variant, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except TshirtColorVariant.DoesNotExist:
            return Response({"error": "Color variant not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can delete variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = TshirtColorVariant.objects.get(id=variant_id)
            variant.delete()
            return Response({"message": "Color variant deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except TshirtColorVariant.DoesNotExist:
            return Response({"error": "Color variant not found"}, status=status.HTTP_404_NOT_FOUND)

class TshirtSizeVariantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can update variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = TshirtSizeVariant.objects.get(id=variant_id)
            serializer = TshirtSizeVariantSerializer(variant, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except TshirtSizeVariant.DoesNotExist:
            return Response({"error": "Size variant not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, variant_id):
        if not request.user.is_staff:
            return Response({"error": "Only admins can delete variants"}, status=status.HTTP_403_FORBIDDEN)
        try:
            variant = TshirtSizeVariant.objects.get(id=variant_id)
            variant.delete()
            return Response({"message": "Size variant deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except TshirtSizeVariant.DoesNotExist:
            return Response({"error": "Size variant not found"}, status=status.HTTP_404_NOT_FOUND)

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


logger = logging.getLogger(__name__)

class GiftOrderCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GiftOrderSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Set the user field to the authenticated user
            serializer.save(user=request.user)
            logger.info(f"Gift order created by user {request.user.username}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Error creating gift order: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GiftOrderListView(ListAPIView):
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

class GiftOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            order = GiftOrder.objects.get(pk=pk)
            if not request.user.is_staff and order.user != request.user:
                logger.warning(f"User {request.user.username} attempted to delete order {pk} without permission")
                return Response(
                    {"detail": "You do not have permission to delete this order."},
                    status=status.HTTP_403_FORBIDDEN
                )
            order.delete()
            logger.info(f"Gift order {pk} deleted by user {request.user.username}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except GiftOrder.DoesNotExist:
            logger.error(f"Gift order {pk} not found for deletion")
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class PrintTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print_types = PrintType.objects.all()
        serializer = PrintTypeSerializer(print_types, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        serializer = PrintTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            print_type = PrintType.objects.get(pk=pk)
        except PrintType.DoesNotExist:
            return Response({"error": "Print type not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PrintTypeSerializer(print_type, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            print_type = PrintType.objects.get(pk=pk)
        except PrintType.DoesNotExist:
            return Response({"error": "Print type not found"}, status=status.HTTP_404_NOT_FOUND)
        print_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PrintSizeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print_sizes = PrintSize.objects.all()
        serializer = PrintSizeSerializer(print_sizes, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        serializer = PrintSizeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            print_size = PrintSize.objects.get(pk=pk)
        except PrintSize.DoesNotExist:
            return Response({"error": "Print size not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PrintSizeSerializer(print_size, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            print_size = PrintSize.objects.get(pk=pk)
        except PrintSize.DoesNotExist:
            return Response({"error": "Print size not found"}, status=status.HTTP_404_NOT_FOUND)
        print_size.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PaperTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        paper_types = PaperType.objects.all()
        serializer = PaperTypeSerializer(paper_types, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        serializer = PaperTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            paper_type = PaperType.objects.get(pk=pk)
        except PaperType.DoesNotExist:
            return Response({"error": "Paper type not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PaperTypeSerializer(paper_type, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            paper_type = PaperType.objects.get(pk=pk)
        except PaperType.DoesNotExist:
            return Response({"error": "Paper type not found"}, status=status.HTTP_404_NOT_FOUND)
        paper_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LaminationTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lamination_types = LaminationType.objects.all()
        serializer = LaminationTypeSerializer(lamination_types, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        serializer = LaminationTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            lamination_type = LaminationType.objects.get(pk=pk)
        except LaminationType.DoesNotExist:
            return Response({"error": "Lamination type not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = LaminationTypeSerializer(lamination_type, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            lamination_type = LaminationType.objects.get(pk=pk)
        except LaminationType.DoesNotExist:
            return Response({"error": "Lamination type not found"}, status=status.HTTP_404_NOT_FOUND)
        lamination_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        if request.user.is_staff:
            orders = DocOrder.objects.all().order_by('-created_at')
        else:
            orders = DocOrder.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            order = DocOrder.objects.get(pk=pk)
            if not request.user.is_staff and order.user != request.user:
                return Response(status=status.HTTP_403_FORBIDDEN)
            order.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DocOrder.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)



class DocumentPrintOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.debug("Raw request data: %s", dict(request.data))
        logger.debug("Raw request files: %s", dict(request.FILES))

        # Prepare data for serializer
        data = {
            'delivery_method': request.data.get('delivery_method'),
            'delivery_charge': request.data.get('delivery_charge', '0'),
            'address': request.data.get('address', ''),
            'document_files': []
        }

        # Parse document_files
        index = 0
        while f'document_files[{index}][file]' in request.FILES:
            file_data = {
                'file': request.FILES.get(f'document_files[{index}][file]'),
                'print_type': request.data.get(f'document_files[{index}][print_type]'),
                'print_size': request.data.get(f'document_files[{index}][print_size]'),
                'quantity': request.data.get(f'document_files[{index}][quantity]', '1'),
                'paper_type': request.data.get(f'document_files[{index}][paper_type]'),
                'lamination': request.data.get(f'document_files[{index}][lamination]') == 'true',
                'lamination_type': request.data.get(f'document_files[{index}][lamination_type]', None)
            }
            data['document_files'].append(file_data)
            index += 1

        if not data['document_files']:
            logger.error("No document files provided in request")
            return Response({"detail": "At least one document file is required."}, status=status.HTTP_400_BAD_REQUEST)

        logger.debug("Processed data for serializer: %s", data)

        serializer = DocumentPrintOrderSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            try:
                order = serializer.save()
                logger.info("Print order saved successfully for user %s with ID %s", request.user.username, order.id)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except serializers.ValidationError as e:
                logger.error("Validation error: %s", str(e))
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error("Unexpected error saving order: %s", str(e))
                return Response({"detail": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.error("Serializer errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DocumentPrintOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            order = DocumentPrintOrder.objects.get(pk=pk)
            if not (request.user.is_staff or request.user.is_superuser or order.user == request.user):
                return Response({"detail": "Not authorized to delete this order."}, status=status.HTTP_403_FORBIDDEN)
            order.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DocumentPrintOrder.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def update_document_print_orders_status(request):
    try:
        order_ids = request.data.get('orderIds', [])
        if not order_ids:
            return JsonResponse({'error': 'No order IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        DocumentPrintOrder.objects.filter(user=request.user, id__in=order_ids).update(status='paid')
        return JsonResponse({'message': 'Document print orders status updated to paid'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error updating document print orders status: {str(e)}")
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def update_document_print_orders_status(request):
    try:
        order_ids = request.data.get('orderIds', [])
        if not order_ids:
            return JsonResponse({'error': 'No order IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        DocumentPrintOrder.objects.filter(user=request.user, id__in=order_ids).update(status='paid')
        return JsonResponse({'message': 'Document print orders status updated to paid'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error updating document print orders status: {str(e)}")
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

