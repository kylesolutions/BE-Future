from rest_framework import serializers
from CustomFrame_app.models import Login, ColorVariant, SizeVariant, FinishingVariant, Frame, FrameHangVariant, CartItem


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

class ColorVariantSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    color_name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)  # Add price field

    class Meta:
        model = ColorVariant
        fields = ['id', 'color_name', 'image', 'price']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation

class SizeVariantSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    size_name = serializers.CharField()
    inner_width = serializers.FloatField()
    inner_height = serializers.FloatField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)  # Add price field

    class Meta:
        model = SizeVariant
        fields = ['id', 'size_name', 'inner_width', 'inner_height', 'image', 'price']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation

class FinishingVariantSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    finish_name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)  # Add price field

    class Meta:
        model = FinishingVariant
        fields = ['id', 'finish_name', 'image', 'price']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation

class HangingsVariantSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    hanging_name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)  # Add price field

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
    image = serializers.ImageField()
    created_by = UserDetails_Serializer(read_only=True)

    class Meta:
        model = Frame
        fields = [
            'id', 'name', 'price', 'image', 'inner_width', 'inner_height',
            'color_variants', 'size_variants', 'finishing_variants',
            'frameHanging_variant', 'created_by'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation

class CartItemCreateSerializer(serializers.ModelSerializer):
    frame = serializers.PrimaryKeyRelatedField(queryset=Frame.objects.all())
    color_variant = serializers.PrimaryKeyRelatedField(queryset=ColorVariant.objects.all(), required=False, allow_null=True)
    size_variant = serializers.PrimaryKeyRelatedField(queryset=SizeVariant.objects.all(), required=False, allow_null=True)
    finish_variant = serializers.PrimaryKeyRelatedField(queryset=FinishingVariant.objects.all(), required=False, allow_null=True)
    hanging_variant = serializers.PrimaryKeyRelatedField(queryset=FrameHangVariant.objects.all(), required=False, allow_null=True)
    original_image = serializers.ImageField(required=False, allow_null=True)
    cropped_image = serializers.ImageField(required=False, allow_null=True)  # New field
    adjusted_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = CartItem
        fields = ['frame', 'original_image', 'cropped_image', 'adjusted_image', 'color_variant', 'size_variant', 'finish_variant', 'hanging_variant', 'quantity']

    def validate(self, data):
        if not self.instance and (not data.get('original_image') or not data.get('adjusted_image')):
            raise serializers.ValidationError("Both original and adjusted images are required.")
        return data

class CartItemSerializer(serializers.ModelSerializer):
    frame = FrameSerializer()
    color_variant = ColorVariantSerializer(allow_null=True)
    size_variant = SizeVariantSerializer(allow_null=True)
    finish_variant = FinishingVariantSerializer(allow_null=True)
    hanging_variant = HangingsVariantSerializer(allow_null=True)
    original_image = serializers.SerializerMethodField()
    cropped_image = serializers.SerializerMethodField()  # New field
    adjusted_image = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'frame', 'original_image', 'cropped_image', 'adjusted_image', 'color_variant', 'size_variant', 'finish_variant', 'hanging_variant', 'quantity', 'total_price']

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

class CartItemUpdateSerializer(serializers.ModelSerializer):
    frame = serializers.PrimaryKeyRelatedField(queryset=Frame.objects.all())
    color_variant = serializers.PrimaryKeyRelatedField(queryset=ColorVariant.objects.all(), required=False, allow_null=True)
    size_variant = serializers.PrimaryKeyRelatedField(queryset=SizeVariant.objects.all(), required=False, allow_null=True)
    finish_variant = serializers.PrimaryKeyRelatedField(queryset=FinishingVariant.objects.all(), required=False, allow_null=True)
    hanging_variant = serializers.PrimaryKeyRelatedField(queryset=FrameHangVariant.objects.all(), required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)
    adjusted_image = serializers.ImageField(required=False, allow_null=True)  # Make optional

    class Meta:
        model = CartItem
        fields = ['frame', 'color_variant', 'size_variant', 'finish_variant', 'hanging_variant', 'quantity', 'adjusted_image']

    def update(self, instance, validated_data):
        # Update image field if provided
        if 'adjusted_image' in validated_data:
            adjusted_image = validated_data.pop('adjusted_image')
            # Delete old image if it exists
            if instance.adjusted_image:
                instance.adjusted_image.delete()
            # Save new image
            file_path = f"cart/adjusted/{adjusted_image.name}"
            saved_path = instance.adjusted_image.storage.save(file_path, adjusted_image)
            instance.adjusted_image = saved_path

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
