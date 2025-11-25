from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_delete
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

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
    year_created = models.PositiveIntegerField("Год создания книги", null=True, blank=True)
    language = models.CharField("Язык книги", max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.original_price:
            self.original_price = self.price
        else:
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

    # Пример метода для получения текущей акции — оставил как есть
    def get_current_promotion(self):
        now = timezone.now()
        try:
            promo_book = self.promotion_on_book
            if promo_book.promotion.start_datetime <= now <= promo_book.promotion.end_datetime:
                return promo_book.promotion
        except Exception:
            return None
        return None

    def get_discounted_price(self):
        promotion = self.get_current_promotion()
        if promotion:
            discount = Decimal(promotion.discount_percent) / Decimal('100')
            return round(self.price * (Decimal('1') - discount), 2)
        return self.price
    

class Order(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    delivery_address = models.TextField()
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Заказ #{self.id} от {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey('Book', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.book.price * self.quantity

    def __str__(self):
        return f"{self.book.title} x {self.quantity}"
    


    




    

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


class Card(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=19)  # format XXXX XXXX XXXX XXXX
    card_holder = models.CharField(max_length=100)
    expiry_date = models.CharField(max_length=5)  # MM/YY
    cvv = models.CharField(max_length=3)
    is_active = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)
    confirmation_code = models.CharField(max_length=4, blank=True, null=True)
    confirmation_code_created = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.card_holder} - **** **** **** {self.card_number[-4:] if self.card_number else '####'}"


class Balance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='balances')
    card = models.ForeignKey(Card, null=True, blank=True, on_delete=models.CASCADE, related_name='balances')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        unique_together = ('user', 'card')

    def __str__(self):
        card_num = self.card.card_number if self.card else "без карты"
        return f"Баланс пользователя {self.user.email} ({card_num}): {self.amount}"


class BalanceOperation(models.Model):
    OPERATION_TYPE_CHOICES = (
        ('deposit', 'Пополнение'),
        ('transfer', 'Перевод'),
        ('add_card', 'Добавление карты'),
        ('delete_card', 'Удаление карты'),
    )
    from_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='operations_made')
    to_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='operations_received')
    card = models.ForeignKey(
        Card, null=True, blank=True, on_delete=models.SET_NULL, related_name='operations')
    to_card = models.ForeignKey(
        Card, null=True, blank=True, on_delete=models.SET_NULL, related_name='operations_to', verbose_name='Карта получателя')
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        card_info = f" (от карты {self.card.card_number[-4:]})" if self.card else ""
        to_card_info = f" на карту {self.to_card.card_number[-4:]}" if self.to_card else ""
        amount_str = f" {self.amount}" if self.amount is not None else ""
        return f"{self.get_operation_type_display()}{card_info}{to_card_info}{amount_str} at {self.timestamp}"


class Chat(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_chats')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='manager_chats')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('client', 'manager')

    def __str__(self):
        manager_name = self.manager.get_full_name() if self.manager else "Удалён"
        return f"Чат клиента {self.client.get_full_name()} с менеджером {manager_name}"

    @property
    def is_manager_deleted(self):
        return self.manager is None


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Добавлено для времени редактирования
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)  # Для удаления своих сообщений

    def __str__(self):
        return f"Сообщение от {self.sender.get_full_name()} в чате {self.chat.id}"


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
    admin_response = models.TextField("Ответ админа", blank=True, null=True)  # Добавлено поле для ответа админа
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
    backup_word = models.CharField("Резервное слово", max_length=100, blank=True)  # добавленное поле

    def __str__(self):
        return f"{self.user.email} Profile"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()