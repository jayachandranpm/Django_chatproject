import json # Moved to top
import os # For path joining
from django.conf import settings # For BASE_DIR

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse # Removed HttpResponse as it's not used
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from rest_framework.parsers import JSONParser
# from rest_framework.decorators import api_view # Commented out, not used
# from rest_framework import status # Imported but not used after api_view removal

from .models import Message
from .forms import SignUpForm
from .serializers import MessageSerializer, UserSerializer
# from django.templatetags.static import static # Not used

# View for the homepage/login page.
def index(request):
    # If user is already authenticated, redirect to the main chat page.
    if request.user.is_authenticated:
        return redirect('chats')
    
    # Handle GET request: display the login form.
    if request.method == 'GET':
        return render(request, 'chat/index.html', {})
    
    # Handle POST request: process login attempt.
    if request.method == "POST":
        username, password = request.POST['username'], request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'User successfully logged in.')
        else:
            # Invalid credentials, show error message.
            messages.error(request, 'Invalid username or password.') # Changed from "User does not exist" for better security practice
        
        return redirect('chats') # Redirect to chats page (will go to index if login failed and index redirects auth users)


# API endpoint for fetching and sending messages (used by AJAX in chat.js).
@csrf_exempt # Exempt from CSRF protection; consider implications and alternatives for production.
def message_list(request, sender=None, receiver=None):
    """
    Handles GET requests to fetch unread messages for a chat pair (sender to receiver)
    and POST requests to submit a new message.
    """
    if request.method == 'GET':
        # Fetch unread messages from 'sender' to 'receiver'.
        # Note: 'sender' and 'receiver' are path parameters from the URL.
        # In chat.js, sender_id is the other user, receiver_id is the current user.
        user_messages = Message.objects.filter(sender_id=sender, receiver_id=receiver, is_read=False)
        serializer = MessageSerializer(user_messages, many=True, context={'request': request})
        # Mark fetched messages as read.
        for msg in user_messages: # Renamed 'messages' to 'msg' to avoid conflict with django.contrib.messages
            msg.is_read = True
            msg.save()
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        # Create a new message.
        data = JSONParser().parse(request)
        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201) # Return created message data.
        return JsonResponse(serializer.errors, status=400) # Return errors if invalid.


# View for user registration.
def register_view(request):
    if request.user.is_authenticated:
        return redirect('chats') # Redirect if already logged in

    if request.method == 'POST':
        
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Process the submitted registration form.
            user = form.save(commit=False) # Create user object but don't save yet.
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1'] # Assuming password confirmation is handled in form.
            user.set_password(password) # Hash the password.
            user.save() # Save the user.
            # Authenticate and log in the newly registered user.
            auth_user = authenticate(username=username, password=password) # Renamed 'user' to 'auth_user'
            if auth_user is not None:
                if auth_user.is_active:
                    login(request, auth_user)
                    messages.success(request, f"Welcome {username}! Registration successful.")
                    return redirect('chats')
            messages.error(request, "Registration successful, but auto-login failed. Please log in manually.")
            return redirect('index') # Or some other appropriate page
    else:
        # Display an empty registration form for GET requests.
        form = SignUpForm()
    template = 'chat/register.html'
    context = {'form': form}
    return render(request, template, context)


# View for the main chat interface.
@login_required # Ensures only logged-in users can access.
def chat_view(request):
    # Handles GET request to display the chat page.
    # The user list for starting new chats is passed in the context.
    if request.method == "GET":
        return render(request, 'chat/chat.html',
                      {'users': User.objects.exclude(username=request.user.username)}) # Exclude self from user list.


# View for displaying messages within a specific chat.
# This view is typically loaded into a part of the chat_view page.
@login_required # Ensures only logged-in users can access.
def message_view(request, sender, receiver):
    # Handles GET request to display messages between 'sender' and 'receiver'.
    # 'sender' and 'receiver' are user IDs from the URL.
    if request.method == "GET":
        # Security check: Ensure the logged-in user is part of this chat.
        if request.user.id != sender and request.user.id != receiver:
            messages.error(request, "You are not authorized to view this chat.")
            return redirect('chats') # Redirect to main chat page or an error page.

        # Fetch the other user in this chat.
        # The 'receiver' URL parameter is assumed to be the ID of the other user in this context.
        other_user = User.objects.get(id=receiver)

        # Fetch all messages exchanged between the logged-in user and the other user.
        # Note: Model's Meta ordering ('timestamp',) handles sorting.
        chat_messages = Message.objects.filter(sender_id=request.user.id, receiver_id=other_user.id) | \
                        Message.objects.filter(sender_id=other_user.id, receiver_id=request.user.id)

        context = {
            'users': User.objects.exclude(username=request.user.username), # For user list sidebar.
            'receiver': other_user, # The other user in this specific chat window.
            'messages': chat_messages
        }
        return render(request, "chat/messages.html", context)


