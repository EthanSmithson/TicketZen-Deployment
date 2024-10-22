from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from .models import User, savedTicket, recentSearch
from .serializers import UserSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .forms import UploadForm, LoginForm
from django.contrib.auth import login, authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
import random
import uuid
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .utils import generate_token
from django.urls import reverse
import  threading
from django.utils.html import strip_tags
from amadeus import Client, ResponseError, Location
from django.views.decorators.csrf import csrf_exempt
import json
import ast
from .flight import Flight
from .booking import Booking
import geocoder
import datetime


amadeus = Client(
        client_id='NLVL5RdwIU8G5G3qpx72ds9gzQ1utroh',
        client_secret='fxVqNnvVr9ez3mxT')

class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


def send_activate_email(user, request):
    current_site= get_current_site(request)
    email_subject = 'Activate your account'
    email_body = render_to_string('activateEmail.html', {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': generate_token.make_token(user)
    })

    plain_message = strip_tags(email_body)

    email = EmailMultiAlternatives(subject=email_subject, body=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                 to=[user.email]
                 )
    
    email.attach_alternative(email_body, "text/html")

    EmailThread(email).start()

def index(request):
    return render(request, 'index.html')

# def about(request):
#     return render(request, 'tickets.html')

# @api_view(['GET', 'POST'])
def register(request):

    if request.POST:
        form = UploadForm(request.POST)

        username = request.POST.get('username')
        email = request.POST.get('email')
        user = User.objects.all()

        if user.filter(username=username).exists():
            return render(request, 'register.html', {'form':form})
        
        if user.filter(email=email).exists():
            return render(request, 'register.html', {'form':form})

        if form.is_valid():
            if form.is_valid():  
 
                post = form.save(commit = False)
                post.is_active = False

                myUUID = uuid.uuid1(random.randint(0, 281474976710655))
                post.activateUUID = myUUID


                post.save() 

                send_activate_email(post, request)

                messages.add_message(request, messages.SUCCESS, 
                                     "Account confirmation email sent, please verify.", extra_tags="email")
                
                return redirect('login')

                # return render(request, 'login.html', {'message': "Please Check Email to Confirm Account"})
                # return HttpResponse('Please confirm your email address to complete the registration')
                
        else:
            return render(request, "register.html", {'form':form})  
        
    else:

        form = UploadForm(None)   
        return render(request, 'register.html', {'form':form})
    #         form.save()
    #     return redirect(register)
    # return render(request, 'register.html', {'form': UploadForm})
    


    return render(request, 'register.html')

def activate_user(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))

        user = User.objects.get(pk=uid)
    except Exception as e:
        user = None

    if user and generate_token.check_token(user, token):
        user.confirmed = 1
        user.save()
        messages.add_message(request, messages.SUCCESS, 'Email Verified!', extra_tags="email")
        return redirect(reverse('login'))
    
    return render(request, 'activate-failed.html', {"user": user})


def check_username(request):

    username = request.POST.get('username')
    user = User.objects.all()
    print(user.filter(username=username).exists())

    if user.filter(username=username).exists():
        return HttpResponse('<p style="color: red">username already exists</p>')
    elif username == "":
        return HttpResponse('<p></p>')
    else:
        return HttpResponse('<p style="color: green">username is available</p>')
    
def check_email(request):

    email = request.POST.get('email')
    user = User.objects.all()
    print(user.filter(email=email).exists())

    if user.filter(email=email).exists():
        return HttpResponse('<p style="color: red">Email already exists</p>')
    elif email == "":
        return HttpResponse('<p></p>')
    else:
        return HttpResponse('<p style="color: green">Email is available</p>')
    

