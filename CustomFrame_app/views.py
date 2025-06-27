import os

from django.conf import settings
from django.core.files.storage import default_storage, FileSystemStorage
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from rest_framework import status, generics, views, serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from CustomFrame_app.forms import UserRegister
from CustomFrame_app.models import Frame, Login, ColorVariant, SizeVariant, FinishingVariant, FrameHangVariant, Cart, \
    CartItem
from CustomFrame_app.serializer import (
    FrameSerializer, ColorVariantSerializer, SizeVariantSerializer,
    FinishingVariantSerializer, HangingsVariantSerializer, UserDetails_Serializer, CartItemCreateSerializer,
    CartItemSerializer, CartItemUpdateSerializer
)
import json

def index(request):
    return HttpResponse("Welcome to the Custom Photo Frame App!")

@csrf_exempt
def user_registration(request):
    result_data = None
    if request.method == 'POST':
        form = UserRegister(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.is_active = True
            form.is_user = True
            form.save()
            result_data = True
    try:
        if result_data:
            data = {'result': True}
        else:
            error_dict = {i: form.errors[i][0] for i in form.errors}
            data = {'result': False, 'errors': error_dict}
    except:
        data = {'result': False}
    return JsonResponse(data, safe=False)

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

class FrameListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        frames = Frame.objects.all()
        serializer = FrameSerializer(frames, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Only admins can create frames"}, status=status.HTTP_403_FORBIDDEN)
        serializer = FrameSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            serializer = FrameSerializer(frame, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
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
            if variant_form_data:
                variant_data['image'] = variant_form_data

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
            color_variant = serializer.validated_data.get('color_variant')
            if color_variant and color_variant.frame != frame:
                return Response({"error": "Color variant does not belong to the selected frame"},
                                status=status.HTTP_400_BAD_REQUEST)

            size_variant = serializer.validated_data.get('size_variant')
            if size_variant and size_variant.frame != frame:
                return Response({"error": "Size variant does not belong to the selected frame"},
                                status=status.HTTP_400_BAD_REQUEST)

            finish_variant = serializer.validated_data.get('finish_variant')
            if finish_variant and finish_variant.frame != frame:
                return Response({"error": "Finish variant does not belong to the selected frame"},
                                status=status.HTTP_400_BAD_REQUEST)

            hanging_variant = serializer.validated_data.get('hanging_variant')
            if hanging_variant and hanging_variant.frame != frame:
                return Response({"error": "Hanging variant does not belong to the selected frame"},
                                status=status.HTTP_400_BAD_REQUEST)

            cart_item = serializer.save(cart=cart)
            return Response({"message": "Item added to cart successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            serializer = CartItemCreateSerializer(cart_item, data=request.data, partial=True)
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
class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return CartItemUpdateSerializer
        return CartItemSerializer

    def get_queryset(self):
        return self.queryset.filter(user_cart=self.request.user_id)


