# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from decimal import Decimal
from django. conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.utils.text import slugify #берет опред поле и переделывает его в поле с типом слаг
from django.core.urlresolvers import reverse
from transliterate import translit


class Category(models.Model):

    name = models.CharField(max_length=100) #
    slug = models.SlugField(blank=True) #отдельная ссылка на себя, True - значит может быть пустым

    def __unicode__(self):
        return self.name    # в админке теперь будет отображаться имя

    def get_absolute_url(self):
        return reverse ('category_detail', kwargs={'category_slug': self.slug})

def pre_save_category_slug(sender, instance, *args, **kwargs):  # автоматическое сохранение слага
    if not instance.slug: # если слаг не заполнен
        slug = slugify(translit(unicode(instance.name), reversed=True)) # траснлит перевод в латиницу
        instance.slug = slug


pre_save.connect(pre_save_category_slug, sender=Category)

class Brand(models.Model):

    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

def image_folder(instance, filename):
    filename = instance.slug + '.' + filename.split('.')[1] # задаем имя + расширение (разбиваем по точке)
    return '{0}/{1}'.format(instance.slug, filename)

class ProductManager(models.Manager):  # для available
    def all(self, *args, **kwargs): # (переопределяем all)
        return super(ProductManager, self).get_queryset().filter(available=True) # говорим что это поле всегда должно быть тру

class Product(models.Model):

    category = models.ForeignKey(Category) # продукт связан с категорией
    brand = models.ForeignKey(Brand)
    title = models.CharField(max_length=120) # название продукта
    slug = models.SlugField() # ссылка на товар
    description = models.TextField()
    image = models.ImageField(upload_to=image_folder)
    price = models.DecimalField(max_digits=9, decimal_places=0)
    available = models.BooleanField(default=True)
    objects = ProductManager() # связываем с классом и тем самым с фильтром на тру

    def __unicode__(self):
        return self.title # в админке отображается имя продукта


    def get_absolute_url(self):
        return reverse ('product_detail', kwargs={'product_slug': self.slug})  # фун-ия reverse нужна для того, чтобы создать ссылки на будущие обьекты


class CartItem(models.Model):

    product = models.ForeignKey(Product)
    qty = models.PositiveIntegerField(default=1) #кол-во
    item_total = models.DecimalField(max_digits=9, decimal_places=0, default=0)

    def __unicode__(self):
        return 'Cart item for product {0}'.format(self.product.title)

class Cart(models.Model): # корзина

    items=models.ManyToManyField(CartItem, blank=True) # в корзину можно добавить множество картайтем
    cart_total = models.DecimalField(max_digits=9, decimal_places=0, default=0)

    def __unicode__(self):
        return str(self.id) # возвращает id корзины

    def add_to_cart(self, product_slug):
        cart=self
        product = Product.objects.get(slug=product_slug)
        new_item, _ = CartItem.objects.get_or_create(product=product, item_total=product.price)
        if new_item not in cart.items.all():
            cart.items.add(new_item)
            cart.save()

    def remove_from_cart(self, product_slug):
        cart=self
        product = Product.objects.get(slug=product_slug)
        for cart_item in cart.items.all():
            if cart_item.product == product:
                cart.items.remove(cart_item)
                cart.save()

    def change_qty(self, qty, item_id):
        cart = self
        cart_item = CartItem.objects.get(id=int(item_id))
        cart_item.qty = int(qty)  # присваеваем новое значение
        cart_item.item_total = int(qty) * Decimal(cart_item.product.price)  # изменяем тотал, кол-во на цену товаров
        cart_item.save()
        new_cart_total = 0
        for item in cart.items.all():
            new_cart_total += float(item.item_total)
        cart.cart_total = new_cart_total
        cart.save()

ORDER_STATUS_CHOISES = (
    ('Принят в обработку','Принят в обработку'),
    ('Выполняется','Выполняется'),
    ('Оплачен','Оплачен')
)

STATUS_CHOISES = (
    ('Самовывоз', 'Самовывоз'),
    ('Доставка', 'Доставка')
)

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    items = models.ManyToManyField(Cart)
    total = models.DecimalField(max_digits=9, decimal_places=0, default=0)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    buying_type = models.CharField(max_length=40, choices=(STATUS_CHOISES), default='Самовывоз')
    date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField()
    status = models.CharField(max_length=100, choices=ORDER_STATUS_CHOISES, default=ORDER_STATUS_CHOISES[0][0])

    def __unicode__(self):
        return "Заказ №{0}".format(str(self.id))

