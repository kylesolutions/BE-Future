import json
import logging

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers, status
from rest_framework.response import Response

from CustomFrame_app.models import Login, ColorVariant, SizeVariant, FinishingVariant, Frame, FrameHangVariant, \
    CartItem, FrameCategories, MackBoard, SavedItemMackBoard, SavedItem, Mug, Cap, Tshirt, Tile, Pens, GiftOrder


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


class MackBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = MackBoard
        fields = '__all__'


import logging

logger = logging.getLogger(__name__)

class SavedItemMackBoardSerializer(serializers.ModelSerializer):
    mack_board = serializers.PrimaryKeyRelatedField(queryset=MackBoard.objects.all())

    class Meta:
        model = SavedItemMackBoard
        fields = ['mack_board', 'width', 'color']
        extra_kwargs = {
            'color': {'required': False, 'allow_blank': True},
        }

    def validate_mack_board(self, value):
        logger.debug(f"Validating mack_board: {value}")
        if not MackBoard.objects.filter(id=value.id).exists():
            logger.error(f"MackBoard with id {value.id} does not exist")
            raise serializers.ValidationError("Invalid MackBoard ID")
        return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Include mack_board details in the response
        representation['mack_board'] = {
            'id': instance.mack_board.id,
            'board_name': instance.mack_board.board_name
        }
        return representation

class SavedItemSerializer(serializers.ModelSerializer):
    mack_boards_data = SavedItemMackBoardSerializer(many=True, write_only=True, required=False)
    frame = FrameSerializer(read_only=True)  # Use FrameSerializer for frame
    color_variant = ColorVariantSerializer(read_only=True)
    size_variant = SizeVariantSerializer(read_only=True)
    finish_variant = FinishingVariantSerializer(read_only=True)
    hanging_variant = HangingsVariantSerializer(read_only=True)  # Match field name
    mack_boards = SavedItemMackBoardSerializer(many=True, read_only=True)

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

    def create(self, validated_data):
        mack_boards_data = validated_data.pop('mack_boards_data', [])
        saved_item = super().create(validated_data)
        for mb_data in mack_boards_data:
            SavedItemMackBoard.objects.create(saved_item=saved_item, **mb_data)
        return saved_item

    def update(self, instance, validated_data):
        logger.debug(f"Updating SavedItem {instance.id} with data: {validated_data}")
        mack_boards_data = validated_data.pop('mack_boards_data', None)  # Fix: Use mack_boards_data
        if 'user' not in validated_data:
            validated_data['user'] = instance.user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if mack_boards_data is not None:
            instance.mack_boards.clear()
            for mack_board_data in mack_boards_data:
                logger.debug(f"Updating SavedItemMackBoard: {mack_board_data}")
                SavedItemMackBoard.objects.create(saved_item=instance, **mack_board_data)
        return instance


class TshirtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tshirt
        fields = ['id', 'tshirt_name', 'price', 'image']

class MugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mug
        fields = ['id', 'mug_name', 'price', 'image']

class CapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cap
        fields = ['id', 'cap_name', 'price', 'image']

class TileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tile
        fields = ['id', 'tile_name', 'price', 'image']

class PenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pens
        fields = ['id', 'pen_name', 'price', 'image']

class GiftOrderSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField()

    class Meta:
        model = GiftOrder
        fields = [
            'id', 'user', 'content_type', 'object_id', 'uploaded_image',
            'image_position_x', 'image_position_y', 'image_scale_x',
            'image_scale_y', 'image_rotation', 'total_price', 'created_at', 'status'
        ]
        read_only_fields = ['id', 'user', 'created_at']

    def validate_content_type(self, value):
        valid_models = ['mug', 'tshirt', 'cap', 'tile', 'pen']
        if not value:
            raise serializers.ValidationError("Content type is required.")
        if value.lower() not in valid_models:
            raise serializers.ValidationError(
                f"Invalid content type: '{value}'. Must be one of: {', '.join(valid_models)}"
            )
        try:
            content_type = ContentType.objects.get(model=value.lower())
            return content_type
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(
                f"Content type '{value}' does not exist in the database."
            )

    def validate_object_id(self, value):
        if not value:
            raise serializers.ValidationError("Object ID is required.")
        try:
            value = int(value)
            if value <= 0:
                raise serializers.ValidationError("Object ID must be a positive integer.")
        except (TypeError, ValueError):
            raise serializers.ValidationError("Object ID must be a valid integer.")
        return value

    def validate_total_price(self, value):
        if value is None:
            raise serializers.ValidationError("Total price is required.")
        try:
            value = float(value)
            if value <= 0:
                raise serializers.ValidationError("Total price must be greater than zero.")
        except (TypeError, ValueError):
            raise serializers.ValidationError("Total price must be a valid number.")
        return value

    def validate(self, data):
        content_type = data.get('content_type')
        object_id = data.get('object_id')
        if content_type and object_id:
            try:
                model_class = content_type.model_class()
                if not model_class.objects.filter(id=object_id).exists():
                    raise serializers.ValidationError({
                        'object_id': f"No {content_type.model} found with ID {object_id}."
                    })
            except Exception as e:
                raise serializers.ValidationError({
                    'object_id': f"Error validating object ID: {str(e)}"
                })
        return data

    def create(self, validated_data):
        content_type = validated_data.pop('content_type')
        validated_data['content_type'] = content_type
        return super().create(validated_data)