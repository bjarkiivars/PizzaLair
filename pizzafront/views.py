from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from pizzafront.models import *
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm

from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from django.urls import reverse

from .forms import RegisterForm


# Create your views here.
def getPizza(request):
    pizzas = Pizza.objects.all()
    pizza_type = PizzaType.objects.all()

    # getting all the toppings for each pizza
    pizza_data = []
    for pizza in pizzas:
        toppings = pizza.topping.all()
        pizza_data.append({
            'pizza': pizza,
            'toppings': toppings
        })

    # The data that is sent to the index html
    context = {
        'pizza_data': pizza_data,
        'pizzatype': list(pizza_type)
    }
    # Extracting the human-readable string for pizza types.
    for typeOfPizza in pizza_type:
        typeOfPizza.name_display = typeOfPizza.get_name_display()

    return render(request, 'index.html', context)


def getOffers(request):
    offers = Offer.objects.all()
    pizzas = Pizza.objects.all()
    pizza_type = PizzaType.objects.all()

    # getting all the toppings for each pizza
    pizza_data = []
    for pizza in pizzas:
        toppings = pizza.topping.all()
        pizza_data.append({
            'pizza': pizza,
            'toppings': toppings
        })

    # Extracting the human-readable string for pizza types.
    for typeOfPizza in pizza_type:
        typeOfPizza.name_display = typeOfPizza.get_name_display()

    # The data that is sent to the index html
    context = {
        'offers': list(offers),
        'pizza_data': pizza_data,
        'pizzatype': list(pizza_type)
    }

    return render(request, 'index.html', context)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect(reverse('login'))
        else:
            messages.error(request, 'Registration failed. Please check the form for errors.')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


'''userlogin: IN DEVELOPMENT'''


def userlogin(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # return redirect('menu')
            return redirect(reverse('menu'))
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'userlogin.html', {'form': form})


# Add to cart functionality Requires user authentication
# TODO: Finish implementing view, so we can post the cart to the DB
# For now I will force the User in my request to test
def addToCart(request, pizza_id, user_id):
    # retrieve the pizza object from the pizza_id param
    pizza = Pizza.objects.get(id=pizza_id)

    # get the current user
    # TODO: Need to authenticate the user
    # Temporary:
    user = User.objects.get(id=user_id)

    try:
        cart = Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=user, cart_sum=0)

    # check if pizza already exists in cart
    existing_pizza = cart.pizza.filter(name=pizza.name, size=pizza.size, topping__in=pizza.topping.all()).first()

    if existing_pizza:
        # if pizza already exists, increment quantity instead of adding a new one
        cart_pizza = CartPizza.objects.get(cart=cart, pizza=existing_pizza)
        cart_pizza.quantity += 1
        cart_pizza.save()
    else:
        # if pizza does not exist, add it to cart with quantity=1
        cart_pizza = CartPizza.objects.create(cart=cart, pizza=pizza, quantity=1)

    cart.cart_sum += pizza.price
    cart.save()
    success = 'Added successfully to cart'
    return HttpResponse(success)


def cart(request, user_id):
    user = User.objects.get(id=user_id)
    cart = Cart.objects.filter(user=user).prefetch_related('cartpizza_set__pizza')

    # serialize the cart data to JSON
    data = {
        'cart': [{
            'created_at': str(item.created_at),
            'cart_sum': item.cart_sum,
            'pizza': [{
                'name': cart_pizza.pizza.name,
                'price': cart_pizza.pizza.price,
                'id': cart_pizza.pizza.id,
                'quantity': cart_pizza.quantity
            } for cart_pizza in item.cartpizza_set.all()]
        } for item in cart
        ]}

    return JsonResponse(data)


def deleteCartItem(request, user_id, pizza_id):
    try:
        # Get the Cart for this user, or throw not found
        cart = get_object_or_404(Cart, user_id=user_id)
        # Get the specific pizza, or throw not found
        pizza = get_object_or_404(Pizza, id=pizza_id)
        # get the CartPizza object for this cart and pizza
        cart_pizza = get_object_or_404(CartPizza, cart=cart, pizza=pizza)
        # if the quantity is greater than 1, decrement the quantity and save
        if cart_pizza.quantity > 1:
            cart_pizza.quantity -= 1
            cart_pizza.save()
            # re-calculate the sum
            cart.cart_sum -= pizza.price
            # update changes
            cart.save()
        else:
            # remove the CartPizza object from the cart
            cart_pizza.delete()
            # remove the pizza from the cart
            cart.pizza.remove(pizza)
            # re-calculate the sum
            cart.cart_sum -= pizza.price
            # update changes
            cart.save()
        # return json message
        return JsonResponse({'message': 'Cart item deleted successfully'})
    except Exception as e:
        print(e)
        # indicating server error
        return JsonResponse({'message': 'Error deleting item'}, status=500)


# Return the sum of the cart
def cartSum(request, user_id):
    # Get the Cart for this user, or throw not found
    cart = get_object_or_404(Cart, user_id=user_id)

    totalAmount = cart.cart_sum

    return JsonResponse({'totalAmount': totalAmount}, status=200)


# Return the amount of items currently in the cart
def countCart(request, user_id):
    # Get the cart for this user, or throw not found
    cart = get_object_or_404(Cart, user_id=user_id)

    item_counter = cart.pizza.count()

    return JsonResponse({'countedItems': item_counter}, status=200)
