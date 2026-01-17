import numpy as np
import logging
from typing import List, Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from models import db, User, MovieRating, UserSimilarity
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CollaborativeFilteringEngine:
    """Collaborative filtering recommendation engine"""
    
    def __init__(self, tmdb_client):
        self.tmdb_client = tmdb_client
        self.similarity_cache_ttl = 7 * 24 * 60 * 60  # 7 days in seconds
    
    def get_recommendations(self, user_id: int, num_recommendations: int = 10) -> List[Dict]:
        """
        Generate recommendations using collaborative filtering
        
        Args:
            user_id: ID of the user to generate recommendations for
            num_recommendations: Number of recommendations to return
            
        Returns:
            List of recommended movies with scores
        """
        try:
            # Get user's ratings
            user_ratings = MovieRating.query.filter_by(user_id=user_id).all()
            
            if not user_ratings or len(user_ratings) < 3:
                logger.warning(f"User {user_id} has insufficient ratings for collab filtering")
                return []
            
            # Find similar users
            similar_users = self._find_similar_users(user_id, top_n=5)  # Reduced from 10 to 5
            
            if not similar_users:
                logger.warning(f"No similar users found for user {user_id}")
                return []
            
            # Get movies rated by similar users but not by current user
            user_movie_ids = {r.tmdb_id for r in user_ratings}
            recommendations = self._get_similar_user_recommendations(
                similar_users, 
                user_movie_ids,
                num_recommendations
            )
            
            logger.info(f"Collaborative filtering returning {len(recommendations)} recommendations for user {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Collaborative filtering error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _find_similar_users(self, user_id: int, top_n: int = 10) -> List[Tuple[int, float]]:
        """
        Find users with similar movie preferences
        
        Returns:
            List of (user_id, similarity_score) tuples
        """
        try:
            # Get user's rating vector
            user_ratings = MovieRating.query.filter_by(user_id=user_id).all()
            
            if not user_ratings:
                logger.info(f"User {user_id} has no ratings")
                return []
            
            # Create rating matrix for this user (only rated movies)
            user_movie_dict = {r.tmdb_id: r.rating for r in user_ratings if r.rating is not None}
            
            if not user_movie_dict:
                logger.info(f"User {user_id} has no rated movies")
                return []
            
            logger.info(f"User {user_id} has {len(user_movie_dict)} rated movies")
            
            # Get all other users
            other_users = User.query.filter(User.id != user_id).all()
            logger.info(f"Found {len(other_users)} other users to compare with")
            
            similarities = []
            
            for other_user in other_users:
                # Get other user's ratings (only rated movies)
                other_ratings = MovieRating.query.filter_by(user_id=other_user.id).all()
                
                if not other_ratings:
                    continue
                
                # Find common movies with ratings
                other_movie_dict = {r.tmdb_id: r.rating for r in other_ratings if r.rating is not None}
                common_movies = set(user_movie_dict.keys()) & set(other_movie_dict.keys())
                
                if len(common_movies) < 2:
                    continue
                
                logger.info(f"User {user_id} and User {other_user.id} have {len(common_movies)} common rated movies")
                
                # Calculate similarity based on common movies
                user_vector = np.array([user_movie_dict[m] for m in common_movies])
                other_vector = np.array([other_movie_dict[m] for m in common_movies])
                
                # Normalize vectors
                user_mean = np.mean(user_vector)
                other_mean = np.mean(other_vector)
                user_std = np.std(user_vector)
                other_std = np.std(other_vector)
                
                user_vector = (user_vector - user_mean) / (user_std + 1e-8)
                other_vector = (other_vector - other_mean) / (other_std + 1e-8)
                
                # Calculate cosine similarity
                similarity = cosine_similarity([user_vector], [other_vector])[0][0]
                
                logger.info(f"Similarity between User {user_id} and User {other_user.id}: {similarity:.3f}")
                
                if similarity > 0:
                    similarities.append((other_user.id, similarity))
            
            # Sort by similarity and return top N
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Found {len(similarities)} similar users for user {user_id}: {similarities[:top_n]}")
            
            return similarities[:top_n]
            
        except Exception as e:
            logger.error(f"Error finding similar users: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _get_similar_user_recommendations(
        self, 
        similar_users: List[Tuple[int, float]], 
        user_movie_ids: set,
        num_recommendations: int
    ) -> List[Dict]:
        """
        Get recommendations from similar users' ratings
        
        Args:
            similar_users: List of (user_id, similarity_score) tuples
            user_movie_ids: Set of movie IDs already rated by current user
            num_recommendations: Number of recommendations to return
            
        Returns:
            List of recommended movies with weighted scores
        """
        try:
            movie_scores = {}
            
            # Aggregate ratings from similar users
            for similar_user_id, similarity_score in similar_users:
                similar_user_ratings = MovieRating.query.filter_by(user_id=similar_user_id).all()
                
                for rating in similar_user_ratings:
                    # Skip movies already rated by current user
                    if rating.tmdb_id in user_movie_ids:
                        continue
                    
                    # Skip unrated movies
                    if rating.rating is None:
                        continue
                    
                    # Weight the rating by similarity score
                    weighted_rating = rating.rating * similarity_score
                    
                    if rating.tmdb_id not in movie_scores:
                        movie_scores[rating.tmdb_id] = {
                            'total_score': 0,
                            'count': 0,
                            'title': rating.title,
                            'year': rating.year,
                            'genres': rating.genres,
                            'poster_path': rating.poster_path
                        }
                    
                    movie_scores[rating.tmdb_id]['total_score'] += weighted_rating
                    movie_scores[rating.tmdb_id]['count'] += 1
            
            # Calculate average weighted scores and sort
            scored_movies = []
            for tmdb_id, data in movie_scores.items():
                avg_score = data['total_score'] / data['count']
                scored_movies.append({
                    'tmdb_id': tmdb_id,
                    'match_score': round(avg_score, 1),
                    'title': data['title'],
                    'year': data['year'],
                    'genres': data['genres'].split(',') if data['genres'] else [],
                    'poster_path': data['poster_path'],
                    'reasoning': 'Recommended by users with similar taste'
                })
            
            # Sort by score and return top N
            scored_movies.sort(key=lambda x: x['match_score'], reverse=True)
            recommendations = scored_movies[:num_recommendations]
            
            # Fetch full movie details only for top recommendations
            final_recommendations = []
            for rec in recommendations:
                try:
                    movie_details = self.tmdb_client.get_movie_details(rec['tmdb_id'])
                    if movie_details:
                        final_recommendations.append({
                            **movie_details,
                            'match_score': rec['match_score'],
                            'reasoning': rec['reasoning']
                        })
                except Exception as e:
                    logger.warning(f"Could not fetch details for movie {rec['tmdb_id']}: {str(e)}")
                    # Still include the recommendation with basic info
                    final_recommendations.append(rec)
            
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error getting similar user recommendations: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def update_user_similarity_cache(self, user_id: int):
        """Update cached similarity scores for a user"""
        try:
            # Delete old cache entries
            cutoff_date = datetime.utcnow() - timedelta(seconds=self.similarity_cache_ttl)
            UserSimilarity.query.filter(
                (UserSimilarity.user_id_1 == user_id) | (UserSimilarity.user_id_2 == user_id),
                UserSimilarity.updated_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Updated similarity cache for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating similarity cache: {str(e)}")
            db.session.rollback()
