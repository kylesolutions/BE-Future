import json
import logging

from rest_framework import serializers
from CustomFrame_app.models import Login, ColorVariant, SizeVariant, FinishingVariant, Frame, FrameHangVariant, \
    CartItem, FrameCategories, MackBoard, SavedItemMackBoard, SavedItem


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

logger = logging.getLogger(__name__)

class SavedItemMackBoardSerializer(serializers.ModelSerializer):
    mack_board = MackBoardSerializer(read_only=True)
    mack_board_id = serializers.PrimaryKeyRelatedField(
        queryset=MackBoard.objects.all(),
        source='mack_board',
        write_only=True,
        required=True
    )
    width = serializers.IntegerField(min_value=0, default=20, required=False)

    class Meta:
        model = SavedItemMackBoard
        fields = ['mack_board', 'mack_board_id', 'width']

    def validate(self, attrs):
        logger.debug(f"SavedItemMackBoardSerializer attrs: {attrs}")
        return attrs

class SavedItemSerializer(serializers.ModelSerializer):
    frame = serializers.PrimaryKeyRelatedField(queryset=Frame.objects.all(), allow_null=True)
    mack_boards = SavedItemMackBoardSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = SavedItem
        fields = [
            'id', 'user', 'original_image', 'cropped_image', 'adjusted_image', 'frame',
            'color_variant', 'size_variant', 'finish_variant', 'hanging_variant',
            'print_width', 'print_height', 'print_unit', 'media_type', 'paper_type',
            'fit', 'border_depth', 'border_color', 'border_unit','status',
            'frame_depth', 'custom_frame_color', 'custom_width', 'custom_height',
            'transform_x', 'transform_y', 'scale', 'rotation', 'total_price', 'mack_boards',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate_mack_boards(self, value):
        logger.debug(f"Raw mack_boards value: {value}")
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format for mack_boards")
        if value is None or value == []:
            return []
        for item in value:
            if not item.get('mack_board_id'):
                raise serializers.ValidationError({"mack_board_id": "This field is required."})
        return value

    def create(self, validated_data):
        mack_boards_data = validated_data.pop('mack_boards', [])
        logger.debug(f"Creating with mack_boards_data: {mack_boards_data}")
        saved_item = SavedItem.objects.create(user=self.context['request'].user, **validated_data)
        for mb_data in mack_boards_data:
            SavedItemMackBoard.objects.create(saved_item=saved_item, **mb_data)
        return saved_item

    def update(self, instance, validated_data):
        mack_boards_data = validated_data.pop('mack_boards', None)
        logger.debug(f"Updating with mack_boards_data: {mack_boards_data}")
        instance = super().update(instance, validated_data)
        if mack_boards_data is not None:
            instance.saveditemmackboard_set.all().delete()
            for mb_data in mack_boards_data:
                SavedItemMackBoard.objects.create(saved_item=instance, **mb_data)
        return instance

