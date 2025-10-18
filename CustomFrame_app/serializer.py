import json
from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from rest_framework import serializers, status
from rest_framework.response import Response
import logging
from CustomFrame_app.models import Login, ColorVariant, SizeVariant, FinishingVariant, Frame, FrameHangVariant, \
    CartItem, FrameCategories, MackBoard, SavedItem, Mug, Cap, Tshirt, Tile, Pens, \
    MackBoardColorVariant, SavedItemMackBoard, PrintType, PrintSize, PaperType, LaminationType, DocumentPrintOrder, \
    DocumentFile, TshirtColorVariant, TshirtSizeVariant, GiftOrder, DocOrder, OrderFile, Background, Sticker, Theme, \
    PhotoBookPapers, Page, PageElement, PhotoBookOrder, UploadedImage


class UserDetails_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Login
        fields = ['id', 'username', 'is_user', 'is_staff', 'is_employee', 'name', 'email', 'phone', 'is_blocked']

class User_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Login
        fields = ['username', 'password', 'is_user', 'name', 'email', 'phone', 'is_blocked', 'id']

class Employee_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Login
        fields = ['username', 'password', 'is_employee', 'email', 'company_name', 'company_address', 'phone', 'id']

class FrameCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrameCategories
        fields = ['id', 'frameCategory']

class ColorVariantSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    corner_image = serializers.ImageField(required=False, allow_null=True)
    color_name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = ColorVariant
        fields = ['id', 'color_name', 'image', 'corner_image', 'price']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        if instance.corner_image and request:
            representation['corner_image'] = request.build_absolute_uri(instance.corner_image.url)
        return representation

class SizeVariantSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    corner_image = serializers.ImageField(required=False, allow_null=True)
    size_name = serializers.CharField()
    inner_width = serializers.FloatField()
    inner_height = serializers.FloatField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = SizeVariant
        fields = ['id', 'size_name', 'inner_width', 'inner_height', 'image', 'corner_image', 'price']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        if instance.corner_image and request:
            representation['corner_image'] = request.build_absolute_uri(instance.corner_image.url)
        return representation

class FinishingVariantSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    corner_image = serializers.ImageField(required=False, allow_null=True)
    finish_name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = FinishingVariant
        fields = ['id', 'finish_name', 'image', 'corner_image', 'price']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        if instance.corner_image and request:
            representation['corner_image'] = request.build_absolute_uri(instance.corner_image.url)
        return representation

class HangingsVariantSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    hanging_name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = FrameHangVariant
        fields = ['id', 'hanging_name', 'image', 'price']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation

