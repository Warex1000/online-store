from PIL import Image   # for work with images
import sys   # module of size images

from django.db import models
from django.contrib.auth import get_user_model  # v.1 Используем юзера, который указан в настройках
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from io import BytesIO   # for work with images
from django.core.files.uploadedfile import InMemoryUploadedFile   # for resize download images
from django.urls import reverse   # make url for object product
from django.utils.translation import gettext_lazy


User = get_user_model()  # v.1.1 Используем юзера, который указан в скрытых настройках (settings.AUTH_USER_MODEL)


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewename):
    ct_model = obj.__class__._meta.model.name
    return reverse(viewename, kwargs={'ct_model': ct_model, 'slug': obj.slug})


"""
Представление которое будет отвечать за стартовую страницу будет имитировать 1 запрос и доставать весь список
товаров которое мы хотим отобразить на главной странице class LatestProductsManager
ContentType Микрофрейм ворк который видет модели которые есть в INSTALLED_APPS в settings предоставляя 
универсальный интерфейс
"""


class MinResolutionErrorException(Exception):
    pass


class MaxResolutionErrorException(Exception):
    pass


class LatestProductsManager:  # 1:13:00 Просмотреть суть этого класса с моделями.

    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')  # Отображение определенных товаров первыми в списке
        products = []  # Финальный список товаров
        ct_models = ContentType.objects.filter(model__in=args)  # Запрос ContentType фильтруя модели которые находятся в аргументах args
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to), reverse=True
                    )
        return products


class LatestProducts:
    objects = LatestProductsManager()


class CategoryManager(models.Manager):  # In site pages for side bar see the product category and Quantity

    CATEGORY_NAME_COUNT_NAME = {
        'Ноутбуки': 'notebook__count',
        'Смартфоны': 'smartphone__count'
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_left_sidebar(self):
        models = get_models_for_count('notebook', 'smartphone')
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolute_url(), count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]
        return data


class Category(models.Model):

    # parents_category = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name='Имя категории')
    slug = models.SlugField(
        unique=True)
    objects = CategoryManager()
    ''' 
    короткое название-метка, содержит только буквы числа нижнее подчеркивание дефис. 
    Используются в URL(Category/nootebook)
    '''
    prepopulated_fields = {"slug": (
    "title",)}  # позволяет определить поля, которые получают значение основываясь на значениях других полей

    class Meta:
        verbose_name = gettext_lazy('category')
        verbose_name_plural = gettext_lazy('categories')

    def __str__(self):  # отображение категории в админке
        return self.name   # f'{self.name} | parent - {self.parents_category}' if self.parent else self.name  # Показывает вложенные категории в админке

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):

    MIN_RESOLUTIONS = (400, 400)
    MAX_RESOLUTIONS = (900, 900)
    MAX_IMAGE_SIZE = 3145728  # ~ 3mb

    class Meta:
        abstract = True

    category = models.ForeignKey(Category, verbose_name='Категория',
                                 on_delete=models.CASCADE)
    '''
    Обект Category класса Product наследуеться(связан) от класса Category / 
    при удалении обекта удаляеться все связи с ним (данные)  
                                 '''
    title = models.CharField(max_length=255, verbose_name='Название продукта')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение')
    description = models.TextField(verbose_name='Описание товара', null=True)  # Поле может быть пустым null=True
    price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        verbose_name='Цена'
    )  # Параметры цены, максимальное колличество символов до запятой(9) и после(2)

    def __str__(self):
        return self.title


'''
    def save(self, *args, **kwargs):
        # 1. Example for save images upper then 400px and lower then 900px
        image = self.image
        img = Image.open(image)
        min_height, min_width = self.MIN_RESOLUTIONS
        max_height, max_width = self.MAX_RESOLUTIONS
        if img.height < min_height or img.width < min_width:
            raise MinResolutionErrorException('Разрешение изображения меньше минимального')
        if img.height > max_height or img.width > max_width:
            raise MaxResolutionErrorException('Разрешение изображения больше максимального')

        # 2. Example cut the images to 200px x 200px
        image = self.image
        img = Image.open(image)
        new_img = img.convert('RGB')
        resized_new_img = new_img.resize((200, 200), Image.ANTIALIAS)
        filestream = BytesIO()
        resized_new_img.save(filestream, 'JPEG', quality=90)
        filestream.seek(0)
        name = '{}.{}'.format(*self.image.name.split('.'))
        self.image = InMemoryUploadedFile(
            filestream, 'ImageField', name, 'jpeg/image', sys.getsizeof(filestream), None
        )
        super().save(*args, **kwargs)
'''


