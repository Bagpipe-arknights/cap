Flask User Management Application
This is a Flask-based user management application that provides user registration, login, password reset, and search functionality. The application uses SQLAlchemy for database management, Flask-Login for user authentication, Flask-CORS for CORS support, and Flask-Mail for sending emails.

Installation
Clone the repository: git clone https://github.com/your_username/your_project.git
Navigate to the project directory: cd your_project
Install the required dependencies: pip install -r requirements.txt
Set up the environment variables for email configuration:
MAIL_USERNAME: Your email address
MAIL_PASSWORD: Your email password
Run the application: python app.py
Access the application in your web browser at http://localhost:5000
Features
User Registration
The application allows users to register by providing their first name, last name, phone number, email address, and password. During registration, the password is securely hashed and stored in the database.

User Login
Registered users can log in using their email address and password. The application uses Flask-Login to handle user authentication and session management. After successful login, users are redirected to the dashboard.

Password Reset
Users can request a password reset if they forget their password. The application sends an email to the user's registered email address with a password reset link. Clicking the link redirects the user to a password reset page where they can enter a new password.

Search Functionality
The application provides a search feature that allows users to search for medicines. Users can enter the brand name of a medicine, and the application will display information about the medicine, such as the generic name, batch, expiration date, strength, and net content.

User Dashboard
The user dashboard displays user-specific information, such as the user's balance and search history. It also provides options to update the user's profile and password.

API Endpoints
The application exposes the following API endpoints:

GET /api/current_user/balance: Retrieves the current user's balance.
POST /deduct_balance: Deducts a certain amount from the current user's balance.
Database Schema
The application uses SQLite as the database and defines the following tables:

users: Stores user information, including first name, last name, phone number, email, password hash, and balance.
search_history: Tracks the search history of users, including the user ID, search term, and timestamp.
Contributing
Contributions are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request.

License
This project is licensed under the MIT License. You are free to use, modify, and distribute the code as permitted by the license.