def login(request):

    if request.POST:
        form = LoginForm(request.POST)

        # context = {'has_error': False, 'date': request.POST}
        password = request.POST.get('password')
        email = request.POST.get('email')
        user = User.objects.all()

        myUser = user.filter(email=email).values()
        if len(myUser) > 0:
            getID = myUser[0]
            myID = getID['id']

        if user.filter(email=email, password=password, confirmed = 1).exists() == False:
            form = LoginForm(None)   

            messages.add_message(request, messages.ERROR, 
                                            "Incorrect Credentials!", extra_tags="login")
            
            return render(request, 'login.html', {'form':form})

        recentSearches = recentSearch.objects.all()
        myRecentSearches = recentSearches.filter(uid=myID).values()
        # print(myRecentSearches)

        g = geocoder.ip("me")
        print(g.latlng)

        data = amadeus.reference_data.locations.airports.get(
                    latitude=g.latlng[0], longitude=g.latlng[1]
                ).data
        
        # print(data[0])

        closestAirport = data[0]
        closestAirportCode = closestAirport["iataCode"]
        print(closestAirportCode)
        closestAirportName = closestAirport["name"]

        try:
            data2 = amadeus.shopping.flight_destinations.get(
                        origin="MAD"
                    ).data
            
            # print(data2)
            inspirationResult = data2
        except:
            inspirationResult = None
            inspirationResultError = "No New Flights based " + closestAirportName

        # print(myUser[0])

        if user.filter(email=email, password=password, confirmed = 1).exists():
            if inspirationResult == None:
                return render(request, 'home.html', {'form':myUser[0], 'currentLocation':closestAirportName, 'inspirationError':inspirationResultError, 'recents':myRecentSearches})
            else:
                return render(request, 'home.html', {'form':myUser[0], 'currentLocation':closestAirportName, 'inspiration': inspirationResult, 'recents':myRecentSearches})
            # return render(request, 'home.html', {'form':myUser[0]})

        else:         
            form = LoginForm(None)   

            messages.add_message(request, messages.ERROR, 
                                            "Incorrect Credentials!", extra_tags="login")
            
            return render(request, 'login.html', {'form':form})

    else:

        form = LoginForm(None)   
        return render(request, 'login.html', {'form':form})
    
def updateSidebarStatus(request):
    id = request.GET.get('data')
    users = User.objects.all()
    myUser = users.filter(id=id).values()[0]
    myUserSidebar = myUser["sidebarStatus"]

    if myUserSidebar == 1 :
        User.objects.filter(id=id).update(sidebarStatus = 0)
    else :
        User.objects.filter(id=id).update(sidebarStatus = 1)

    return HttpResponse(status=200)

def updateDisplay(request):
    id = request.GET.get('id')
    print(id)
    users = User.objects.all()
    myUser = users.filter(id=id).values()[0]
    myUserSidebar = myUser["displayStatus"]

    if myUserSidebar == 1 :
        User.objects.filter(id=id).update(displayStatus = 0)
    else :
        User.objects.filter(id=id).update(displayStatus = 1)

    return HttpResponse(status=200)

@csrf_exempt
def searchRecent(request):
    id = request.POST.get("id")
    uid = request.POST.get("uid")
    # myRecentSearchId = request.POST.get("id")
    # allRecentsSearches = recentSearch.objects.all()
    # myRecentSearch = allRecentsSearches.filter(id=myRecentSearchId).values()[0]

    users = User.objects.all()

    myUser = users.filter(id=uid).values()

    origin = request.POST.get("origin")
    destination = request.POST.get("destination")
    departure_date = request.POST.get("departureDate")
    return_date = request.POST.get("returnDate")

    # origin = myRecentSearch['origin']
    # destination = myRecentSearch['destination']
    # departure_date = myRecentSearch['departureDate']
    # return_date = myRecentSearch['returnDate']
    # uid = myRecentSearch['uid']

    kwargs = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": 1,
    }

    # For a round trip, we use AI Trip Purpose Prediction
    # to predict if it is a leisure or business trip
    tripPurpose = ""
    if return_date:
        # Adds the parameter returnDate for the Flight Offers Search API call
        kwargs["returnDate"] = return_date
        kwargs_trip_purpose = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "returnDate": return_date,
        }
        try:
            # Calls Trip Purpose Prediction API
            trip_purpose_response = amadeus.travel.predictions.trip_purpose.get(
                **kwargs_trip_purpose
            ).data
            tripPurpose = trip_purpose_response["result"]
        except ResponseError as error:
            messages.add_message(
                request, messages.ERROR, error.response.result["errors"][0]["detail"]
            )
            return render(request, "tickets.html", {'form':myUser[0]})

    # Perform flight search based on previous inputs
    if origin and destination and departure_date:
        try:
            search_flights = amadeus.shopping.flight_offers_search.get(**kwargs)
        except ResponseError as error:
            messages.add_message(
                request, messages.ERROR, error.response.result["errors"][0]["detail"]
            )
            return render(request, "tickets.html", {'form':myUser[0]})
        search_flights_returned = []
        response = ""
        for flight in search_flights.data:
            offer = Flight(flight).construct_flights()
            search_flights_returned.append(offer)
            response = zip(search_flights_returned, search_flights.data)

        return render(
            request,
            "results.html",
            {
                "response": response,
                "origin": origin,
                "destination": destination,
                "departureDate": departure_date,
                "returnDate": return_date,
                'form': myUser[0],
                # "tripPurpose": tripPurpose
            },
        )
    return render(request, "results.html", {'form':myUser[0]})

    # return render(request, 'tickets.html')
    

