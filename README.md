
# Forsys ERP Server

Forsys ERP Server is a backend server for an ERP system built with Django and Django REST framework. It includes authentication and other essential modules.

## Features

- User Authentication (JWT)
- User Registration and Email Verification
- Password Reset
- Swagger API Documentation
- Pagination, Filtering, and Searching

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/ForsysERPServer.git
cd ForsysERPServer
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Set up the database:

- For development (SQLite):

```bash
python manage.py makemigrations
python manage.py migrate
```

- For production (PostgreSQL):

```bash
# Update the DATABASES setting in ForsysServer/settings.py
# Then run:
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser:

```bash
python manage.py createsuperuser
```

6. Run the development server:

```bash
python manage.py runserver
```

## API Documentation

Swagger UI is available at `http://localhost:8000/swagger/` and ReDoc at `http://localhost:8000/redoc/`.

## Project Structure

```
ForsysDRFServer/
├── backend/
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── manager.py
│   ├── models.py
│   ├── pagination.py
│   ├── serializers.py
│   ├── urls.py
│   ├── utils.py
│   ├── validators.py
│   ├── views.py
│   └── ...
├── ForsysServer/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── ...
├── manage.py
└── requirements.txt
```

## Environment Variables

Create a `.env` file in the root directory and add the following variables:

```
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/forsys_erp_db
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Running Tests

To run tests, use the following command:

```bash
python manage.py test
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
