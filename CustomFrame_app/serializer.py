import json
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers, status
from rest_framework.response import Response
import logging
from CustomFrame_app.models import Login, ColorVariant, SizeVariant, FinishingVariant, Frame, FrameHangVariant, \
    CartItem, FrameCategories, MackBoard, SavedItem, Mug, Cap, Tshirt, Tile, Pens, GiftOrder, \
    MackBoardColorVariant, SavedItemMackBoard, PrintType, PrintSize, PaperType, LaminationType, DocumentPrintOrder


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

    class Meta:
        model = Mug
        fields = ['id', 'mug_name', 'price', 'image', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return f"{settings.MEDIA_URL}{obj.image}"
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

class TshirtSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True, required=False)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Tshirt
        fields = ['id', 'tshirt_name', 'price', 'image', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return f"{settings.MEDIA_URL}{obj.image}"
        return None

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
    content_type = serializers.CharField()
    uploaded_image = serializers.ImageField()
    preview_image = serializers.ImageField(required=True)
    size = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = GiftOrder
        fields = [
            'id', 'user', 'content_type', 'object_id', 'uploaded_image',
            'preview_image', 'size', 'image_position_x', 'image_position_y',
            'image_scale_x', 'image_scale_y', 'image_rotation',
            'total_price', 'created_at', 'status'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'status']

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

    def validate_size(self, value):
        valid_sizes = ['S', 'M', 'L', 'XL', 'XXL']
        if value and value not in valid_sizes:
            raise serializers.ValidationError(
                f"Invalid T-shirt size: '{value}'. Must be one of: {', '.join(valid_sizes)}"
            )
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
        logger.debug("Serializer input data: %s", data)
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

        if not data.get('uploaded_image'):
            raise serializers.ValidationError({"uploaded_image": "An image is required."})
        if not data.get('preview_image'):
            raise serializers.ValidationError({"preview_image": "A preview image is required."})
        if data.get('content_type') and data.get('content_type').model.lower() == 'tshirt' and not data.get('size', '').strip():
            raise serializers.ValidationError({"size": "T-shirt size is required for T-shirt orders."})

        return data

    def create(self, validated_data):
        content_type = validated_data.pop('content_type')
        validated_data['content_type'] = content_type
        return super().create(validated_data)


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

class DocumentPrintOrderSerializer(serializers.ModelSerializer):
    file = serializers.FileField()
    print_type = serializers.PrimaryKeyRelatedField(queryset=PrintType.objects.all(), allow_null=False)
    print_size = serializers.PrimaryKeyRelatedField(queryset=PrintSize.objects.all(), allow_null=False)
    paper_type = serializers.PrimaryKeyRelatedField(queryset=PaperType.objects.all(), allow_null=False)
    lamination_type = serializers.PrimaryKeyRelatedField(queryset=LaminationType.objects.all(), allow_null=True, required=False)
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    print_type_name = serializers.CharField(source='print_type.name', read_only=True)
    print_size_name = serializers.CharField(source='print_size.name', read_only=True)
    paper_type_name = serializers.CharField(source='paper_type.name', read_only=True)
    lamination_type_name = serializers.CharField(source='lamination_type.name', read_only=True, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = DocumentPrintOrder
        fields = [
            'id', 'file', 'print_type', 'print_size', 'quantity', 'paper_type',
            'delivery_method', 'delivery_charge', 'address', 'lamination', 'lamination_type',
            'total_price', 'created_at', 'status', 'username', 'user_id',
            'print_type_name', 'print_size_name', 'paper_type_name', 'lamination_type_name'
        ]
        read_only_fields = [
            'id', 'total_price', 'created_at', 'status', 'username', 'user_id',
            'print_type_name', 'print_size_name', 'paper_type_name', 'lamination_type_name'
        ]

    def validate(self, data):
        logger.debug("Serializer input data: %s", data)
        if not data.get('file'):
            raise serializers.ValidationError({"file": "A file is required."})
        if data.get('quantity', 0) < 1:
            raise serializers.ValidationError({"quantity": "Quantity must be at least 1."})
        if data.get('delivery_method') == 'Delivery' and not data.get('address', '').strip():
            raise serializers.ValidationError({"address": "Delivery address is required for delivery method."})
        if 'lamination_type' in data and (data['lamination_type'] == '' or data['lamination_type'] is None):
            data['lamination_type'] = None
            logger.debug("Converted lamination_type to None")
        return data