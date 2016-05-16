import datetime
import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response, get_object_or_404
import random

# Create your views here.
from django.template import RequestContext

from loffi.models import ItemClass, ItemModel, MainSlider, ItemSubClass, Article, Cart, CartItem, OrderForm, Order, \
    Client, UserRegForm, ClientForm, QuestionForm


# random_idx = random.randint(0, Model.objects.count() - 1)
# random_obj = Model.objects.all()[random_idx]
# MyModel.objects.order_by('?').first()
def index(request):
    main_slides = MainSlider.objects.all()
    news_list = Article.objects.all()[:4]
    context = {
        'main_slides': main_slides,
        'news': news_list,
    }
    return render(request, 'index.html', context)


def menu_items(request):
    # subcl = ItemSubClass.objects.all()
    userregform = UserRegForm()
    clientform = ClientForm()
    return {
        'sects': ItemClass.objects.all(),
        'form': AuthenticationForm(),
        'clientform': clientform,
        'userregform': userregform,
    }


def section(request, link):
    sctn = ItemClass.objects.get(link=link)
    objcts = sctn.items.all()
    paginator = Paginator(objcts, 24)  # Show 24 items per page

    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)
    context = {'items': items,
               'section': sctn,
               }
    return render(request, 'section.html', context)


def subsection(request, link, subsection_link):
    sctn = ItemClass.objects.get(link=link)
    subsctn = ItemSubClass.objects.get(link=subsection_link)
    objcts = subsctn.items.all()
    paginator = Paginator(objcts, 24)  # Show 24 items per page

    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)
    if objcts.count():
        random_idx = random.randint(0, objcts.count() - 1)
        random_obj = objcts[random_idx]
    else:
        random_obj = None
    context = {'items': items,
               'rand_it': random_obj,
               'section': sctn,
               'subsection': subsctn,
               }
    return render(request, 'subsection.html', context)


def show_item(request, link, subsection_link, item_link):
    item = ItemModel.objects.get(link=item_link)
    try:
        in_cart = request.user.cart.cartitem_set.get(item=item).amount
    except Exception:
        in_cart = 0
    rand_items = ItemModel.objects.filter(subclass=subsection_link).exclude(link=item.link).order_by('?')[:4]
    return render(request, 'show.html', {'item': item,
                                         'rand_items': rand_items,
                                         'section': item.section,
                                         'subsection': item.subclass,
                                         'in_cart': in_cart,
                                         })


def about(request):
    return render(request, 'about.html', {'section': 'about', 'title': 'О нас'})


def contacts(request):
    return render(request, 'contacts.html', {'section': 'contacts', 'title': 'Контакты'})


def news(request):
    objcts = Article.objects.all()
    paginator = Paginator(objcts, 12)  # Show 12 news per page

    page = request.GET.get('page')
    try:
        news_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        news_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        news_list = paginator.page(paginator.num_pages)
    return render(request, 'news.html', {'news': news_list, 'title': "Новости", 'section': 'news'})


def show_article(request, article):
    artic = Article.objects.get(link=article)
    return render(request, 'article.html', {'article': artic, 'section': 'news', 'title': artic.title})


def all_items(request):
    all_items_lazy = ItemModel.objects.all()
    paginator = Paginator(all_items_lazy, 24)  # Show 24 items per page
    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)
    return render(request, 'all.html', {'items': items, 'title': 'Товары'})


