# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- View activity participants and remaining capacity
- Teacher sign-in to manage student sign-ups and unregister students

Activity viewing remains public. Only signed-in teachers can change enrollment.

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Assign a password to each teacher from the `src` directory. Passwords must be at least 12 characters and are stored as salted hashes in a local, git-ignored `teachers.json` file:

   ```
   python manage_teachers.py add teachername
   ```

3. Run the application:

   ```
   python app.py
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| GET    | `/auth/me`                                                        | Check whether the current browser has a teacher session              |
| POST   | `/auth/login`                                                      | Sign in as a teacher                                                 |
| POST   | `/auth/logout`                                                     | Sign out the current teacher                                         |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher-only student sign-up                                         |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only unregister                                          |

The app creates a local `.session_secret` file on first use to sign teacher sessions. It is git-ignored. For deployment, set a strong `SESSION_SECRET` and set `COOKIE_SECURE=true` when serving over HTTPS.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
