
## map-pixel-backend

### Overview

This backend application provides APIs for a pixel-based map game where users can place and view pixels on a map. It uses Flask for the web framework, Flask-Login for user authentication, and SQLite for the database. Users need to wait for a cooldown period between pixel placements.

### Features

- User registration and login with bcrypt for password hashing.
- Protected endpoints requiring user authentication.
- APIs to place pixels, view placed pixels, and get user statistics.
- Cooldown mechanism to prevent spamming pixel placements.
- CORS

### Prerequisites

- Python 3.9
- Docker (for containerization)

### Setup Instructions

#### 1. Clone the repository

```sh
git clone https://github.com/JakeTurner616/map-pixel-backend
cd map-pixel-backend
```

#### 2. Create and activate a virtual environment (optional but recommended)

```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

#### 3. Install dependencies

```sh
pip install -r requirements.txt
```

#### 4. Run the application for testing and development

```sh
python backend.py
```

The application should now be running on `http://localhost:5000`.

### API Endpoints

#### User Authentication

1. **Register**: `POST /register`
   - Request Body: `{"username": "your_username", "password": "your_password"}`
   - Response: `{"message": "Registration successful"}`

2. **Login**: `POST /login`
   - Request Body: `{"username": "your_username", "password": "your_password"}`
   - Response: `{"message": "Login successful"}`

3. **Logout**: `POST /logout`
   - Response: `{"message": "Logout successful"}`

#### Pixel Operations

4. **Place Pixel**: `POST /api/update_pixels`
   - Request Body: `{"pixels": [{"lat": 51.505, "lng": -0.09, "color": "#ff0000"}]}`
   - Response: `{"status": "success", "user_id": 1, "next_allowed_time": "2024-07-02T14:00:00Z"}`

5. **Get Map**: `GET /api/get_map`
   - Response: `{"pixels": [{"lat": 51.505, "lng": -0.09, "color": "#ff0000", "user_id": 1, "placed_at": "2024-07-02T14:00:00Z", "username": "user1"}]}`

6. **User Statistics**: `GET /api/user_stats`
   - Response: User-specific and world statistics

7. **Next Allowed Time**: `GET /api/next_allowed_time`
   - Response: `{"next_allowed_time": "2024-07-02T14:00:00Z"}`

### Docker Setup

A Dockerfile is provided to containerize the application.

#### 1. Build the Docker image

```sh
docker build -t map-pixel-backend .
```

#### 2. Run the Docker container

```sh
docker run -p 50617:50617 map-pixel-backend
```

The application should now be accessible at `http://localhost:50617`.

### Environment Variables

- `REACT_APP_BACKEND_URL`: URL of the backend server.
- `REACT_APP_HCAPTCHA_SITE_KEY`: Site key for HCaptcha.

### Notes

- Ensure you replace `"https://serverboi.org"` and `"http://localhost:3000"` in the CORS setup with your actual frontend domains.

### License

This project is licensed under the GNU GPL 3.0 License. See the [License](https://github.com/JakeTurner616/map-pixel-backend/blob/main/LICENSE) file for details.