class FrameSerializer(serializers.ModelSerializer):
    color_variants = ColorVariantSerializer(many=True, read_only=True)
    size_variants = SizeVariantSerializer(many=True, read_only=True)
    finishing_variants = FinishingVariantSerializer(many=True, read_only=True)
    frameHanging_variant = HangingsVariantSerializer(many=True, read_only=True)
    image = serializers.ImageField(allow_null=True, required=False)
    corner_image = serializers.ImageField(allow_null=True, required=False)
    created_by = UserDetails_Serializer(read_only=True)
    category = FrameCategoriesSerializer(read_only=True)  # Display category details
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=FrameCategories.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )  # Accept category ID for creation/update

    class Meta:
        model = Frame
        fields = [
            'id', 'name', 'price', 'image', 'corner_image', 'inner_width', 'inner_height',
            'color_variants', 'size_variants', 'finishing_variants',
            'frameHanging_variant', 'created_by', 'created_at', 'category', 'category_id'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        if instance.corner_image and request:
            representation['corner_image'] = request.build_absolute_uri(instance.corner_image.url)
        return representation


class CartItemCreateSerializer(serializers.ModelSerializer):
    frame = serializers.PrimaryKeyRelatedField(queryset=Frame.objects.all())
    color_variant = serializers.PrimaryKeyRelatedField(queryset=ColorVariant.objects.all(), required=False, allow_null=True)
    size_variant = serializers.PrimaryKeyRelatedField(queryset=SizeVariant.objects.all(), required=False, allow_null=True)
    finish_variant = serializers.PrimaryKeyRelatedField(queryset=FinishingVariant.objects.all(), required=False, allow_null=True)
    hanging_variant = serializers.PrimaryKeyRelatedField(queryset=FrameHangVariant.objects.all(), required=False, allow_null=True)
    original_image = serializers.ImageField(required=False, allow_null=True)
    cropped_image = serializers.ImageField(required=False, allow_null=True)
    adjusted_image = serializers.ImageField(required=False, allow_null=True)
    transform_x = serializers.FloatField(default=0)
    transform_y = serializers.FloatField(default=0)
    scale = serializers.FloatField(default=1)
    rotation = serializers.FloatField(default=0)
    frame_rotation = serializers.FloatField(default=0)

    class Meta:
        model = CartItem
        fields = ['frame', 'original_image', 'cropped_image', 'adjusted_image', 'color_variant', 'size_variant', 'finish_variant', 'hanging_variant', 'quantity', 'transform_x', 'transform_y', 'scale', 'rotation', 'frame_rotation']

    def validate(self, data):
        if not self.instance and (not data.get('original_image') or not data.get('adjusted_image')):
            raise serializers.ValidationError("Both original and adjusted images are required.")
        frame = data.get('frame')
        for variant_type in ['color_variant', 'size_variant', 'finish_variant', 'hanging_variant']:
            variant = data.get(variant_type)
            if variant and variant.frame != frame:
                raise serializers.ValidationError(f"{variant_type} does not belong to the selected frame")
        return data

class CartItemUpdateSerializer(serializers.ModelSerializer):
    frame = serializers.PrimaryKeyRelatedField(queryset=Frame.objects.all())
    color_variant = serializers.PrimaryKeyRelatedField(queryset=ColorVariant.objects.all(), required=False, allow_null=True)
    size_variant = serializers.PrimaryKeyRelatedField(queryset=SizeVariant.objects.all(), required=False, allow_null=True)
    finish_variant = serializers.PrimaryKeyRelatedField(queryset=FinishingVariant.objects.all(), required=False, allow_null=True)
    hanging_variant = serializers.PrimaryKeyRelatedField(queryset=FrameHangVariant.objects.all(), required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)
    adjusted_image = serializers.ImageField(required=False, allow_null=True)
    transform_x = serializers.FloatField(default=0)
    transform_y = serializers.FloatField(default=0)
    scale = serializers.FloatField(default=1)
    rotation = serializers.FloatField(default=0)
    frame_rotation = serializers.FloatField(default=0)

    class Meta:
        model = CartItem
        fields = ['frame', 'color_variant', 'size_variant', 'finish_variant', 'hanging_variant', 'quantity', 'adjusted_image', 'transform_x', 'transform_y', 'scale', 'rotation', 'frame_rotation']

    def validate(self, data):
        frame = data.get('frame', self.instance.frame)
        for variant_type in ['color_variant', 'size_variant', 'finish_variant', 'hanging_variant']:
            variant = data.get(variant_type, getattr(self.instance, variant_type, None))
            if variant and variant.frame != frame:
                raise serializers.ValidationError(f"{variant_type} does not belong to the selected frame")
        return data

    def update(self, instance, validated_data):
        if 'adjusted_image' in validated_data:
            adjusted_image = validated_data.pop('adjusted_image')
            if instance.adjusted_image:
                instance.adjusted_image.delete()
            file_path = f"cart/adjusted/{adjusted_image.name}"
            saved_path = instance.adjusted_image.storage.save(file_path, adjusted_image)
            instance.adjusted_image = saved_path
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class CartItemSerializer(serializers.ModelSerializer):
    frame = FrameSerializer()
    color_variant = ColorVariantSerializer(allow_null=True)
    size_variant = SizeVariantSerializer(allow_null=True)
    finish_variant = FinishingVariantSerializer(allow_null=True)
    hanging_variant = HangingsVariantSerializer(allow_null=True)
    original_image = serializers.SerializerMethodField()
    cropped_image = serializers.SerializerMethodField()
    adjusted_image = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'frame', 'original_image', 'cropped_image', 'adjusted_image', 'color_variant', 'size_variant', 'finish_variant', 'hanging_variant', 'quantity', 'total_price', 'transform_x', 'transform_y', 'scale', 'rotation', 'frame_rotation']

    def get_original_image(self, obj):
        if obj.original_image:
            return self.context['request'].build_absolute_uri(obj.original_image.url)
        return None

    def get_cropped_image(self, obj):
        if obj.cropped_image:
            return self.context['request'].build_absolute_uri(obj.cropped_image.url)
        return None

    def get_adjusted_image(self, obj):
        if obj.adjusted_image:
            return self.context['request'].build_absolute_uri(obj.adjusted_image.url)
        return None

class MackBoardColorVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = MackBoardColorVariant
        fields = ['id', 'mack_board', 'color_name', 'image']

class MackBoardSerializer(serializers.ModelSerializer):
    color_variants = MackBoardColorVariantSerializer(many=True, read_only=True)
    class Meta:
        model = MackBoard
        fields = ['id', 'board_name', 'image', 'price', 'color_variants']


logger = logging.getLogger(__name__)

class SavedItemMackBoardSerializer(serializers.ModelSerializer):
    mack_board = MackBoardSerializer(read_only=True)
    mack_board_id = serializers.PrimaryKeyRelatedField(
        queryset=MackBoard.objects.all(), source='mack_board', write_only=True, required=False, allow_null=True
    )
    mack_board_color = MackBoardColorVariantSerializer(read_only=True)
    mack_board_color_id = serializers.PrimaryKeyRelatedField(
        queryset=MackBoardColorVariant.objects.all(), source='mack_board_color', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = SavedItemMackBoard
        fields = ['id', 'mack_board', 'mack_board_id', 'mack_board_color', 'mack_board_color_id', 'width', 'position']

    def validate_mack_board(self, value):
        if value and not MackBoard.objects.filter(id=value.id).exists():
            logger.error(f"MackBoard with id {value.id} does not exist")
            raise serializers.ValidationError("Invalid MackBoard ID")
        return value

    def validate_mack_board_color(self, value):
        if value and not MackBoardColorVariant.objects.filter(id=value.id).exists():
            logger.error(f"MackBoardColorVariant with id {value.id} does not exist")
            raise serializers.ValidationError("Invalid MackBoardColorVariant ID")
        return value

class SavedItemSerializer(serializers.ModelSerializer):
    frame = FrameSerializer(read_only=True)
    frame_id = serializers.PrimaryKeyRelatedField(
        queryset=Frame.objects.all(), source='frame', write_only=True, required=False, allow_null=True
    )
    color_variant = ColorVariantSerializer(read_only=True)
    color_variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ColorVariant.objects.all(), source='color_variant', write_only=True, required=False, allow_null=True
    )
    size_variant = SizeVariantSerializer(read_only=True)
    size_variant_id = serializers.PrimaryKeyRelatedField(
        queryset=SizeVariant.objects.all(), source='size_variant', write_only=True, required=False, allow_null=True
    )
    finish_variant = FinishingVariantSerializer(read_only=True)
    finish_variant_id = serializers.PrimaryKeyRelatedField(
        queryset=FinishingVariant.objects.all(), source='finish_variant', write_only=True, required=False, allow_null=True
    )
    hanging_variant = HangingsVariantSerializer(read_only=True)
    hanging_variant_id = serializers.PrimaryKeyRelatedField(
        queryset=FrameHangVariant.objects.all(), source='hanging_variant', write_only=True, required=False, allow_null=True
    )
    mack_boards = SavedItemMackBoardSerializer(many=True, read_only=True)
    mack_boards_data = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = SavedItem
        fields = '__all__'
        extra_kwargs = {
            'frame': {'required': False},
            'color_variant': {'required': False},
            'size_variant': {'required': False},
            'finish_variant': {'required': False},
            'hanging_variant': {'required': False},
        }

    def validate_mack_boards_data(self, value):
        if not value:
            return []
        try:
            data = json.loads(value)
            if not isinstance(data, list):
                raise serializers.ValidationError("mack_boards_data must be a list of dictionaries")
            for item in data:
                if not isinstance(item, dict):
                    raise serializers.ValidationError("Each item in mack_boards_data must be a dictionary")
                if 'mack_board_id' in item and item['mack_board_id'] is not None:
                    if not MackBoard.objects.filter(id=item['mack_board_id']).exists():
                        raise serializers.ValidationError(f"Invalid MackBoard ID: {item['mack_board_id']}")
                if 'mack_board_color_id' in item and item['mack_board_color_id'] is not None:
                    if not MackBoardColorVariant.objects.filter(id=item['mack_board_color_id']).exists():
                        raise serializers.ValidationError(f"Invalid MackBoardColorVariant ID: {item['mack_board_color_id']}")
            return data
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in mack_boards_data: {value}")
            raise serializers.ValidationError("mack_boards_data must be a valid JSON string representing a list of dictionaries")

    def create(self, validated_data):
        logger.debug(f"Creating SavedItem with data: {validated_data}")
        mack_boards_data = validated_data.pop('mack_boards_data', [])
        instance = super().create(validated_data)

        # Create associated MackBoards
        for index, mack_board_data in enumerate(mack_boards_data):
            SavedItemMackBoard.objects.create(
                saved_item=instance,
                mack_board=MackBoard.objects.get(id=mack_board_data['mack_board_id']) if mack_board_data.get('mack_board_id') else None,
                mack_board_color=MackBoardColorVariant.objects.get(id=mack_board_data['mack_board_color_id']) if mack_board_data.get('mack_board_color_id') else None,
                width=mack_board_data.get('width', 20),
                position=index
            )

        return instance

    def update(self, instance, validated_data):
        logger.debug(f"Updating SavedItem {instance.id} with data: {validated_data}")
        mack_boards_data = validated_data.pop('mack_boards_data', None)

        if 'user' not in validated_data:
            validated_data['user'] = instance.user

        # Update the SavedItem instance
        instance = super().update(instance, validated_data)

        # Update MackBoards if provided
        if mack_boards_data is not None:
            # Delete existing MackBoards
            instance.mack_boards.all().delete()
            # Create new MackBoards
            for index, mack_board_data in enumerate(mack_boards_data):
                SavedItemMackBoard.objects.create(
                    saved_item=instance,
                    mack_board=MackBoard.objects.get(id=mack_board_data['mack_board_id']) if mack_board_data.get('mack_board_id') else None,
                    mack_board_color=MackBoardColorVariant.objects.get(id=mack_board_data['mack_board_color_id']) if mack_board_data.get('mack_board_color_id') else None,
                    width=mack_board_data.get('width', 20),
                    position=index
                )
        return instance

class MugSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True, required=False)
    image_url = serializers.SerializerMethodField()
    glb_file = serializers.FileField(allow_null=True, required=False)
    glb_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Mug
        fields = ['id', 'mug_name', 'price', 'image', 'image_url', 'glb_file', 'glb_file_url']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f"{settings.MEDIA_URL}{obj.image}")
            return f"http://localhost:8000{settings.MEDIA_URL}{obj.image}"
        return None

    def get_glb_file_url(self, obj):
        if obj.glb_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f"{settings.MEDIA_URL}{obj.glb_file}")
            return f"http://localhost:8000{settings.MEDIA_URL}{obj.glb_file}"
        return None

class CapSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True, required=False)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Cap
        fields = ['id', 'cap_name', 'price', 'image', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return f"{settings.MEDIA_URL}{obj.image}"
        return None

class TshirtColorVariantSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    color_name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = TshirtColorVariant
        fields = ['id', 'color_name', 'image', 'price']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation

class TshirtSizeVariantSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    size_name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = TshirtSizeVariant
        fields = ['id', 'size_name', 'image', 'price']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation

class TshirtSerializer(serializers.ModelSerializer):
    color_variants = TshirtColorVariantSerializer(many=True, read_only=True)
    size_variants = TshirtSizeVariantSerializer(many=True, read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Tshirt
        fields = ['id', 'tshirt_name', 'image', 'color_variants', 'size_variants','created_by']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation


class TileSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True, required=False)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Tile
        fields = ['id', 'tile_name', 'price', 'image', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return f"{settings.MEDIA_URL}{obj.image}"
        return None

class PenSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True, required=False)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Pens
        fields = ['id', 'pen_name', 'price', 'image', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return f"{settings.MEDIA_URL}{obj.image}"
        return None

class GiftOrderSerializer(serializers.ModelSerializer):
    tshirt = serializers.PrimaryKeyRelatedField(queryset=Tshirt.objects.all(), required=False, allow_null=True)
    mug = serializers.PrimaryKeyRelatedField(queryset=Mug.objects.all(), required=False, allow_null=True)
    cap = serializers.PrimaryKeyRelatedField(queryset=Cap.objects.all(), required=False, allow_null=True)
    tile = serializers.PrimaryKeyRelatedField(queryset=Tile.objects.all(), required=False, allow_null=True)
    pen = serializers.PrimaryKeyRelatedField(queryset=Pens.objects.all(), required=False, allow_null=True)
    tshirt_color_variant = serializers.PrimaryKeyRelatedField(
        queryset=TshirtColorVariant.objects.all(), required=False, allow_null=True
    )
    tshirt_size_variant = serializers.PrimaryKeyRelatedField(
        queryset=TshirtSizeVariant.objects.all(), required=False, allow_null=True
    )
    uploaded_image = serializers.ImageField(required=True)
    preview_image = serializers.ImageField(required=True)
    content_type = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()  # New field for item name
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = GiftOrder
        fields = [
            'id', 'user', 'tshirt', 'mug', 'cap', 'tile', 'pen',
            'tshirt_color_variant', 'tshirt_size_variant',
            'total_price', 'uploaded_image', 'preview_image',
            'image_position_x', 'image_position_y',
            'image_scale_x', 'image_scale_y', 'image_rotation',
            'status', 'content_type', 'object_name', 'created_at'
        ]
        read_only_fields = ['user', 'created_at', 'content_type', 'object_name']

    def get_content_type(self, obj):
        if obj.tshirt:
            return 'T-shirt'
        elif obj.mug:
            return 'Mug'
        elif obj.cap:
            return 'Cap'
        elif obj.tile:
            return 'Tile'
        elif obj.pen:
            return 'Pen'
        return 'Unknown'

    def get_object_name(self, obj):
        if obj.tshirt:
            return obj.tshirt.tshirt_name
        elif obj.mug:
            return obj.mug.mug_name
        elif obj.cap:
            return obj.cap.cap_name
        elif obj.tile:
            return obj.tile.tile_name
        elif obj.pen:
            return obj.pen.pen_name
        return 'Unknown'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        # Convert image paths to full URLs
        for field in ['uploaded_image', 'preview_image']:
            if representation.get(field) and request:
                representation[field] = request.build_absolute_uri(representation[field])
        return representation

    def validate(self, data):
        gift_types = [data.get('tshirt'), data.get('mug'), data.get('cap'), data.get('tile'), data.get('pen')]
        non_null_gifts = [gt for gt in gift_types if gt is not None]
        if len(non_null_gifts) != 1:
            raise serializers.ValidationError("Exactly one gift type (tshirt, mug, cap, tile, or pen) must be specified.")
        if data.get('tshirt'):
            if not data.get('tshirt_color_variant') or not data.get('tshirt_size_variant'):
                raise serializers.ValidationError("T-shirt orders require both color and size variants.")
            if data.get('tshirt_color_variant').tshirt != data.get('tshirt'):
                raise serializers.ValidationError("T-shirt color variant must belong to the selected T-shirt.")
            if data.get('tshirt_size_variant').tshirt != data.get('tshirt'):
                raise serializers.ValidationError("T-shirt size variant must belong to the selected T-shirt.")
        else:
            if data.get('tshirt_color_variant') or data.get('tshirt_size_variant'):
                raise serializers.ValidationError("Non-T-shirt orders cannot have T-shirt variants.")
        return data


class PrintTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintType
        fields = ['id', 'name', 'price']

    def validate_name(self, value):
        if PrintType.objects.filter(name=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Print type with this name already exists.")
        return value


class PrintSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintSize
        fields = ['id', 'name', 'price']

    def validate_name(self, value):
        if PrintSize.objects.filter(name=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Print size with this name already exists.")
        return value


class PaperTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperType
        fields = ['id', 'name', 'price']

    def validate_name(self, value):
        if PaperType.objects.filter(name=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Paper type with this name already exists.")
        return value


class LaminationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaminationType
        fields = ['id', 'name', 'price']

    def validate_name(self, value):
        if LaminationType.objects.filter(name=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Lamination type with this name already exists.")
        return value

class OrderFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderFile
        fields = ['id', 'file', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        min_length=1,
        allow_empty=False,
        write_only=True
    )
    files_data = OrderFileSerializer(source='files', many=True, read_only=True)
    total_amount = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    user = serializers.CharField(source='user.username', read_only=True)
    print_type_name = serializers.SerializerMethodField()
    print_size_name = serializers.SerializerMethodField()
    paper_type_name = serializers.SerializerMethodField()
    lamination_type_name = serializers.SerializerMethodField()

    class Meta:
        model = DocOrder
        fields = [
            'id', 'user', 'print_type', 'print_type_name', 'print_size', 'print_size_name',
            'paper_type', 'paper_type_name', 'lamination', 'lamination_type', 'lamination_type_name',
            'delivery_option', 'address_city', 'address_pin', 'address_house_name',
            'quantity', 'total_amount', 'created_at', 'files', 'files_data', 'status'
        ]
        read_only_fields = ['id', 'created_at', 'total_amount', 'files_data', 'user']

    def get_print_type_name(self, obj):
        return obj.print_type.name if obj.print_type else 'N/A'

    def get_print_size_name(self, obj):
        return obj.print_size.name if obj.print_size else 'N/A'

    def get_paper_type_name(self, obj):
        return obj.paper_type.name if obj.paper_type else 'N/A'

    def get_lamination_type_name(self, obj):
        return obj.lamination_type.name if obj.lamination_type else 'N/A'

    def validate(self, data):
        if data['delivery_option'] == 'delivery':
            if not all([data.get('address_city'), data.get('address_pin'), data.get('address_house_name')]):
                raise serializers.ValidationError("All address fields are required for delivery")
        if data['lamination'] and not data.get('lamination_type'):
            raise serializers.ValidationError("Lamination type is required when lamination is selected")
        return data

    def create(self, validated_data):
        files = validated_data.pop('files')
        total_amount = self.calculate_total_amount(validated_data)
        validated_data['total_amount'] = total_amount
        validated_data['user'] = self.context['request'].user
        order = DocOrder.objects.create(**validated_data)
        for file in files:
            OrderFile.objects.create(order=order, file=file)
        return order

    def calculate_total_amount(self, data):
        total = Decimal('0')
        print_type = data['print_type']
        print_size = data['print_size']
        paper_type = data['paper_type']
        total += print_type.price + print_size.price + paper_type.price
        if data['lamination'] and data.get('lamination_type'):
            lamination_type = data['lamination_type']
            total += lamination_type.price
        if data['delivery_option'] == 'delivery':
            total += Decimal('5.00')  # Delivery charge
        total *= Decimal(data['quantity'])
        return total


logger = logging.getLogger(__name__)

class DocumentFileSerializer(serializers.ModelSerializer):
    print_type = serializers.PrimaryKeyRelatedField(queryset=PrintType.objects.all())
    print_size = serializers.PrimaryKeyRelatedField(queryset=PrintSize.objects.all())
    paper_type = serializers.PrimaryKeyRelatedField(queryset=PaperType.objects.all())
    lamination_type = serializers.PrimaryKeyRelatedField(queryset=LaminationType.objects.all(), allow_null=True)
    file = serializers.FileField()

    class Meta:
        model = DocumentFile
        fields = ['file', 'print_type', 'print_size', 'quantity', 'paper_type', 'lamination', 'lamination_type']

    def validate(self, data):
        # Ensure lamination_type is provided if lamination is True
        if data.get('lamination') and not data.get('lamination_type'):
            raise serializers.ValidationError({"lamination_type": "Lamination type is required when lamination is enabled."})
        return data

class DocumentPrintOrderSerializer(serializers.ModelSerializer):
    document_files = DocumentFileSerializer(many=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = DocumentPrintOrder
        fields = ['user', 'delivery_method', 'delivery_charge', 'address', 'document_files', 'total_price', 'status']
        read_only_fields = ['user', 'total_price', 'status']

    def validate(self, data):
        # Ensure at least one document file is provided
        if not data.get('document_files'):
            raise serializers.ValidationError({"document_files": "At least one document file is required."})
        # Validate delivery_method and address
        if data.get('delivery_method') == 'Delivery' and not data.get('address'):
            raise serializers.ValidationError({"address": "Delivery address is required for delivery method."})
        return data

    def create(self, validated_data):
        logger.debug("Validated data: %s", validated_data)
        document_files_data = validated_data.pop('document_files', [])
        validated_data['user'] = self.context['request'].user
        logger.debug("Creating DocumentPrintOrder with data: %s", validated_data)
        try:
            with transaction.atomic():
                order = DocumentPrintOrder.objects.create(**validated_data)
                logger.debug("Created order with ID: %s", order.id)
                for file_data in document_files_data:
                    logger.debug("Creating DocumentFile with data: %s", file_data)
                    DocumentFile.objects.create(order=order, **file_data)
                logger.debug("Calculating total_price for order ID: %s", order.id)
                order.total_price = order.calculate_total_price()
                order.save()
                logger.debug("Final total_price: %s", order.total_price)
                return order
        except Exception as e:
            logger.error("Error creating order: %s", str(e))
            raise serializers.ValidationError({"detail": f"Failed to save order: {str(e)}"})

class BackgroundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Background
        fields = ['id', 'theme', 'name', 'image', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class StickerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sticker
        fields = ['id', 'theme', 'name', 'image', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ThemeSerializer(serializers.ModelSerializer):
    backgrounds = BackgroundSerializer(many=True, read_only=True)
    stickers = StickerSerializer(many=True, read_only=True)

    class Meta:
        model = Theme
        fields = ['id', 'theme_name', 'backgrounds', 'stickers', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class PhotoBookPapersSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoBookPapers
        fields = ['id', 'size', 'image', 'price', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class UploadedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedImage
        fields = ['id', 'image']

class PageElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageElement
        fields = ['id', 'type', 'content', 'x', 'y', 'width', 'height', 'rotation', 'z_index']

class PageSerializer(serializers.ModelSerializer):
    elements = PageElementSerializer(many=True)
    preview_image = serializers.SerializerMethodField()
    background = serializers.SerializerMethodField()
    client_page_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Page
        fields = ['id', 'page_number', 'background', 'preview_image', 'elements', 'client_page_id']

    def get_preview_image(self, obj):
        request = self.context.get('request')
        if obj.preview_image and hasattr(obj.preview_image, 'url') and request:
            logger.info(f"Serializing preview_image for page {obj.id}: {obj.preview_image.url}")
            return request.build_absolute_uri(obj.preview_image.url)
        logger.warning(f"No preview_image for page {obj.id}")
        return None

    def get_background(self, obj):
        if obj.background:
            request = self.context.get('request')
            return {
                'id': obj.background.id,
                'name': obj.background.name,
                'image': request.build_absolute_uri(obj.background.image.url) if request and obj.background.image else None
            }
        return None

class PhotoBookOrderSerializer(serializers.ModelSerializer):
    pages = PageSerializer(many=True, required=False)
    theme = ThemeSerializer(read_only=True)
    paper = PhotoBookPapersSerializer(read_only=True)
    page_previews = serializers.DictField(child=serializers.FileField(), write_only=True, required=False)

    class Meta:
        model = PhotoBookOrder
        fields = ['id', 'user', 'theme', 'paper', 'total_price', 'created_at', 'updated_at', 'pages', 'page_previews']

    def validate(self, data):
        pages = data.get('pages', [])
        page_previews = data.get('page_previews', {})
        client_page_ids = {page['client_page_id'] for page in pages if 'client_page_id' in page}
        for page_id in page_previews.keys():
            if page_id not in client_page_ids:
                raise serializers.ValidationError(f"Invalid client_page_id in page_previews: {page_id}")
        return data
