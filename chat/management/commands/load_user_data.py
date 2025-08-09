import json
import os
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from chat.models import Profile, Interest

class Command(BaseCommand):
    help = 'Loads user data from a JSON file into the database'

    def handle(self, *args, **options):
        json_file_path = os.path.join(settings.STATICFILES_DIRS[0], 'json/users.json')

        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
            users = data['users']

            for user_data in users:
                username = user_data['name'].replace(' ', '').lower()
                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.WARNING(f'User {username} already exists, skipping.'))
                    continue

                user = User.objects.create_user(
                    username=username,
                    password=username,  # Using username as password for simplicity
                    first_name=user_data['name']
                )
                user.save()

                profile = Profile.objects.create(user=user)

                for interest_name, score in user_data['interests'].items():
                    interest, created = Interest.objects.get_or_create(name=interest_name)
                    profile.interests.add(interest)

                profile.save()

                self.stdout.write(self.style.SUCCESS(f'Successfully created user {username}'))
