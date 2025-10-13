import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import CharField
from django.utils import timezone
from django.utils.deconstruct import deconstructible


class Login(AbstractUser):
    is_user = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=False)
    email = models.EmailField()
    company_name = models.CharField(max_length=100, blank=True, null=True)
    company_address = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    is_blocked = models.BooleanField(default=False)

class FrameCategories(models.Model):
    frameCategory = models.CharField(max_length=100)

    def __str__(self):
        return self.frameCategory

class Frame(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='frames/')
    corner_image = models.ImageField(upload_to='frames/corner/')
    inner_width = models.FloatField()
    inner_height = models.FloatField()
    created_by = models.ForeignKey(Login, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        FrameCategories,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='frames'
    )
    def __str__(self):
        return self.name

class ColorVariant(models.Model):
    frame = models.ForeignKey(Frame, related_name='color_variants', on_delete=models.CASCADE)
    color_name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='frame_variants/colors/')
    corner_image = models.ImageField(upload_to='frame_variants/colors/corner/')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.frame.name} - {self.color_name}"

    def clean(self):
        if ColorVariant.objects.filter(frame=self.frame, color_name=self.color_name).exclude(id=self.id).exists():
            raise ValidationError(f"Color variant '{self.color_name}' already exists for frame '{self.frame.name}'.")

    class Meta:
        unique_together = ('frame', 'color_name')

class SizeVariant(models.Model):
    frame = models.ForeignKey(Frame, related_name='size_variants', on_delete=models.CASCADE)
    size_name = models.CharField(max_length=50)
    inner_width = models.FloatField()
    inner_height = models.FloatField()
    image = models.ImageField(upload_to='frame_variants/sizes/', blank=True, null=True)
    corner_image = models.ImageField(upload_to='frame_variants/sizes/corner/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.frame.name} - {self.size_name}"

    def clean(self):
        if SizeVariant.objects.filter(frame=self.frame, size_name=self.size_name).exclude(id=self.id).exists():
            raise ValidationError(f"Size variant '{self.size_name}' already exists for frame '{self.frame.name}'.")

    class Meta:
        unique_together = ('frame', 'size_name')

class FinishingVariant(models.Model):
    frame = models.ForeignKey(Frame, related_name='finishing_variants', on_delete=models.CASCADE)
    finish_name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='frame_variants/finishes/')
    corner_image = models.ImageField(upload_to='frame_variants/finishes/corner/')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.frame.name} - {self.finish_name}"

    def clean(self):
        if FinishingVariant.objects.filter(frame=self.frame, finish_name=self.finish_name).exclude(id=self.id).exists():
            raise ValidationError(f"Finishing variant '{self.finish_name}' already exists for frame '{self.frame.name}'.")

    class Meta:
        unique_together = ('frame', 'finish_name')

class FrameHangVariant(models.Model):
    frame = models.ForeignKey(Frame, related_name='frameHanging_variant', on_delete=models.CASCADE)
    hanging_name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='hangings_variants/hangings/')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.frame.name} - {self.hanging_name}"

    def clean(self):
        if FrameHangVariant.objects.filter(frame=self.frame, hanging_name=self.hanging_name).exclude(id=self.id).exists():
            raise ValidationError(f"Hanging variant '{self.hanging_name}' already exists for frame '{self.frame.name}'.")

    class Meta:
        unique_together = ('frame', 'hanging_name')

