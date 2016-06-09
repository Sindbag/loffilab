import datetime
from ckeditor_uploader.fields import RichTextUploadingField
from django import forms
from django.contrib.auth.models import User, PermissionsMixin
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.forms import ModelForm, Textarea, Form, TextInput, EmailInput, PasswordInput
from django.utils import timezone
from django.utils.deconstruct import deconstructible

from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)


def subclass_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/images_<subclass>/<model>_<filename>
    return 'images_{0}/{1}_{2}'.format(instance.model.subclass.link, instance.model.link, filename)


alphanumeric = RegexValidator(r'^[0-9a-zA-Z_-]*$', 'Только латинские буквы и цифры.')

phone_regex = RegexValidator(regex=r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$',
                             message="Телефон должен быть введён в формате: "
                                     "'+7 (999) 999 9999'.")


class MyUserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        """
        Creates and saves a User with the given email, name
        and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            name=name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        """
        Creates and saves a superuser with the given email, name
        and password.
        """
        user = self.create_user(email,
                                password=password,
                                name=name,
                                )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class MyUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='E-mail адрес',
        max_length=255,
        unique=True,
    )
    name = models.CharField(
        verbose_name='Имя',
        max_length=50,
    )
    is_staff = models.BooleanField('Администратор', default=False,
                                   help_text='Доступ к администрированию сайта')
    is_active = models.BooleanField('Активированный аккаунт', default=True,
                                    help_text='Активен ли пользователь')
    date_joined = models.DateTimeField('date joined', default=timezone.now)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name_plural = 'Пользователи'
        verbose_name = 'Пользователь'

    def get_full_name(self):
        # The user is identified by their email address
        return self.name + " | " + self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):  # __unicode__ on Python 2
        return self.name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

    def get_today_questions(self):
        today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)

        return self.questions.filter(pub_date__range=(today_min, today_max)).count()

    def has_unread_ans(self):
        return self.questions.filter(is_read=False).count()


class ItemModel(models.Model):
    title = models.CharField('Название', max_length=130)
    link = models.CharField('Название на английском', max_length=130, validators=[alphanumeric], unique=True,
                            primary_key=True, help_text='Название для использования в ссылках')
    description = models.TextField('Описание', max_length=1500)

    price = models.PositiveIntegerField('Цена', default=0)

    materials = models.CharField('Материал', max_length=200)

    size_x = models.FloatField('Ширина', default=0, help_text="миллиметров, мм")
    size_y = models.FloatField('Длина', default=0, help_text="миллиметров, мм")
    size_z = models.FloatField('Высота', default=0, blank=True, null=True, help_text="миллиметров, мм")

    def get_size(self):
        return str(self.size_x) + " мм x " + str(self.size_y) + " мм x " + str(self.size_z) + " мм"

    add_date = models.DateTimeField(auto_now=True)

    section = models.ForeignKey('ItemClass', related_name='items', verbose_name='Раздел')
    subclass = models.ForeignKey('ItemSubClass', related_name='items', verbose_name='Подраздел')

    # is_promoted = models.BooleanField(default=False, verbose_name="Рекламируется",
    #                                   help_text="Выводить предмет в список")
    # promotion_header = models.CharField(max_length=120, blank=True, null=True, verbose_name="Заголовок рекламы")
    # promotion_text = models.CharField(max_length=250, blank=True, null=True, verbose_name="Описание рекламы")

    keywords = models.CharField(max_length=200, verbose_name='Ключевые слова', help_text='Для поисковиков', default='')

    def __str__(self):
        return str(self.title)

    class Meta:
        ordering = ['-add_date']
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def save(self, *args, **kwargs):
        """Присваиваем раздел по подразделу перед сохранением"""
        self.section = self.subclass.super_class
        super(ItemModel, self).save(*args, **kwargs)

        # def clean(self):
        #     """Не разрешается помещать объект в рекламу при отсутствии заголовка рекламы и хотя бы одного изображения,
        #     максимум одновременно рекламируемых объектов — 5"""
        #     super(ItemModel, self).clean()
        #     if self.is_promoted and (self.promotion_header is None or self.images is None or ItemModel.objects.filter(
        #             is_promoted=True).count() > 5):
        #         raise ValidationError(
        #             """Нельзя рекламировать без хотя бы одного изображения и с пустым заголовком слайда,
        #             а также больше 5 элементов одновременно"""
        #         )