def home(request):

    uid = request.GET.get('uid')
    users = User.objects.all()

    myUser = users.filter(id=uid).values()

    g = geocoder.ip("me")
    print(g.latlng)

    recentSearches = recentSearch.objects.all()
    myRecentSearches = recentSearches.filter(uid=uid).values()

    dateDiff = datetime.date.today() - datetime.timedelta(days=2)
    print(dateDiff)
    deleteOldRecents = recentSearches.filter(uid=uid, creationDtTm__lte=dateDiff)
    print(deleteOldRecents)
    deleteOldRecents.delete()

    data = amadeus.reference_data.locations.airports.get(
                latitude=g.latlng[0], longitude=g.latlng[1]
            ).data
    
    print(data[0])

    closestAirport = data[0]
    closestAirportCode = closestAirport["iataCode"]
    print(closestAirportCode)
    closestAirportName = closestAirport["name"]

    try:
        data2 = amadeus.shopping.flight_destinations.get(
                    origin="MAD"
                ).data
        
        print(data2)
        inspirationResult = data2
    except:
        inspirationResult = None
        inspirationResultError = "No New Flights based " + closestAirportName

    if inspirationResult == None:
        return render(request, 'home.html', {'form':myUser[0], 'currentLocation':closestAirportName, 'inspirationError':inspirationResultError, 'recents':myRecentSearches})
    else:
        return render(request, 'home.html', {'form':myUser[0], 'currentLocation':closestAirportName, 'inspiration': inspirationResult, 'recents':myRecentSearches})
    
def myRecents(request):
    searchKey = request.GET.get('searchKey')
    id = request.GET.get("id")
    resultList = []
    # print(searchKey)
    myRecents = savedTicket.objects.all()
    filteredRecents = myRecents.filter(origin__icontains=searchKey, uid=id).values("id", "origin", "destination", "departureDate", "returnDate", "uid") | myRecents.filter(destination__icontains=searchKey, uid=id).values("id", "origin", "destination", "departureDate", "returnDate", "uid")
    print(filteredRecents)

    # print("this: " + json.dumps(list(filteredRecents)))
    html = render_to_string('searched.html', {'data': filteredRecents})
    
    return HttpResponse(html)

@csrf_exempt
def searchedLookup(request):
    id = request.POST.get("id")
    uid = request.POST.get("uid")

    print(request.POST)

    users = User.objects.all()

    myUser = users.filter(id=uid).values()
    # print(myUser)
    savedTickets = savedTicket.objects.all()
    mysavedTickets = savedTickets.filter(uid=uid).values("zeroFlightTotalDuration", "zeroFirstFlightDepartureDate", "zeroFirstFlightDepartureAirport", "zeroFirstFlightArrivalAirport", "zeroFirstFlightArrivalDate", "oneFirstFlightDepartureAirport", "oneFlightTotalDuration", "oneFirstFlightDepartureDate", "oneFirstFlightArrivalAirport", "oneFirstFlightArrivalDate", "origin", "destination", "departureDate", "returnDate", "price", "id", "uid")

    return render(request, 'myTickets.html', {'form':myUser[0], 'tickets': mysavedTickets, 'searchedId': id})

# def settings(request):
#     uid = request.GET.get('uid')
#     users = User.objects.all()

#     myUser = users.filter(id=uid).values()

#     html = render_to_string('settings.html', {'form':myUser[0]})
    
#     return HttpResponse(html)
    
    # return render(request, 'settings.html', {'form':myUser[0]})

def tickets(request):  
    print(request.GET.get('uid'))
    uid = request.GET.get('uid')
    users = User.objects.all()

    myUser = users.filter(id=uid).values()

    return render(request, 'tickets.html', {'form':myUser[0]})

def explore(request):
    return render(request, 'explore.html')


def save_explore_ticket(request, total, origin, destination, departureDate, returnDate, uid):
    thisId = uid
    users = User.objects.all()

    myUser = users.filter(id=thisId).values()
    
    newTicket = savedTicket(uid=thisId
                            , price=total
                            , origin=origin
                            , destination=destination
                            , departureDate=departureDate
                            , returnDate=returnDate
                        )
    newTicket.save()
    return render(request, 'home.html', {'form':myUser[0]})


