from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import logging
import os
from config import Config
from models import db, User, MovieRating
from auth import auth_bp
from tmdb_client import TMDbClient
from csv_importer import CSVImporter
from recommendation_engine import RecommendationEngine
from collab_filtering import CollaborativeFilteringEngine
from chatbot import MovieChatbot
import traceback

app = Flask(__name__)
CORS(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Configure logging
logging.basicConfig(
    filename=Config.LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
tmdb_client = TMDbClient(Config.TMDB_API_KEY)
csv_importer = CSVImporter(tmdb_client)
recommendation_engine = RecommendationEngine(tmdb_client)
collab_filtering = CollaborativeFilteringEngine(tmdb_client)

# Initialize chatbot with Gemini
chatbot = None
if Config.GEMINI_API_KEY:
    chatbot = MovieChatbot(Config.GEMINI_API_KEY, tmdb_client, recommendation_engine)
    logger.info("Chatbot initialized successfully with Gemini")
else:
    logger.warning("Gemini API key not found - chatbot features disabled")

# In-memory storage for user movie history (in production, use a database)
user_movies = []

# Register blueprints
app.register_blueprint(auth_bp)


@app.route('/api/upload-csv', methods=['POST'])
@jwt_required()
def upload_csv():
    """Handle CSV file upload and import movies"""
    try:
        user_id = int(get_jwt_identity())
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Read file content
        file_content = file.read().decode('utf-8')
        
        # Import movies
        result = csv_importer.import_csv(file_content)
        
        if result['success']:
            # Add imported movies to database for this user
            for movie in result['movies']:
                # Check if movie already exists for this user
                existing = MovieRating.query.filter_by(
                    user_id=user_id,
                    tmdb_id=movie['tmdb_id']
                ).first()
                
                if existing:
                    # Update existing movie
                    if movie.get('rating'):
                        existing.rating = movie['rating']
                    if movie.get('watch_date'):
                        existing.watched_date = movie['watch_date']
                    db.session.merge(existing)
                else:
                    # Create new movie rating
                    rating = MovieRating(
                        user_id=user_id,
                        tmdb_id=movie['tmdb_id'],
                        title=movie['title'],
                        rating=movie.get('rating'),
                        watched_date=movie.get('watch_date'),
                        genres=','.join(movie.get('genres', [])),
                        year=movie.get('year'),
                        poster_path=movie.get('poster_path')
                    )
                    db.session.add(rating)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'count': result['count'],
                'message': f"Successfully imported {result['count']} movies",
                'errors': result.get('errors', [])
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Import failed'),
                'errors': result.get('errors', [])
            }), 400
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in upload_csv: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/add-movie', methods=['POST'])
@jwt_required()
def add_movie():
    """Add a movie manually by searching TMDb"""
    try:
        user_id = int(get_jwt_identity())
        data = request.json
        logger.info(f"Received data: {data}")
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # If user is confirming a specific movie (has tmdb_id)
        if 'tmdb_id' in data:
            tmdb_id = data['tmdb_id']
            rating = data.get('rating')
            watch_date = data.get('watch_date')
            
            # Get full movie details
            movie_details = tmdb_client.get_movie_details(tmdb_id)
            
            if movie_details:
                # Check if movie already exists for this user
                existing = MovieRating.query.filter_by(
                    user_id=user_id,
                    tmdb_id=tmdb_id
                ).first()
                
                if existing:
                    # Update existing movie
                    if rating:
                        existing.rating = rating
                    if watch_date:
                        existing.watched_date = watch_date
                    db.session.merge(existing)
                else:
                    # Create new movie rating
                    movie_rating = MovieRating(
                        user_id=user_id,
                        tmdb_id=tmdb_id,
                        title=movie_details['title'],
                        rating=rating,
                        watched_date=watch_date,
                        genres=','.join(movie_details.get('genres', [])),
                        year=movie_details.get('year'),
                        poster_path=movie_details.get('poster_path')
                    )
                    db.session.add(movie_rating)
                
                db.session.commit()
                
                movie_entry = {
                    'tmdb_id': tmdb_id,
                    'title': movie_details['title'],
                    'year': movie_details['year'],
                    'genres': movie_details['genres'],
                    'rating': rating,
                    'watch_date': watch_date,
                    'poster_path': movie_details.get('poster_path'),
                    'overview': movie_details.get('overview')
                }
                
                return jsonify({
                    'success': True,
                    'message': f"Added '{movie_details['title']}' to your collection",
                    'movie': movie_entry
                }), 200
            else:
                return jsonify({'error': 'Failed to fetch movie details'}), 500
        
        # Otherwise, search for movies by title
        if 'title' not in data:
            return jsonify({'error': 'Movie title is required'}), 400
        
        title = data['title']
        year = data.get('year')
        
        # Search TMDb for the movie
        search_results = tmdb_client.search_movie(title, year)
        
        if not search_results:
            return jsonify({
                'error': 'Movie not found',
                'message': f"No results found for '{title}'"
            }), 404
        
        # Return search results for user to select
        return jsonify({
            'matches': search_results[:5]  # Return top 5 matches
        }), 200
        
    except Exception as e:
        logger.error(f"Error in add_movie: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Generate personalized movie recommendations using hybrid approach (collaborative + content-based)"""
    try:
        user_id = int(get_jwt_identity())
        
        # Get user's movies from database
        user_movie_ratings = MovieRating.query.filter_by(user_id=user_id).all()
        
        if len(user_movie_ratings) < 3:
            return jsonify({
                'error': 'Insufficient data',
                'message': f"You need at least 3 rated movies to get recommendations. You have {len(user_movie_ratings)}."
            }), 400
        
        recommendations = []
        
        # Use collaborative filtering (requires 3+ movies)
        if len(user_movie_ratings) >= 3:
            try:
                collab_recommendations = collab_filtering.get_recommendations(user_id, num_recommendations=15)
                recommendations.extend(collab_recommendations)
                logger.info(f"Collaborative filtering returned {len(collab_recommendations)} recommendations for user {user_id}")
            except Exception as e:
                logger.warning(f"Collaborative filtering failed: {str(e)}")
        
        # Always use content-based filtering for diversity (requires 5+ movies)
        if len(user_movie_ratings) >= 5:
            try:
                # Convert to format expected by content-based recommendation engine
                user_movies_data = [
                    {
                        'tmdb_id': m.tmdb_id,
                        'title': m.title,
                        'rating': m.rating or 5,
                        'genres': m.genres.split(',') if m.genres else [],
                        'year': m.year
                    }
                    for m in user_movie_ratings
                ]
                
                # Generate content-based recommendations
                content_recommendations = recommendation_engine.generate_recommendations(user_movies_data, num_recommendations=15)
                
                # Merge with collaborative filtering results, avoiding duplicates
                existing_ids = {r['tmdb_id'] for r in recommendations}
                for rec in content_recommendations:
                    if rec['tmdb_id'] not in existing_ids:
                        recommendations.append(rec)
                        existing_ids.add(rec['tmdb_id'])
                
                logger.info(f"Content-based filtering added {len([r for r in content_recommendations if r['tmdb_id'] not in existing_ids])} recommendations for user {user_id}")
            except Exception as e:
                logger.warning(f"Content-based filtering failed: {str(e)}")
        
        # Sort by match score and limit to top 20
        recommendations.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        recommendations = recommendations[:20]
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_recommendations: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/movie/<int:tmdb_id>', methods=['GET'])
@jwt_required()
def get_movie_details(tmdb_id):
    """Get detailed information about a specific movie"""
    try:
        movie_details = tmdb_client.get_movie_details(tmdb_id)
        
        if movie_details:
            return jsonify(movie_details), 200
        else:
            return jsonify({'error': 'Movie not found'}), 404
            
    except Exception as e:
        logger.error(f"Error in get_movie_details: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/movies', methods=['GET'])
@jwt_required()
def get_user_movies():
    """Get all movies in user's collection"""
    try:
        user_id = int(get_jwt_identity())
        
        # Query movies for this user from database
        user_movie_ratings = MovieRating.query.filter_by(user_id=user_id).all()
        
        movies = [
            {
                'tmdb_id': m.tmdb_id,
                'title': m.title,
                'year': m.year,
                'genres': m.genres.split(',') if m.genres else [],
                'rating': m.rating,
                'watched_date': m.watched_date.isoformat() if m.watched_date else None,
                'poster_path': m.poster_path
            }
            for m in user_movie_ratings
        ]
        
        return jsonify({
            'movies': movies,
            'count': len(movies)
        }), 200
    except Exception as e:
        logger.error(f"Error in get_user_movies: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/delete-movie/<int:tmdb_id>', methods=['DELETE'])
@jwt_required()
def delete_movie(tmdb_id):
    """Delete a movie from user's collection"""
    try:
        user_id = int(get_jwt_identity())
        
        # Find and delete the movie
        movie = MovieRating.query.filter_by(user_id=user_id, tmdb_id=tmdb_id).first()
        
        if not movie:
            return jsonify({'error': 'Movie not found in your collection'}), 404
        
        db.session.delete(movie)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Deleted '{movie.title}' from your collection"
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in delete_movie: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat():
    """Chat with AI assistant about movies using Gemini"""
    try:
        if not chatbot:
            return jsonify({
                'error': 'Chatbot not available',
                'message': 'Gemini API key not configured'
            }), 503
        
        user_id = int(get_jwt_identity())
        data = request.json
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message']
        
        # Get user's movies from database
        user_movie_ratings = MovieRating.query.filter_by(user_id=user_id).all()
        
        user_movies_data = [
            {
                'tmdb_id': m.tmdb_id,
                'title': m.title,
                'rating': m.rating or 5,
                'genres': m.genres.split(',') if m.genres else [],
                'year': m.year
            }
            for m in user_movie_ratings
        ]
        
        # Get chatbot response
        response = chatbot.chat(user_message, user_movies_data)
        
        return jsonify({
            'success': True,
            'response': response['message'],
            'suggestions': response.get('suggestions', [])
        }), 200
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/chat/reset', methods=['POST'])
@jwt_required()
def reset_chat():
    """Reset chat conversation history"""
    try:
        if chatbot:
            chatbot.reset_conversation()
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error in reset_chat: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