class Cart(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    frame = models.ForeignKey(Frame, on_delete=models.CASCADE)
    original_image = models.ImageField(upload_to='cart/original/', null=True, blank=True)
    cropped_image = models.ImageField(upload_to='cart/cropped/', null=True, blank=True)
    adjusted_image = models.ImageField(upload_to='cart/adjusted/', null=True, blank=True)
    color_variant = models.ForeignKey(ColorVariant, null=True, blank=True, on_delete=models.SET_NULL)
    size_variant = models.ForeignKey(SizeVariant, null=True, blank=True, on_delete=models.SET_NULL)
    finish_variant = models.ForeignKey(FinishingVariant, null=True, blank=True, on_delete=models.SET_NULL)
    hanging_variant = models.ForeignKey(FrameHangVariant, null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField(default=1)
    transform_x = models.FloatField(default=0)
    transform_y = models.FloatField(default=0)
    scale = models.FloatField(default=1)
    rotation = models.FloatField(default=0)
    frame_rotation = models.FloatField(default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Calculate total price based on frame and variants
        price = self.frame.price if self.frame else 0
        if self.color_variant:
            price += self.color_variant.price
        if self.size_variant:
            price += self.size_variant.price
        if self.finish_variant:
            price += self.finish_variant.price
        if self.hanging_variant:
            price += self.hanging_variant.price
        self.total_price = price * self.quantity
        super().save(*args, **kwargs)
    def __str__(self):
        return f"CartItem for {self.cart.user.username} - Frame: {self.frame.name}"

class Order(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ], default='pending')

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    image = models.ImageField(upload_to='order_images/')
    frame = models.ForeignKey(Frame, on_delete=models.CASCADE)
    color_variant = models.ForeignKey(ColorVariant, on_delete=models.CASCADE, null=True, blank=True)
    size_variant = models.ForeignKey(SizeVariant, on_delete=models.CASCADE, null=True, blank=True)
    finish_variant = models.ForeignKey(FinishingVariant, on_delete=models.CASCADE, null=True, blank=True)
    hanging_variant = models.ForeignKey(FrameHangVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"OrderItem for {self.frame.name} ({self.quantity})"


class MackBoard(models.Model):
    board_name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='mack_board_images/', null=True, blank=True)
    price = models.DecimalField(null=True, max_digits=10, decimal_places=2)

    def __str__(self):
        return self.board_name

class MackBoardColorVariant(models.Model):
    mack_board = models.ForeignKey(MackBoard, related_name='color_variants', on_delete=models.CASCADE)
    color_name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='mack_board_color_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.color_name} for {self.mack_board.board_name}"


@deconstructible
class UploadToShortName:
    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        new_filename = f"{uuid.uuid4().hex[:8]}.{ext}"
        return os.path.join(self.path, new_filename)

class SavedItem(models.Model):
    user = models.ForeignKey('Login', on_delete=models.CASCADE)
    frame = models.ForeignKey('Frame', on_delete=models.SET_NULL, null=True, blank=True)
    color_variant = models.ForeignKey('ColorVariant', on_delete=models.SET_NULL, null=True, blank=True)
    size_variant = models.ForeignKey('SizeVariant', on_delete=models.SET_NULL, null=True, blank=True)
    finish_variant = models.ForeignKey('FinishingVariant', on_delete=models.SET_NULL, null=True, blank=True)
    hanging_variant = models.ForeignKey('FrameHangVariant', on_delete=models.SET_NULL, null=True, blank=True)
    custom_width = models.FloatField(null=True, blank=True)
    custom_height = models.FloatField(null=True, blank=True)
    transform_x = models.FloatField(default=0)
    transform_y = models.FloatField(default=0)
    scale = models.FloatField(default=1)
    rotation = models.FloatField(default=0)
    frame_rotation = models.FloatField(default=0)
    adjusted_image = models.ImageField(upload_to='adjusted_images/', null=True, blank=True)
    original_image = models.ImageField(upload_to=UploadToShortName('original_images/'), blank=True, null=True)
    cropped_image = models.ImageField(upload_to=UploadToShortName('cropped_images/'), blank=True, null=True)
    print_width = models.FloatField(null=True, blank=True)
    print_height = models.FloatField(null=True, blank=True)
    print_unit = models.CharField(max_length=10, choices=[('inches', 'Inches'), ('cm', 'Cm')], default='inches')
    media_type = models.CharField(max_length=50, default='Photopaper')
    paper_type = models.CharField(max_length=50, null=True, blank=True)
    fit = models.CharField(max_length=20, choices=[('borderless', 'Borderless'), ('bordered', 'Bordered')], default='borderless')
    border_depth = models.IntegerField(null=True, blank=True, default=0)
    border_color = models.CharField(max_length=7, default='#ffffff')
    border_unit = models.CharField(max_length=50, blank=True, null=True)
    frame_depth = models.IntegerField(null=True, blank=True, default=0)
    custom_frame_color = models.CharField(max_length=7, blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid')], default='pending')
    total_price = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SavedItem {self.id} for user {self.user.username}"

class SavedItemMackBoard(models.Model):
    saved_item = models.ForeignKey(SavedItem, on_delete=models.CASCADE, related_name='mack_boards')
    mack_board = models.ForeignKey('MackBoard', on_delete=models.SET_NULL, null=True, blank=True)
    mack_board_color = models.ForeignKey('MackBoardColorVariant', on_delete=models.SET_NULL, null=True, blank=True)
    width = models.IntegerField(default=20)
    position = models.IntegerField(default=0)  # To maintain order of MackBoards

    def __str__(self):
        return f"MackBoard {self.mack_board.board_name} for SavedItem {self.saved_item.id}"


class Mug(models.Model):
    mug_name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='mug/', null=True, blank=True)
    glb_file = models.FileField(upload_to='mug/glb/', null=True, blank=True)  # New field for GLB file
    price = models.DecimalField(null=True, max_digits=10, decimal_places=2)

    def clean(self):
        # Ensure at least one of image or glb_file is provided
        if not self.image and not self.glb_file:
            raise ValidationError("At least one of image or GLB file must be provided.")

    def __str__(self):
        return self.mug_name

class Cap(models.Model):
    cap_name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='cap/', null=True, blank=True)
    price = models.DecimalField(null=True, max_digits=10, decimal_places=2)

class Tshirt(models.Model):
    tshirt_name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='tshirt/%Y/%m/%d/', null=True, blank=True)
    created_by = models.ForeignKey('Login', on_delete=models.CASCADE)  # Adjust as per your auth model
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tshirt_name

    class Meta:
        ordering = ['tshirt_name']