def save_ticket(request, zeroFlightTotalDuration, zeroFirstFlightDepartureDate, zeroFirstFlightDepartureAirport, zeroFirstFlightArrivalAirport, zeroFirstFlightArrivalDate, oneFirstFlightDepartureAirport, oneFlightTotalDuration, oneFirstFlightDepartureDate, oneFirstFlightArrivalAirport, oneFirstFlightArrivalDate, origin, destination, departureDate, returnDate, price, uid):
    thisId = uid
    users = User.objects.all()

    myUser = users.filter(id=thisId).values()

    newTicket = savedTicket(uid=thisId, zeroFlightTotalDuration=zeroFlightTotalDuration
                            , zeroFirstFlightDepartureDate=zeroFirstFlightDepartureDate
                            , zeroFirstFlightDepartureAirport=zeroFirstFlightDepartureAirport
                            , zeroFirstFlightArrivalAirport=zeroFirstFlightArrivalAirport
                            , zeroFirstFlightArrivalDate=zeroFirstFlightArrivalDate
                            , oneFirstFlightDepartureAirport=oneFirstFlightDepartureAirport
                            , oneFlightTotalDuration=oneFlightTotalDuration
                            , oneFirstFlightDepartureDate=oneFirstFlightDepartureDate
                            , oneFirstFlightArrivalAirport=oneFirstFlightArrivalAirport
                            , oneFirstFlightArrivalDate=oneFirstFlightArrivalDate
                            , origin=origin
                            , destination=destination
                            , departureDate=departureDate
                            , returnDate=returnDate
                            , price=price
                            , originLocation=zeroFirstFlightDepartureAirport
                            , destinationLocation=oneFirstFlightArrivalDate
                        )
    newTicket.save()
    return render(request, 'tickets.html', {'form':myUser[0]})

def delete_ticket(request, uid, id):
    thisId = uid
    ticketId = id
    users = User.objects.all()

    print(thisId, ticketId)

    myUser = users.filter(id=thisId).values()

    savedTickets = savedTicket.objects.all()

    deleteTicket = savedTickets.filter(id=ticketId)
    deleteTicket.delete()

    mysavedTickets = savedTickets.filter(uid=thisId).values("zeroFlightTotalDuration", "zeroFirstFlightDepartureDate", "zeroFirstFlightDepartureAirport", "zeroFirstFlightArrivalAirport", "zeroFirstFlightArrivalDate", "oneFirstFlightDepartureAirport", "oneFlightTotalDuration", "oneFirstFlightDepartureDate", "oneFirstFlightArrivalAirport", "oneFirstFlightArrivalDate", "origin", "destination", "departureDate", "returnDate", "price", "id")

    # myUser['ticket'] = savedTickets
    
    return render(request, 'myTickets.html', {'form':myUser[0], 'tickets': mysavedTickets})


def myTickets(request):
    uid = request.GET.get('uid')
    users = User.objects.all()

    myUser = users.filter(id=uid).values()
    # print(myUser)
    savedTickets = savedTicket.objects.all()
    mysavedTickets = savedTickets.filter(uid=uid).values("zeroFlightTotalDuration", "zeroFirstFlightDepartureDate", "zeroFirstFlightDepartureAirport", "zeroFirstFlightArrivalAirport", "zeroFirstFlightArrivalDate", "oneFirstFlightDepartureAirport", "oneFlightTotalDuration", "oneFirstFlightDepartureDate", "oneFirstFlightArrivalAirport", "oneFirstFlightArrivalDate", "origin", "destination", "departureDate", "returnDate", "price", "id")
    print(mysavedTickets)

    # myUser['ticket'] = savedTickets
    
    return render(request, 'myTickets.html', {'form':myUser[0], 'tickets': mysavedTickets})


