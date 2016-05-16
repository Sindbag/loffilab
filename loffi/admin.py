from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from loffi.models import MyUser, Client, Status, CartItem, Question


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput)

    class Meta:
        model = MyUser
        fields = ('email', 'name')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпали")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = MyUser
        fields = ('email', 'password', 'name', 'is_active', 'is_staff')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class DetailsInline(admin.StackedInline):
    model = Client
    extra = 0
    allow_add = True
    fields = ('tel',)


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'name', 'is_staff', 'details')
    list_filter = ('is_staff', )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('name',)}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                      'groups', 'user_permissions')}),
    )
    inlines = [DetailsInline, ]
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2')}
         ),
    )
    search_fields = ('email', 'name', 'details__tel')
    ordering = ('email',)
    filter_horizontal = ()


# Now register the new UserAdmin...
admin.site.register(MyUser, UserAdmin)
# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
# admin.site.unregister(Group)

from loffi.models import ItemSubClass, ItemClass, ItemModel, ItemImage, MainSlider, Article, Cart, Order


class ItemImageAdmin(admin.ModelAdmin):
    list_display = ('image_tag',)


class ItemImageInline(admin.StackedInline):
    model = ItemImage
    extra = 2
    allow_add = True
    fields = ('image_tag', 'image')
    readonly_fields = ('image_tag',)


class ItemModelAdmin(admin.ModelAdmin):
    inlines = [
        ItemImageInline,
    ]
    list_display = ('link', 'title', 'section', 'subclass', 'get_size')
    list_filter = ('section', 'subclass')
    search_fields = ('title', 'section', 'subclass', 'description', 'get_size')


class CartItemInline(admin.StackedInline):
    model = CartItem
    extra = 0
    allow_add = False
    fields = ('item', 'amount',)


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'items', 'sum', 'view_status', 'question', 'contact', 'create_date')
    search_fields = ('owner', 'status', 'create_date', 'id')
    list_filter = ('status',)
    # readonly_fields = ('cart',)

    @staticmethod
    def view_status(obj):
        return obj.status

    view_status.__name__ = 'Статус'

    view_status.empty_value_display = '???'


class CartAdmin(admin.ModelAdmin):
    inlines = [
        CartItemInline,
    ]
    list_display = ('id', 'model_owner', 'sum_price', 'order')
    search_fields = ('sum_price', 'owner', 'id', 'order')

    def get_form(self, request, obj=None, **kwargs):
        if hasattr(obj, 'order') and obj.order:
            self.exclude = ("owner", )
        form = super(CartAdmin, self).get_form(request, obj, **kwargs)
        return form


class StatusAdmin(admin.ModelAdmin):
    list_display = ('text', 'details')


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'link', 'short_text', 'pub_date')


class ItemClassAdmin(admin.ModelAdmin):
    list_display = ('link', 'title', 'description', 'keywords')
    search_fields = ('link', 'title', 'super_class', 'description', 'keywords')


class ItemSubClassAdmin(admin.ModelAdmin):
    list_display = ('link', 'title', 'description', 'super_class', 'keywords')
    search_fields = ('title', 'link', 'super_class', 'description', 'keywords')
    list_filter = ('super_class',)


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'answer', 'is_read_str', 'pub_date')
    list_filter = ('is_read_str',)
    search_fields = ('question', 'pub_date', 'answer')

    @staticmethod
    def ans(obj):
        return obj.answer
    ans.empty_value_display = 'В обработке'

    ans.__name__ = 'Ответ администратора'


admin.site.register(ItemModel, ItemModelAdmin)
admin.site.register(ItemImage, ItemImageAdmin)
admin.site.register(ItemClass, ItemClassAdmin)
admin.site.register(ItemSubClass, ItemSubClassAdmin)
admin.site.register(MainSlider)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Status, StatusAdmin)
# admin.site.register(Question, QuestionAdmin)
