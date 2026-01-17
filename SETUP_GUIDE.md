# Collaborative Filtering Setup Guide

## Overview
This guide walks you through setting up the authentication system and PostgreSQL database for collaborative filtering recommendations.

## Prerequisites
- PostgreSQL installed and running
- Python 3.8+
- pip package manager

## Step 1: Install PostgreSQL

### Windows
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer and follow the setup wizard
3. Remember the password you set for the `postgres` user
4. PostgreSQL will run on `localhost:5432` by default

### macOS
```bash
brew install postgresql
brew services start postgresql
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

## Step 2: Create Database

Open PostgreSQL command line (psql) and run:

```sql
-- Create database
CREATE DATABASE movie_suggestor;

-- Create user (if not using default postgres user)
CREATE USER movie_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
ALTER ROLE movie_user SET client_encoding TO 'utf8';
ALTER ROLE movie_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE movie_user SET default_transaction_deferrable TO on;
ALTER ROLE movie_user SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE movie_suggestor TO movie_user;
```

## Step 3: Update Environment Variables

Edit `.env` file with your database credentials:

```env
# Database Configuration
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=movie_suggestor

# JWT Secret (change this to a random string in production!)
JWT_SECRET_KEY=your-super-secret-key-here
```

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

New packages added:
- `Flask-SQLAlchemy` - ORM for database
- `Flask-JWT-Extended` - JWT authentication
- `psycopg2-binary` - PostgreSQL driver
- `bcrypt` - Password hashing

## Step 5: Initialize Database

Run the initialization script to create all tables:

```bash
python init_db.py
```

You should see:
```
Creating database tables...
Database tables created successfully!
Tables created: ['users', 'movie_ratings', 'user_similarities']
```

## Step 6: Start the Application

```bash
python app.py
```

## API Endpoints

### Authentication

**Sign Up**
```
POST /api/auth/signup
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123"
}

Response:
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2025-01-17T..."
  }
}
```

**Login**
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepassword123"
}

Response:
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {...}
}
```

**Get Profile**
```
GET /api/auth/profile
Authorization: Bearer <access_token>
```

### Movies (Protected - Requires Auth)

**Add Movie**
```
POST /api/add-movie
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "tmdb_id": 550,
  "rating": 9.5,
  "watch_date": "2025-01-17"
}
```

**Get Recommendations (Content-Based)**
```
GET /api/recommendations
Authorization: Bearer <access_token>
```

**Get Recommendations (Collaborative Filtering)**
```
GET /api/recommendations/collab
Authorization: Bearer <access_token>
```

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email
- `password_hash` - Bcrypt hashed password
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp

### Movie Ratings Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `tmdb_id` - TMDb movie ID
- `title` - Movie title
- `rating` - User's rating (0-10)
- `watched_date` - When user watched it
- `genres` - Comma-separated genres
- `year` - Release year
- Unique constraint on (user_id, tmdb_id)

### User Similarities Table
- `id` - Primary key
- `user_id_1` - First user
- `user_id_2` - Second user
- `similarity_score` - Cosine similarity (0-1)
- `created_at` - Cache creation time
- `updated_at` - Last update time

## How Collaborative Filtering Works

1. **User Rates Movies** - Users rate movies they've watched
2. **Find Similar Users** - System finds users with similar taste (based on common movies and ratings)
3. **Get Recommendations** - Movies rated highly by similar users are recommended
4. **Weight by Similarity** - Recommendations are weighted by how similar the other user is

## Troubleshooting

### "Connection refused" error
- Make sure PostgreSQL is running
- Check DB_HOST and DB_PORT in .env

### "Database does not exist" error
- Run the SQL commands in Step 2 to create the database

### "ModuleNotFoundError" for psycopg2
- Run `pip install psycopg2-binary`

### JWT token errors
- Make sure to include `Authorization: Bearer <token>` header
- Token expires after 24 hours (configurable)

## Next Steps

1. Update frontend to use authentication
2. Modify endpoints to use `user_id` from JWT token
3. Store user ratings in database instead of in-memory
4. Implement hybrid recommendations (content + collaborative)
5. Add user profile management