class TshirtColorVariant(models.Model):
    tshirt = models.ForeignKey(Tshirt, related_name='color_variants', on_delete=models.CASCADE)
    color_name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='tshirt_variants/colors/%Y/%m/%d/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.tshirt.tshirt_name} - {self.color_name}"

    def clean(self):
        if TshirtColorVariant.objects.filter(tshirt=self.tshirt, color_name=self.color_name).exclude(id=self.id).exists():
            raise ValidationError(f"Color variant '{self.color_name}' already exists for tshirt '{self.tshirt.tshirt_name}'.")

    class Meta:
        unique_together = ('tshirt', 'color_name')

class TshirtSizeVariant(models.Model):
    tshirt = models.ForeignKey(Tshirt, related_name='size_variants', on_delete=models.CASCADE)
    size_name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='tshirt_variants/sizes/%Y/%m/%d/', null=True, blank=True)
    inner_width = models.FloatField(null=True, blank=True)
    inner_height = models.FloatField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.tshirt.tshirt_name} - {self.size_name}"

    def clean(self):
        if TshirtSizeVariant.objects.filter(tshirt=self.tshirt, size_name=self.size_name).exclude(id=self.id).exists():
            raise ValidationError(f"Size variant '{self.size_name}' already existsISnipped '{self.tshirt.tshirt_name}'.")

class Tile(models.Model):
    tile_name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='tile/', null=True, blank=True)
    price = models.DecimalField(null=True, max_digits=10, decimal_places=2)

class Pens(models.Model):
    pen_name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='pen/', null=True, blank=True)
    price = models.DecimalField(null=True, max_digits=10, decimal_places=2)


