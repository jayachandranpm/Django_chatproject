Django Chatting Application




## Getting Started

These instructions will help you set up and run the Chat Application project on your local machine.

### Prerequisites

Before you begin, make sure you have the following installed:

- Python 3.x (https://www.python.org/downloads/)
- Git (https://git-scm.com/downloads/) (optional, but recommended)

### Setting up a Virtual Environment

We recommend using a virtual environment to manage project dependencies. You can create a virtual environment using `virtualenv` or `venv`, depending on your Python version.

#### Using virtualenv (Python 3.6+)


# Install virtualenv (if not already installed)
pip install virtualenv

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS and Linux
source venv/bin/activate


# Installing Dependencies
Once your virtual environment is activated, install project dependencies using pip and the requirements.txt file:

pip install -r requirements.txt


### Changing Database Configuration

By default, the project uses the SQLite database. If you wish to use a different database, follow these steps to update the database configuration:

1. Open the `settings.py` file located in the `chat_project` directory.

2. Locate the `DATABASES` section in the `settings.py` file. It should look something like this:


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        ...
    }
}



# MySQL Database Configuration
# Install mysqlclient
First, ensure you have MySQL installed on your system. You can download it from the official MySQL website or use a package manager for your operating system.

Install the mysqlclient Python package to enable Django to work with MySQL:

pip install mysqlclient
Update Django Settings
Open the settings.py file in your Django project directory.

Locate the DATABASES section and update it as follows:

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_database_name',
        'USER': 'your_database_user',
        'PASSWORD': 'your_database_password',
        'HOST': 'localhost',  # Replace with your database host if not localhost
        'PORT': '3306',       # Replace with your database port if different
    }
}
Replace 'your_database_name', 'your_database_user', 'your_database_password', 'localhost', and '3306' with your MySQL database details.

Save the settings.py file.

# Migrating the Database
You'll need to apply database migrations to create the necessary database schema:

python manage.py makemigrations
python manage.py migrate

# Running the Project
You can now run the Django development server to start the Chat Application:

python manage.py runserver