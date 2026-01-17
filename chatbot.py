import logging
import google.generativeai as genai
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class MovieChatbot:
    """AI-powered chatbot for movie recommendations using google-generativeai"""
    
    def __init__(self, api_key: str, tmdb_client=None, recommendation_engine=None):
        genai.configure(api_key=api_key)
        
        self.tmdb_client = tmdb_client
        self.recommendation_engine = recommendation_engine
        # Best free tier model as of Jan 2025: Flash-Lite has 1000 requests/day
        # Try these in order if one doesn't work:
        # 1. "gemini-2.5-flash-lite" (1000 req/day)
        # 2. "gemini-2.5-flash" (20 req/day) 
        # 3. "gemini-2.5-pro" (50 req/day, may not be available)
        self.model_name = "gemini-2.5-flash-lite"
        
        # Base system prompt (without dynamic context)
        self.base_system_prompt = """You are a friendly movie recommendation assistant. 
You help users discover movies based on their preferences and viewing history.

IMPORTANT FORMATTING RULES:
- When recommending movies, use this exact format:
  1. Movie Title (Year)
  2. Movie Title (Year)
  3. Movie Title (Year)
  etc.
- Put each movie on its own line with just the title and year
- After the numbered list, add a brief explanation paragraph about why these movies match their taste
- Do NOT include descriptions next to each movie title - keep the list clean
- Keep the explanation paragraph to 2-3 sentences max

Guidelines:
- Be conversational and enthusiastic about movies
- Suggest specific movies with brief, compelling reasons
- Keep responses concise overall
- If asked for recommendations, provide 3-5 movie titles
- Consider the user's collection context when making suggestions"""

        # Initialize model and chat session
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=self.base_system_prompt
        )
        self.chat_session = self.model.start_chat(history=[])
        self._last_context = None

    def chat(self, user_message: str, user_movies: List[Dict]) -> Dict:
        """
        Process a chat message with context about user's movie collection.
        
        Args:
            user_message: The user's message
            user_movies: List of movie dictionaries with keys like 'title', 'rating', 'genres'
            
        Returns:
            Dict with 'message' and optional 'suggestions' list
        """
        try:
            # Build context from user's collection
            context = self._build_context(user_movies)
            
            # Inject context into the conversation if it changed significantly
            if self._should_update_context(context):
                context_message = f"[System Context Update]\n{context}"
                full_message = f"{context_message}\n\nUser: {user_message}"
                self._last_context = context
            else:
                full_message = user_message
            
            # Send message and get response
            response = self.chat_session.send_message(full_message)
            
            # Extract movie suggestions if present
            suggestions = self._extract_movie_suggestions(response.text)
            
            return {
                "message": response.text,
                "suggestions": suggestions
            }
            
        except genai.types.generation_types.StopCandidateException as e:
            logger.error(f"Content was blocked: {str(e)}")
            print(f"DEBUG: Content blocked - {e}")
            return {
                "message": "I apologize, but I can't process that request. Could you rephrase your question?",
                "suggestions": []
            }
        except AttributeError as e:
            # This often happens with genai.types issues
            logger.error(f"AttributeError in chatbot: {str(e)}", exc_info=True)
            print(f"DEBUG AttributeError: {e}")
            print(f"Full traceback:")
            import traceback
            traceback.print_exc()
            return {
                "message": f"Configuration error: {str(e)}",
                "suggestions": []
            }
        except Exception as e:
            logger.error(f"Chatbot error: {str(e)}", exc_info=True)
            print(f"\n{'='*60}")
            print(f"DEBUG ERROR DETAILS:")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {e}")
            print(f"{'='*60}\n")
            import traceback
            traceback.print_exc()
            return {
                "message": f"Error: {type(e).__name__} - {str(e)}",
                "suggestions": []
            }

    def reset_conversation(self):
        """Reset the chat session to start fresh"""
        self.chat_session = self.model.start_chat(history=[])
        self._last_context = None
        logger.info("Chat session reset")

    def _should_update_context(self, new_context: str) -> bool:
        """Check if context has changed enough to warrant an update"""
        if self._last_context is None:
            return True
        # Simple check: has the context changed?
        return new_context != self._last_context

    def _build_context(self, user_movies: List[Dict]) -> str:
        """Build a concise context summary of user's movie collection"""
        if not user_movies:
            return "The user has no movies in their collection yet."
        
        # Get top-rated movies
        top_movies = sorted(
            [m for m in user_movies if m.get('rating')],
            key=lambda x: x['rating'],
            reverse=True
        )[:5]
        
        # Get favorite genres
        genres = self._get_top_genres(user_movies)
        
        # Build context string
        context_parts = [
            f"User's Collection: {len(user_movies)} movies"
        ]
        
        if top_movies:
            titles = [f"{m['title']} ({m['rating']}/10)" for m in top_movies]
            context_parts.append(f"Top Rated: {', '.join(titles)}")
        
        if genres:
            context_parts.append(f"Favorite Genres: {', '.join(genres)}")
        
        # Add average rating if available
        ratings = [m['rating'] for m in user_movies if m.get('rating')]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            context_parts.append(f"Average Rating: {avg_rating:.1f}/10")
        
        return "\n".join(context_parts)

    def _get_top_genres(self, user_movies: List[Dict], top_n: int = 3) -> List[str]:
        """Extract the most common genres from user's collection"""
        genre_counts = {}
        
        for movie in user_movies:
            for genre in movie.get('genres', []):
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Sort by frequency
        sorted_genres = sorted(
            genre_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [genre for genre, count in sorted_genres[:top_n]]

    def _extract_movie_suggestions(self, response_text: str) -> List[Dict]:
        """
        Extract movie titles from the response and fetch their details including posters.
        Returns a list of dicts with title, year, and poster_path.
        """
        suggestions = []
        
        # Look for common patterns like:
        # - "Title (Year)"
        # - "**Title**"
        # - Lines starting with numbers like "1. Title"
        
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            # Simple pattern: numbered list items
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                # Remove numbering and markdown
                cleaned = line.lstrip('0123456789.-* ')
                if cleaned and len(cleaned) > 3:  # Avoid very short matches
                    # Try to extract just the title (before any dash or colon)
                    title = cleaned.split(' - ')[0].split(':')[0].strip('*')
                    if title:
                        # Try to fetch movie details from TMDb
                        movie_data = self._fetch_movie_details(title)
                        if movie_data:
                            suggestions.append(movie_data)
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _fetch_movie_details(self, title: str) -> Optional[Dict]:
        """
        Fetch movie details including poster from TMDb.
        Returns dict with title, year, poster_path, and tmdb_id.
        """
        if not self.tmdb_client:
            return None
        
        try:
            # Search for the movie
            results = self.tmdb_client.search_movie(title)
            
            if not results:
                return None
            
            # Get the top result
            top_result = results[0]
            
            # Fetch full details
            details = self.tmdb_client.get_movie_details(top_result['tmdb_id'])
            
            if details:
                return {
                    'title': details.get('title'),
                    'year': details.get('year'),
                    'poster_path': details.get('poster_path'),
                    'tmdb_id': details.get('tmdb_id'),
                    'overview': details.get('overview', '')[:150] + '...'
                }
        except Exception as e:
            logger.warning(f"Could not fetch details for {title}: {str(e)}")
        
        return None

    def get_conversation_history(self) -> List[Dict]:
        """Return the current conversation history"""
        if not self.chat_session or not self.chat_session.history:
            return []
        
        history = []
        for message in self.chat_session.history:
            history.append({
                'role': message.role,
                'content': message.parts[0].text if message.parts else ''
            })
        return history