from django.shortcuts import render, redirect
from django.contrib import messages
from pizzafront.models import *
# from django.http import HttpResponse

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm



# Create your views here.
def getPizza(request):
    response = Pizza.objects.all()
    return render(request, 'index.html', {'pizza': list(response)})

def getOffers(request):
    response = Offer.objects.all()
    return render(request, 'index.html', {'offer': list(response)})


def userlogin(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/menu/')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'userlogin.html', {'form': form})