# Path for the JSON file, made portable
# Assumes 'static/json/users.json' relative to BASE_DIR
# For a production setup, consider Django's staticfiles infrastructure more deeply.
JSON_FILE_PATH = os.path.join(settings.BASE_DIR, 'static', 'json', 'users.json')

# Load user data from JSON for friend recommendations.
# This is done once when the module is loaded.
# Considerations:
# - If the JSON file changes, the server needs a restart to pick up changes.
# - File I/O at import time can be problematic if settings (like BASE_DIR) are not fully configured.
# - For larger applications, this data would typically be in the database.
try:
    with open(JSON_FILE_PATH, 'r') as json_file:
        users_json_data = json.load(json_file)
except FileNotFoundError:
    users_json_data = {"users": []}
    # Log this error in a real application e.g., import logging; logging.error(...)
    print(f"ERROR: User data file not found at {JSON_FILE_PATH}. Friend recommendations will be empty.")


# View for displaying suggested friends to the logged-in user.
@login_required
def suggested_friends_view(request):
    logged_in_user_id = request.user.id # Use a more descriptive variable name

    # Find the profile of the logged-in user in the loaded JSON data.
    current_user_profile_json = None
    for user_profile in users_json_data['users']:
        if user_profile['id'] == logged_in_user_id:
            current_user_profile_json = user_profile
            break

    if current_user_profile_json:
        user_interests = current_user_profile_json['interests']
        # Calculate recommendations based on the logged-in user's interests and all users' data.
        all_recommendations = calculate_recommendations(logged_in_user_id, user_interests, users_json_data['users'])

        # Limit to top 5 recommendations.
        top_recommendations = all_recommendations[:5]

        context = {
            # Pass current user's JSON profile data (optional, if template needs it).
            'user_profile_data': current_user_profile_json,
            'suggested_friends': top_recommendations,
        }
        return render(request, 'chat/suggested_friends.html', context)
    else:
        # Handle case where logged-in user's profile is not found in the JSON data.
        messages.error(request, 'Your profile data was not found, so we cannot provide friend suggestions at this time.')
        return render(request, 'chat/suggested_friends.html', {'suggested_friends': []})


# Helper function for friend recommendation logic.
def calculate_recommendations(current_user_id, current_user_interests, all_users_data):
    """
    Calculates a list of recommended friends based on shared interests.
    Excludes the current user from recommendations.
    Sorts recommendations by a similarity score.
    """
    recommended_friends = []
    for other_user_profile in all_users_data:
        if other_user_profile['id'] == current_user_id:
            continue # Skip self.

        # Calculate similarity score (e.g., based on common interests).
        similarity_score = calculate_interests_similarity(current_user_interests, other_user_profile['interests'])

        # Store the user's data and score in the recommended_friends list
        # Could add a threshold: if similarity_score > 0 ...
        recommended_friends.append({
            'id': other_user_profile['id'],
            'name': other_user_profile['name'],
            'age': other_user_profile['age'], # Be mindful of privacy if displaying age.
            'interests': other_user_profile['interests'], # For transparency or further client-side filtering.
            'score': similarity_score
        })

    # Sort recommendations by score in descending order.
    recommended_friends.sort(key=lambda x: x['score'], reverse=True)
    return recommended_friends


# Helper function to calculate interest similarity.
def calculate_interests_similarity(interests1, interests2):
    """
    Calculates a simple similarity score based on the number of common keys in interest dictionaries.
    """
    # Get common keys (topics of interest).
    common_interest_topics = set(interests1.keys()) & set(interests2.keys())
    # Score is the count of common topics.
    score = len(common_interest_topics)
    return score