class GiftOrder(models.Model):
    # Specific foreign keys for each gift type
    user = models.ForeignKey('Login', on_delete=models.CASCADE)
    tshirt = models.ForeignKey(
        'Tshirt',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    mug = models.ForeignKey(
        'Mug',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    cap = models.ForeignKey(
        'Cap',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    tile = models.ForeignKey(
        'Tile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    pen = models.ForeignKey(
        'Pens',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    # T-shirt specific variant fields
    tshirt_color_variant = models.ForeignKey(
        'TshirtColorVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    tshirt_size_variant = models.ForeignKey(
        'TshirtSizeVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    # Order details
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    uploaded_image = models.ImageField(upload_to='orders/uploaded/%Y/%m/%d/')
    preview_image = models.ImageField(upload_to='orders/preview/%Y/%m/%d/')
    image_position_x = models.FloatField()
    image_position_y = models.FloatField()
    image_scale_x = models.FloatField()
    image_scale_y = models.FloatField()
    image_rotation = models.FloatField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Ensure exactly one gift type is selected
        gift_types = [self.tshirt, self.mug, self.cap, self.tile, self.pen]
        non_null_gifts = [gt for gt in gift_types if gt is not None]
        if len(non_null_gifts) != 1:
            raise ValidationError("Exactly one gift type (Tshirt, Mug, Cap, Tile, or Pen) must be specified.")

        # Validate T-shirt orders have both color and size variants
        if self.tshirt and (not self.tshirt_color_variant or not self.tshirt_size_variant):
            raise ValidationError("T-shirt orders must include both a color variant and a size variant.")

        # Validate non-T-shirt orders do not have T-shirt variants
        if not self.tshirt and (self.tshirt_color_variant or self.tshirt_size_variant):
            raise ValidationError("Non-T-shirt orders cannot include T-shirt variants.")

        # Ensure T-shirt variants belong to the selected T-shirt
        if self.tshirt:
            if self.tshirt_color_variant and self.tshirt_color_variant.tshirt != self.tshirt:
                raise ValidationError("T-shirt color variant must belong to the selected T-shirt.")
            if self.tshirt_size_variant and self.tshirt_size_variant.tshirt != self.tshirt:
                raise ValidationError("T-shirt size variant must belong to the selected T-shirt.")

    def __str__(self):
        gift_type = next((gt for gt in ['tshirt', 'mug', 'cap', 'tile', 'pen'] if getattr(self, gt)), 'unknown')
        gift = getattr(self, gift_type)
        return f"Order {self.id} for {gift_type.capitalize()} {getattr(gift, f'{gift_type}_name', 'Unknown')}"

    class Meta:
        ordering = ['-created_at']

class PrintType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.price}"


class PrintSize(models.Model):
    name = models.CharField(max_length=20, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.price}"


class PaperType(models.Model):
    name = models.CharField(max_length=20, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.price}"


class LaminationType(models.Model):
    name = models.CharField(max_length=20, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.price}"


class DocOrder(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    print_type = models.ForeignKey(PrintType, on_delete=models.CASCADE)
    print_size = models.ForeignKey(PrintSize, on_delete=models.CASCADE)
    paper_type = models.ForeignKey(PaperType, on_delete=models.CASCADE)
    lamination = models.BooleanField(default=False)
    lamination_type = models.ForeignKey(LaminationType, on_delete=models.CASCADE, null=True, blank=True)
    delivery_option = models.CharField(max_length=20, choices=[('collection', 'Collection'), ('delivery', 'Delivery')])
    address_city = models.CharField(max_length=100, blank=True)
    address_pin = models.CharField(max_length=20, blank=True)
    address_house_name = models.CharField(max_length=200, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

class OrderFile(models.Model):
    order = models.ForeignKey('DocOrder', on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='order_files/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for Order {self.order.id}"


class DocumentFile(models.Model):
    order = models.ForeignKey('DocumentPrintOrder', on_delete=models.CASCADE, related_name='document_files')
    file = models.FileField(upload_to='document_prints/%Y/%m/%d/')
    print_type = models.ForeignKey('PrintType', on_delete=models.SET_NULL, null=True)
    print_size = models.ForeignKey('PrintSize', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    paper_type = models.ForeignKey('PaperType', on_delete=models.SET_NULL, null=True)
    lamination = models.BooleanField(default=False)
    lamination_type = models.ForeignKey('LaminationType', on_delete=models.SET_NULL, null=True, blank=True)

    def calculate_file_price(self):
        price = 0
        if self.print_type:
            price += float(self.print_type.price)
        if self.print_size:
            price += float(self.print_size.price)
        if self.paper_type:
            price += float(self.paper_type.price)
        if self.lamination and self.lamination_type:
            price += float(self.lamination_type.price)
        price *= self.quantity
        return round(price, 2)

    def __str__(self):
        return f"{self.file.name} - {self.print_type.name if self.print_type else 'No Print Type'}"

class DocumentPrintOrder(models.Model):
    DELIVERY_METHODS = (
        ('Collection', 'Collection'),
        ('Delivery', 'Delivery'),
    )
    user = models.ForeignKey('Login', on_delete=models.CASCADE, related_name='document_print_orders')
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    address = models.TextField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Add default
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')

    def calculate_total_price(self):
        price = sum(file.calculate_file_price() for file in self.document_files.all())
        price += float(self.delivery_charge)
        return round(price, 2)

    def save(self, *args, **kwargs):
        # Set a temporary total_price for initial save if not set
        if not self.pk and 'total_price' not in kwargs:
            self.total_price = 0.00
        super().save(*args, **kwargs)
        # Calculate total_price only if pk exists (after initial save)
        if self.pk:
            self.total_price = self.calculate_total_price()
            super().save(*args, **kwargs)  # Save again to update total_price

    def __str__(self):
        return f"Order by {self.user.username} - {self.created_at}"


class Theme(models.Model):
    theme_name = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.theme_name

class Background(models.Model):
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='backgrounds')
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='backgrounds/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.theme.theme_name})"

class Sticker(models.Model):
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='stickers')
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='stickers/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.theme.theme_name})"

class PhotoBookPapers(models.Model):
    size = models.CharField(max_length=50)  # e.g., 'A4', '8x10', etc.
    image = models.ImageField(upload_to='photobook_papers/')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.size} - ${self.price}"

class UploadedImage(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='uploads/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image by {self.user.username}"

class PhotoBookOrder(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)
    paper = models.ForeignKey(PhotoBookPapers, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

class Page(models.Model):
    order = models.ForeignKey(PhotoBookOrder, on_delete=models.CASCADE, related_name='pages')
    page_number = models.IntegerField()
    background = models.ForeignKey(Background, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('order', 'page_number')

    def __str__(self):
        return f"Page {self.page_number} of Order {self.order.id}"

class PageElement(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='elements')
    type = models.CharField(max_length=20, choices=[('image', 'Image'), ('sticker', 'Sticker'), ('text', 'Text'), ('placeholder', 'Placeholder')])
    content = models.TextField(blank=True)
    x = models.FloatField()
    y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    rotation = models.FloatField(default=0)
    z_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type} on Page {self.page.page_number}"