def add_to_cart(request):
    if not request.user.is_authenticated:
        return HttpResponse(
            json.dumps({'error': "NOT AUTHORISED"}),
            content_type="application/json"
        )
    if request.is_ajax():
        link = request.POST.get('link')
        item = get_object_or_404(ItemModel, link=link)
        amount = request.POST.get('amount')
        if not amount:
            amount = 1
        else:
            amount = int(amount)
        change = request.POST.get('change')
        if not change:
            change = 0
        else:
            change = 1
        sum = 0
        flag = False
        try:
            cart_item = request.user.cart.cartitem_set.get(item=item)
            if change:
                cart_item.amount = amount
            else:
                cart_item.amount += amount
            amount = cart_item.amount
            sum = cart_item.sprice()
            cart_item.save()
        except Cart.DoesNotExist:
            request.user.cart = Cart.objects.create(owner=request.user)
        except CartItem.DoesNotExist:
            it = CartItem.objects.create(cart=request.user.cart, item=item, amount=amount)
            it.save()
            request.user.cart.cartitem_set.add(it)
        request.user.cart.save()
        response_data = {
            'amount': amount,
            'sum': sum,
            'total_items': request.user.cart.item_count(),
            'total_price': request.user.cart.sum_price()
        }
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json"
        )
    return HttpResponseRedirect('/')


@login_required
def account(request):
    filled, mistake = False, False
    try:
        user_cart = request.user.cart
    except Cart.DoesNotExist:
        user_cart = Cart.objects.create(owner=request.user)
        user_cart.save()

    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        if order_form.is_valid() and user_cart.item_count():
            try:
                order = Order.objects.create(
                    question=order_form.cleaned_data['question'],
                    contact=order_form.cleaned_data['tel'],
                    owner=request.user,
                    cart=user_cart
                )
                order.save()
                request.user.orders.add(order)

                user_cart.owner = None
                user_cart.save()

                if not hasattr(request.user, 'details'):
                    client = Client.objects.create(tel=order_form.cleaned_data['tel'], user=request.user)
                    client.save()
                new_cart = Cart.objects.create(owner=request.user)
                new_cart.save()

                filled = True
            except Cart.DoesNotExist or Cart.RelatedObjectDoesNotExist or \
                    Client.DoesNotExist or Client.RelatedObjectDoesNotExist or Client.MultipleObjectsReturned or \
                    ValidationError:
                mistake = True
    else:
        order_form = OrderForm()
    questionform = QuestionForm()
    return render(request, 'account.html', {
        'title': 'Личный Кабинет',
        'order_form': order_form,
        'order_filled': filled,
        'user_cart': user_cart,
        'mistake': mistake,
        'questionform': questionform,
    })


@login_required
def add_question(request):
    today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)

    if request.method == 'POST':
        if request.user.questions.filter(pub_date__range=(today_min, today_max)).count() <= 20:
            q_form = QuestionForm(data=request.POST)
            q = q_form.save()
            q.user = request.user
            q.save()
    return HttpResponseRedirect(reverse('account'))


def register(request):
    # Like before, get the request's context.
    context = RequestContext(request)

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    if request.user.is_authenticated():
        return HttpResponseRedirect('profile')

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserRegForm(data=request.POST)
        profile_form = ClientForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user_form.cleaned_data['password'])
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save()
            profile.user = user
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

            new_user = authenticate(email=user_form.cleaned_data['email'], password=user_form.cleaned_data['password'])
            login(request, new_user)
            next_page = request.GET.get('next')
            if next_page:
                return HttpResponseRedirect(next_page)
            else:
                return HttpResponseRedirect('/accounts/profile')

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        # else:
        #     print(user_form.errors, profile_form.errors)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserRegForm()
        profile_form = ClientForm()

    # Render the template depending on the context.
    return render_to_response(
        'registration/login.html',
        {'userregform': user_form,
         'clientform': profile_form,
         'registered': registered,
         },
        context)


def remove_from_cart(request):
    if not request.user.is_authenticated:
        return HttpResponse(
            json.dumps({'error': "NOT AUTHORISED"}),
            content_type="application/json"
        )
    if request.is_ajax():
        link = request.POST.get('link')
        item = get_object_or_404(ItemModel, link=link)
        try:
            request.user.cart.cartitem_set.get(item=item).delete()
        except Cart.DoesNotExist:
            request.user.cart = Cart.objects.create(owner=request.user)
        except CartItem.DoesNotExist:
            pass
        request.user.cart.save()
        response_data = {
            'total_items': request.user.cart.item_count(),
            'total_price': request.user.cart.sum_price(),
        }
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json"
        )
    return HttpResponseRedirect('/')