class ItemImage(models.Model):
    model = models.ForeignKey(ItemModel, related_name='images', verbose_name='Товар', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=subclass_directory_path, verbose_name="Изображение")

    def __str__(self):
        return str(self.model) + " Фото " + str(self.id)

    def image_tag(self):
        return '%s<br><img src="%s" width="100" height="100" />' % (str(self), self.image.url)

    image_tag.short_description = 'Превью изображения'
    image_tag.allow_tags = True

    def url(self):
        return self.image.url

    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'


class ItemClass(models.Model):
    title = models.CharField("Название раздела", max_length=100)
    link = models.CharField("Название на английском", max_length=50, unique=True, validators=[alphanumeric],
                            help_text="Название для адресной строки браузера", primary_key=True)

    description = models.CharField(max_length=500, verbose_name='Описание раздела')

    keywords = models.CharField(max_length=200, verbose_name='Ключевые слова', help_text='Для поисковиков', default='')

    image = models.ImageField(upload_to='sec_img', verbose_name='Изображение раздела',
                              help_text='Соотношение сторон должно быть 16x9')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Раздел'
        verbose_name_plural = 'Разделы'


class ItemSubClass(models.Model):
    title = models.CharField('Название подраздела', max_length=50)
    link = models.CharField("Название на английском", max_length=50, unique=True, validators=[alphanumeric],
                            help_text="Название для адресной строки браузера", primary_key=True)

    title_single = models.CharField('Название в единственном числе', max_length=50,
                                    help_text='Для использования в отдельных объектах', blank=True, null=True)

    super_class = models.ForeignKey(ItemClass, related_name='subclasses', verbose_name="Раздел",
                                    help_text="Раздел, к которому относится подраздел")

    description = models.TextField(max_length=700, verbose_name='Описание подраздела')

    keywords = models.CharField(max_length=200, verbose_name='Ключевые слова', help_text='Для поисковиков', default='')

    image = models.ImageField(upload_to='sub_img', verbose_name='Изображение подраздела',
                              help_text='Соотношение сторон должно быть 16x9')

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name = 'Подраздел'
        verbose_name_plural = 'Подразделы'


class MainSlider(models.Model):
    image = models.ImageField(upload_to='main_slider/', verbose_name="Фоновое изображение",
                              help_text='Соотношение сторон должно быть 16x9')
    link = models.CharField(max_length=250, verbose_name='Ссылка',
                            help_text='Куда переводить пользователя при нажатии на изображение', null=True)
    title = models.CharField(max_length=150, verbose_name='Заголовок слайда')

    # title_2 = models.CharField(max_length=200, verbose_name='Заголовок второго уровня', blank=True, null=True)
    # text = models.TextField(max_length=600, verbose_name='Содержание')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Слайд на главной'
        verbose_name_plural = 'Слайды на главной'


class Article(models.Model):
    title = models.CharField(max_length=150, verbose_name="Название")
    link = models.CharField(max_length=50, verbose_name="Ссылка", validators=[alphanumeric], unique=True,
                            help_text='Для отображения в адресной строке браузера,'
                                      ' английскими буквами, например \'first-article\'')

    short_text = models.TextField(max_length=650, verbose_name="Краткое содержание",
                                  help_text="Для отображения в общем списке новостей")
    text = RichTextUploadingField("Содержание статьи")

    pub_date = models.DateTimeField(auto_now=True)

    image = models.ImageField(upload_to='news', verbose_name='Изображение статьи',
                              help_text='Для отображения в общем списке новостей')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Публикации'
        ordering = ['-pub_date']


class Cart(models.Model):
    owner = models.OneToOneField(MyUser, verbose_name="Покупатель", related_name='cart', null=True)
    items = models.ManyToManyField('ItemModel', verbose_name='Товары', related_name='carts', through="CartItem")

    def __str__(self):
        return 'Корзина #' + str(self.id)

    def item_count(self):
        s = 0
        for cartitem in self.cartitem_set.all():
            s += cartitem.amount
        return s

    item_count.__name__ = 'Количество товаров'

    def sum_price(self):
        sprice = 0
        for cartitem in self.cartitem_set.all():
            sprice += cartitem.sprice()
        return sprice

    sum_price.__name__ = 'Сумма заказа'

    def model_owner(self):
        if not self.owner:
            return self.order.owner
        return self.owner

    model_owner.__name__ = 'Покупатель'

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class CartItem(models.Model):
    amount = models.PositiveSmallIntegerField(default=1, verbose_name='Количество')
    cart = models.ForeignKey('Cart', verbose_name='Корзина')
    item = models.ForeignKey('ItemModel', verbose_name='Товар')

    def sprice(self):
        return self.amount * self.item.price

    def __str__(self):
        return str(self.item)

    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'


