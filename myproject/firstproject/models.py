from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_delete
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db.models import Avg

class Balance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='balance')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Balance {self.user.email}: {self.amount}"

class BalanceOperation(models.Model):
    OPERATION_TYPE_CHOICES = (
        ('deposit', 'Пополнение'),
        ('transfer', 'Перевод'),
    )
    from_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='operations_made')
    to_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='operations_received')
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_operation_type_display()} {self.amount} at {self.timestamp}"


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('user', 'book')

    def get_total_price(self):
        return self.book.price * self.quantity

    def __str__(self):
        return f"{self.book.title} x {self.quantity} для {self.user.username}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    book = models.ForeignKey('Book', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.book.title} в избранном у {self.user.username}"

class BookReview(models.Model):
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_reviews')
    rating = models.PositiveSmallIntegerField("Оценка", choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField("Комментарий", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.get_full_name()} for {self.book.title}"

class ReviewReaction(models.Model):
    review = models.ForeignKey(BookReview, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_reactions')
    is_like = models.BooleanField(default=True)  # True - лайк, False - дизлайк

    class Meta:
        unique_together = ('review', 'user')


class Promotion(models.Model):
    title = models.CharField("Название акции", max_length=255)
    description = models.TextField("Описание", blank=True)
    image_url = models.URLField("URL картинки", blank=True)
    discount_percent = models.PositiveIntegerField("Процент скидки")
    start_datetime = models.DateTimeField("Дата и время начала")
    end_datetime = models.DateTimeField("Дата и время окончания")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.start_datetime is not None and self.end_datetime is not None:
            if self.start_datetime >= self.end_datetime:
                raise ValidationError("Дата начала должна быть меньше даты окончания")
        if self.discount_percent <= 0 or self.discount_percent > 100:
            raise ValidationError("Процент скидки должен быть от 1 до 100")

    def __str__(self):
        return f"{self.title} ({self.discount_percent}%)"

    def is_active(self):
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime


class Book(models.Model):
    title = models.CharField("Название", max_length=255)
    author = models.CharField("Автор", max_length=255)
    genre = models.CharField("Жанр", max_length=100)
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    original_price = models.DecimalField("Оригинальная цена", max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField("Количество на складе")
    isbn = models.CharField("ISBN", max_length=20, unique=True)
    image_urls = models.TextField("Ссылки на изображения (через запятую)", blank=True)
    rating = models.FloatField("Рейтинг", default=0.0)
    delivery_days = models.PositiveIntegerField("Количество дней доставки")
    sku = models.CharField("Артикул", max_length=12, unique=True, editable=False)

    def save(self, *args, **kwargs):
        # Устанавливаем original_price, если не задана
        if not self.original_price:
            self.original_price = self.price
        else:
            # Если цена книги меняется (не из-за акции), обновляем original_price
            if self.pk is not None:
                old = Book.objects.filter(pk=self.pk).first()
                if old and old.price != self.price and old.price == old.original_price:
                    self.original_price = self.price
        if not self.sku:
            while True:
                sku_candidate = get_random_string(length=12, allowed_chars='0123456789')
                if not Book.objects.filter(sku=sku_candidate).exists():
                    self.sku = sku_candidate
                    break
        super().save(*args, **kwargs)

    def get_image_list(self):
        return [url.strip() for url in self.image_urls.split(',') if url.strip()]

    def __str__(self):
        return f"{self.title} ({self.author})"

    def get_current_promotion(self):
        now = timezone.now()
        try:
            promo_book = self.promotion_on_book
            if promo_book.promotion.start_datetime <= now <= promo_book.promotion.end_datetime:
                return promo_book.promotion
        except PromotionBook.DoesNotExist:
            return None
        return None

    def get_discounted_price(self):
        promotion = self.get_current_promotion()
        if promotion:
            discount = Decimal(promotion.discount_percent) / Decimal('100')
            return round(self.price * (Decimal('1') - discount), 2)
        return self.price


class PromotionBook(models.Model):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='promotion_books')
    book = models.OneToOneField('Book', on_delete=models.CASCADE, related_name='promotion_on_book')

    def clean(self):
        active_promos = Promotion.objects.filter(
            promotion_books__book=self.book,
            end_datetime__gt=timezone.now()
        ).exclude(pk=self.promotion.pk)
        if active_promos.exists():
            raise ValidationError(f"Книга '{self.book.title}' уже участвует в другой акции.")

    def __str__(self):
        return f"{self.book.title} в акции {self.promotion.title}"


@receiver(post_save, sender=PromotionBook)
def apply_discount(sender, instance, **kwargs):
    book = instance.book
    promotion = instance.promotion

    if book.original_price is None:
        book.original_price = book.price

    discount_factor = Decimal(promotion.discount_percent) / Decimal('100')
    new_price = (book.original_price * (1 - discount_factor)).quantize(Decimal('0.01'))

    if book.price != new_price:
        # Обновляем цену напрямую через update, чтобы избежать рекурсивного вызова save
        Book.objects.filter(pk=book.pk).update(price=new_price)


@receiver(post_delete, sender=PromotionBook)
def remove_discount(sender, instance, **kwargs):
    book = instance.book
    if book.original_price is not None and book.price != book.original_price:
        # Обновляем цену напрямую через update, чтобы избежать рекурсивного вызова save
        Book.objects.filter(pk=book.pk).update(price=book.original_price)


@receiver(pre_delete, sender=Promotion)
def remove_promotionbooks_before_promotion_delete(sender, instance, **kwargs):
    books_to_reset = [pb.book.pk for pb in instance.promotion_books.all()]
    instance.promotion_books.all().delete()
    Book.objects.filter(pk__in=books_to_reset, price__lt=models.F('original_price')).update(
        price=models.F('original_price')
    )



def reset_prices_for_expired_promotions():
    now = timezone.now()
    expired_promos = Promotion.objects.filter(end_datetime__lt=now)
    for promo in expired_promos:
        for pb in promo.promotion_books.all():
            book = pb.book
            if book.original_price and book.price != book.original_price:
                Book.objects.filter(pk=book.pk).update(price=book.original_price)



# Остальные модели (Profile, PasswordResetCode и т.д.) без изменений



# Остальные модели (Profile, PasswordResetCode и т.д.) оставляем без изменений

class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('client', 'Клиент'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    middle_name = models.CharField("Отчество", max_length=30, blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    role = models.CharField("Роль", max_length=10, choices=ROLE_CHOICES, default='client')
    is_blocked = models.BooleanField("Блокирован", default=False)

    def __str__(self):
        return f"{self.user.email} Profile"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"ResetCode for {self.user.email} - expires at {self.expires_at}"