def findTickets(request):
    print(request.POST)
    # Retrieve data from the UI form
    origin = request.POST.get("Origin")[0:3]
    destination = request.POST.get("Destination")[0:3]
    departure_date = request.POST.get("Departuredate")
    return_date = request.POST.get("Returndate")
    uid = request.POST.get("uid")
    originLocation = request.POST.get("Origin").replace(",", "")
    destinationLocation = request.POST.get("Destination").replace(",", "")

    if origin != "" and destination != "" and  departure_date != "" and return_date != "":
        recentSearchedTicket = recentSearch(uid=uid
                                , origin=origin
                                , destination=destination
                                , departureDate=departure_date
                                , returnDate=return_date
                                , creationDtTm=datetime.date.today()
                            )
        
        recentSearchedTicket.save()

    users = User.objects.all()

    myUser = users.filter(id=uid).values()

    # Prepare url parameters for search
    kwargs = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": 1,
    }

    # For a round trip, we use AI Trip Purpose Prediction
    # to predict if it is a leisure or business trip
    tripPurpose = ""
    if return_date:
        # Adds the parameter returnDate for the Flight Offers Search API call
        kwargs["returnDate"] = return_date
        kwargs_trip_purpose = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "returnDate": return_date,
        }
        try:
            # Calls Trip Purpose Prediction API
            trip_purpose_response = amadeus.travel.predictions.trip_purpose.get(
                **kwargs_trip_purpose
            ).data
            tripPurpose = trip_purpose_response["result"]
        except ResponseError as error:
            messages.add_message(
                request, messages.ERROR, error.response.result["errors"][0]["detail"]
            )
            return render(request, "tickets.html", {})

    # Perform flight search based on previous inputs
    if origin and destination and departure_date:
        try:
            search_flights = amadeus.shopping.flight_offers_search.get(**kwargs)
            print(search_flights.data)
        except ResponseError as error:
            messages.add_message(
                request, messages.ERROR, error.response.result["errors"][0]["detail"]
            )
            return render(request, "tickets.html", {})
        search_flights_returned = []
        response = ""
        for flight in search_flights.data:
            offer = Flight(flight).construct_flights()
            search_flights_returned.append(offer)
            response = zip(search_flights_returned, search_flights.data)

        return render(
            request,
            "results.html",
            {
                "response": response,
                "origin": origin,
                "destination": destination,
                "departureDate": departure_date,
                "returnDate": return_date,
                'form': myUser[0],
                'originLocation': originLocation,
                'destinationLocation': destinationLocation
                # "tripPurpose": tripPurpose
            },
        )
    return render(request, "results.html", {'form':myUser[0]})


def book_flight(request, flight):
    # Create a fake traveler profile for booking
    traveler = {
        "id": "1",
        "dateOfBirth": "1982-01-16",
        "name": {"firstName": "JORGE", "lastName": "GONZALES"},
        "gender": "MALE",
        "contact": {
            "emailAddress": "jorge.gonzales833@telefonica.es",
            "phones": [
                {
                    "deviceType": "MOBILE",
                    "countryCallingCode": "34",
                    "number": "480080076",
                }
            ],
        },
        "documents": [
            {
                "documentType": "PASSPORT",
                "birthPlace": "Madrid",
                "issuanceLocation": "Madrid",
                "issuanceDate": "2015-04-14",
                "number": "00000000",
                "expiryDate": "2025-04-14",
                "issuanceCountry": "ES",
                "validityCountry": "ES",
                "nationality": "ES",
                "holder": True,
            }
        ],
    }
    # Use Flight Offers Price to confirm price and availability
    try:
        flight_price_confirmed = amadeus.shopping.flight_offers.pricing.post(
            ast.literal_eval(flight)
        ).data["flightOffers"]
    except (ResponseError, KeyError, AttributeError) as error:
        messages.add_message(request, messages.ERROR, error.response.body)
        return render(request, "demo/book_flight.html", {})

    # Use Flight Create Orders to perform the booking
    try:
        order = amadeus.booking.flight_orders.post(
            flight_price_confirmed, traveler
        ).data
    except (ResponseError, KeyError, AttributeError) as error:
        messages.add_message(
            request, messages.ERROR, error.response.result["errors"][0]["detail"]
        )
        return render(request, "demo/book_flight.html", {})

    passenger_name_record = []
    booking = Booking(order).construct_booking()
    passenger_name_record.append(booking)

    return render(request, "demo/book_flight.html", {"response": passenger_name_record})


def origin_airport_search(request):
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        try:
            data = amadeus.reference_data.locations.get(
                keyword=request.GET.get("term", None), subType=Location.ANY
            ).data
        except (ResponseError, KeyError, AttributeError) as error:
            messages.add_message(
                request, messages.ERROR, error.response.result["errors"][0]["detail"]
            )
    return HttpResponse(get_city_airport_list(data), "application/json")


def destination_airport_search(request):
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        try:
            data = amadeus.reference_data.locations.get(
                keyword=request.GET.get("term", None), subType=Location.ANY
            ).data
        except (ResponseError, KeyError, AttributeError) as error:
            messages.add_message(
                request, messages.ERROR, error.response.result["errors"][0]["detail"]
            )
    return HttpResponse(get_city_airport_list(data), "application/json")


def get_city_airport_list(data):
    result = []
    for i, val in enumerate(data):
        result.append(data[i]["iataCode"] + ", " + data[i]["name"])
    result = list(dict.fromkeys(result))
    return json.dumps(result)
