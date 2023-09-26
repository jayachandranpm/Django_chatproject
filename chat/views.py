from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from chat.models import Message
from chat.forms import SignUpForm
from chat.serializers import MessageSerializer, UserSerializer


from django.contrib import messages

def index(request):
    if request.user.is_authenticated:
        return redirect('chats')
    
    if request.method == 'GET':
        return render(request, 'chat/index.html', {})
    
    if request.method == "POST":
        username, password = request.POST['username'], request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'User successfully logged in.')
        else:
            messages.error(request, 'User does not exist.')
        
        return redirect('chats')


@csrf_exempt
def message_list(request, sender=None, receiver=None):
    """
    List all required messages, or create a new message.
    """
    if request.method == 'GET':
        messages = Message.objects.filter(sender_id=sender, receiver_id=receiver, is_read=False)
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        for message in messages:
            message.is_read = True
            message.save()
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


def register_view(request):
    """
    Render registration template
    """
    if request.method == 'POST':
        print("working1")
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user.set_password(password)
            user.save()
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('chats')
    else:
       
        form = SignUpForm()
    template = 'chat/register.html'
    context = {'form':form}
    return render(request, template, context)


def chat_view(request):
    if not request.user.is_authenticated:
        return redirect('index')
    if request.method == "GET":
        return render(request, 'chat/chat.html',
                      {'users': User.objects.exclude(username=request.user.username)})


def message_view(request, sender, receiver):
    if not request.user.is_authenticated:
        return redirect('index')
    if request.method == "GET":
        return render(request, "chat/messages.html",
                      {'users': User.objects.exclude(username=request.user.username),
                       'receiver': User.objects.get(id=receiver),
                       'messages': Message.objects.filter(sender_id=sender, receiver_id=receiver) |
                                   Message.objects.filter(sender_id=receiver, receiver_id=sender)})



import json
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status
from django.templatetags.static import static

# Construct the URL for the JSON file using the static() function
json_file_path = 'C:\\AI PROJECTS\\chatting-app-django\\static\\json\\users.json'


# Load the JSON data from the file
with open(json_file_path, 'r') as json_file:
    json_data = json.load(json_file)
    
@api_view(['GET'])
def api_suggested_friends(request, user_id):
    # Convert user_id to int (if needed)
    user_id = int(user_id)

    # Find the user with the given user_id in the JSON data
    user = None
    for user_data in json_data['users']:
        if user_data['id'] == user_id:
            user = user_data
            break

    if user:
        user_interests = user['interests']

        # Calculate friend recommendations based on interests
        recommendations = calculate_recommendations(user_id, user['interests'])


        # Return the top 5 recommended friends (if available)
        top_recommendations = recommendations[:5]
        response_data = {
            'user': {
                'id': user_id,
                'name': user['name'],
                'age': user['age'],
                'interests': user_interests,
            },
            'recommended_friends': top_recommendations
        }

        return JsonResponse(response_data, status=status.HTTP_200_OK)
    else:
        return JsonResponse({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
def calculate_recommendations(current_user_id, user_interests):
    # Initialize an empty list to store recommended friends
    recommended_friends = []

    # Iterate through all users in the JSON data
    for user_info in json_data['users']:
        if user_info['id'] == current_user_id:
            # Skip the current user
            continue

        # Calculate a score for the user based on shared interests
        score = calculate_interests_similarity(user_interests, user_info['interests'])

        # Store the user's data and score in the recommended_friends list
        user_data = {
            'id': user_info['id'],
            'name': user_info['name'],
            'age': user_info['age'],
            'interests': user_info['interests'],
            'score': score
        }
        recommended_friends.append(user_data)

    # Sort recommended friends by score in descending order
    recommended_friends.sort(key=lambda x: x['score'], reverse=True)

    return recommended_friends

def calculate_interests_similarity(user_interests, other_user_interests):
    # Implement a scoring mechanism based on shared interests
    shared_interests = set(user_interests.keys()) & set(other_user_interests.keys())
    
    # Calculate a simple score as the number of shared interests
    score = len(shared_interests)
    
    return score


