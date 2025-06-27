from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

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

class Frame(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='frames/')
    inner_width = models.FloatField()
    inner_height = models.FloatField()
    created_by = models.ForeignKey(Login, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ColorVariant(models.Model):
    frame = models.ForeignKey(Frame, related_name='color_variants', on_delete=models.CASCADE)
    color_name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='frame_variants/colors/')
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