class Notebook(Product):
    name = models.CharField(max_length=255, verbose_name='Имя')
    diagonal = models.CharField(max_length=255, verbose_name='Диагональ')
    display_type = models.CharField(max_length=255, verbose_name='Тип дисплея')
    processor_freq = models.CharField(max_length=255, verbose_name='Частота процессора')
    ram = models.CharField(max_length=255, verbose_name='Оперативная память')
    video = models.CharField(max_length=255, verbose_name='Видеокарта')
    time_without_charge = models.CharField(max_length=255, verbose_name='Время работы аккамулятора')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)   # {Категория} : {Какой товар}

    def get_absolute_url(self):   # for url view
        return get_product_url(self, 'product_detail')


class Smartphone(Product):
    name = models.CharField(max_length=255, verbose_name='Имя')
    diagonal = models.CharField(max_length=255, verbose_name='Диагональ')
    display_type = models.CharField(max_length=255, verbose_name='Тип дисплея')
    resolution = models.CharField(max_length=255, verbose_name='Разрешение екрана')
    accum_volume = models.CharField(max_length=255, verbose_name='Обьем батареи')
    ram = models.CharField(max_length=255, verbose_name='Оперативная память')
    sd = models.BooleanField(default=True, verbose_name='Наличие sd карты')
    sd_volume_max = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Максимальный обем встроенной памяти'
    )
    main_camp_mp = models.CharField(max_length=255, verbose_name='Главная камера')
    frontal_camp_mp = models.CharField(max_length=255, verbose_name='Фронтальная камера')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):   # for url view
        return get_product_url(self, 'product_detail')

    # @property  # This all for check box sd
    # def sd(self):
    #     if self.sd:
    #         return 'Да'
    #     return 'Нет'


class CartProduct(models.Model):
    user = models.ForeignKey('Customer', verbose_name='Покупатель', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Корзина', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    '''
    Микрофрейм ворк который видет модели которые есть в INSTALLED_APPS в settings предоставляя универсальный интерфейс
    '''
    object_id = models.PositiveIntegerField()  # Индификатор инстанс этой модели
    content_object = GenericForeignKey('content_type', 'object_id')
    qty = models.PositiveIntegerField(default=1)
    '''
    Колличество выбранного товара в корзине, по умолчанию 1, Подобно IntegerField, но должно быть либо положительным, 
    либо нулевым (0). Значения от 0 до 2147483647 безопасны во всех базах данных, поддерживаемых Django.
    '''
    final_price = models.DecimalField(max_digits=9, decimal_places=2,
                                      verbose_name='Цена')  # Финальная цена всех товаров в корзине

    def __str__(self):
        return "Продукт: {} (для корзины)".format(
            self.content_object.title)


class Cart(models.Model):
    owner = models.ForeignKey('Customer', verbose_name='Владелец', on_delete=models.CASCADE)
    products = models.ManyToManyField(
        CartProduct,
        blank=True,
        related_name='related_cart'
    )  # Связь многие ко многим к CartProduct
    total_products = models.PositiveIntegerField(default=0)  # Корректное колличество товаров в корзине шт.
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')
    in_order = models.BooleanField(default=False)  # If True for identity user this is his cart
    for_anonymous_user = models.BooleanField(default=False)  # For anonymous user his cart

    def __str__(self):
        return str(self.id)


class Customer(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона')
    address = models.CharField(max_length=255, verbose_name='Адрес')

    def __str__(self):  # Показываем в админке что это за покупатель
        return "Покупатель: {} {}".format(self.user.first_name, self.user.last_name)

#   !!! Change type fields were it must be integer or float, then we do filter on Options