@deconstructible
class Status(models.Model):
    text = models.CharField(max_length=60, verbose_name='Статус')
    details = models.CharField(max_length=600, verbose_name='Подробнее', help_text='Более детальное описание статуса')

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Статус'
        verbose_name_plural = 'Статусы заказов'


class Order(models.Model):
    cart = models.OneToOneField('Cart', verbose_name='Товары', related_name='order')
    status = models.ForeignKey('Status', verbose_name='Статус заказа', related_name='orders', null=True,
                               default=Status.objects.get_or_create(text='Не обработан',
                                                                    details='Заказ поступил в базу,'
                                                                            'но не был обработан администратором')[0]
                               )
    owner = models.ForeignKey(MyUser, verbose_name='Заказчик', related_name='orders', null=True)

    question = models.TextField('Дополнительная информация', blank=True)
    answer = models.TextField('Ответ администратора', null=True, blank=True)

    create_date = models.DateTimeField(verbose_name='Время создания заказа', default=timezone.now)
    answer_date = models.DateTimeField(auto_now=True, verbose_name='Время обработки заказа', null=True)

    contact = models.CharField(max_length=20, null=True, default='', verbose_name='Контактные данные')

    def items(self):
        return '\n'.join([str(x.item) + "\t" + str(x.amount) + " шт." for x in self.cart.cartitem_set.all()])

    items.__name__ = 'Товары'

    def items_and_price(self):
        return '\n'.join([str(x.item) + "\t" + str(x.amount) + " шт.\t" + str(x.sprice()) + " ₽" for x in
                          self.cart.cartitem_set.all()])

    def sum(self):
        return self.cart.sum_price()

    sum.__name__ = 'Сумма'

    def __str__(self):
        return 'Заказ #' + str(self.id)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-create_date']


class Client(models.Model):
    tel = models.CharField(max_length=25, validators=[phone_regex], blank=True, verbose_name='Телефон')
    user = models.OneToOneField(MyUser, related_name='details', verbose_name='Пользователь', null=True)

    def __str__(self):
        return self.tel

    class Meta:
        verbose_name = 'Информация'
        verbose_name_plural = 'Информация'


class Question(models.Model):
    question = models.CharField(max_length=1000, verbose_name='Вопрос пользователя')
    user = models.ForeignKey(MyUser, related_name='questions', verbose_name='Пользователь', null=True)
    answer = models.CharField(max_length=1000, verbose_name='Ответ администратора')
    pub_date = models.DateTimeField(default=timezone.now)

    is_read = models.BooleanField('Прочитано', default=True)

    def is_read_str(self):
        if self.is_read:
            return 'Прочитано'
        return 'Не прочитано'

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы пользователей'
        ordering = ['-pub_date']


# ################ Формы ################# #

class OrderForm(Form):
    question = forms.CharField(max_length=1600, help_text='Дополнительная информация о заказе', required=False,
                               widget=Textarea(
                                   attrs={'placeholder': 'Дополнительная информация о заказе'}
                               ))
    tel = forms.CharField(validators=[phone_regex], help_text='Номер телефона для связи',
                          widget=TextInput(attrs={'placeholder': '+7(900)1234567'}))


class UserForm(ModelForm):
    class Meta:
        model = MyUser
        fields = ('email', 'password')
        widgets = {
            'email': EmailInput(
                attrs={
                    'placeholder': "E-mail",
                    'required': ''
                }
            ),
            'password': PasswordInput(
                attrs={
                    'placeholder': 'Пароль',
                    'required': ''
                }
            ),
        }
        labels = {
            'password': 'Пароль',
        }
        help_texts = {
            'email': '',
        }


class UserRegForm(forms.ModelForm):
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(
        attrs={
            'placeholder': 'Пароль',
            'required': ''
        }))
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput(
        attrs={
            'placeholder': 'Повторите пароль',
            'required': ''
        }))

    class Meta:
        model = MyUser
        fields = ('email', 'name')
        widgets = {
            'email': EmailInput(
                attrs={
                    'placeholder': 'E-mail',
                    'required': ''
                }),
            'name': TextInput(
                attrs={
                    'placeholder': 'Как к Вам обращаться',
                    'required': ''
                }
            )
        }

    def clean_password2(self):
        # Check that the two password entries match
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Пароли не совпали")
        return password2


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ('tel',)
        widgets = {
            'tel': TextInput(attrs={'placeholder': '+7 (900) 123 45 67'}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('question',)
        widgets = {
            'question': TextInput(
                attrs={
                    'placeholder': 'Вы можете задать свой вопрос или оставить пожелания',
                    'size': '100%',
                }
            ),
        }
        labels = {
            'question': 'Задать новый вопрос:',
        }
