from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ratings = db.relationship('MovieRating', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }


class MovieRating(db.Model):
    """User movie ratings for collaborative filtering"""
    __tablename__ = 'movie_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tmdb_id = db.Column(db.Integer, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    rating = db.Column(db.Float, nullable=True)  # Allow NULL for unrated movies
    watched_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Store additional metadata for faster queries
    genres = db.Column(db.String(255))  # Comma-separated genres
    year = db.Column(db.Integer)
    poster_path = db.Column(db.String(255))  # TMDb poster path
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'tmdb_id', name='unique_user_movie'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'tmdb_id': self.tmdb_id,
            'title': self.title,
            'rating': self.rating,
            'watched_date': self.watched_date.isoformat() if self.watched_date else None,
            'genres': self.genres.split(',') if self.genres else [],
            'year': self.year,
            'poster_path': self.poster_path
        }


class UserSimilarity(db.Model):
    """Cache user similarity scores for collaborative filtering"""
    __tablename__ = 'user_similarities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id_1 = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user_id_2 = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    similarity_score = db.Column(db.Float, nullable=False)  # 0-1 scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id_1', 'user_id_2', name='unique_user_pair'),
    )
