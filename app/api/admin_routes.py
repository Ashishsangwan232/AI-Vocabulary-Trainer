from flask import Blueprint, jsonify
from app.db.models import User, NLPWord, TriviaFact, UserHistory

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/stats", methods=["GET"])
def get_admin_stats():
    try:
        # 1. Get total counts
        total_users = User.query.count()
        total_words = NLPWord.query.count()
        total_facts = TriviaFact.query.count()
        total_interactions = UserHistory.query.count()

        # 2. Get the 5 most recently added words
        recent_words_query = NLPWord.query.order_by(NLPWord.id.desc()).limit(5).all()
        recent_words = [
            {"word": w.word, "difficulty": w.difficulty} for w in recent_words_query
        ]

        # 3. NEW: Get the 5 most recently added facts
        recent_facts_query = TriviaFact.query.order_by(TriviaFact.id.desc()).limit(5).all()
        recent_facts = [
            {"fact": f.fact_text} for f in recent_facts_query
        ]

        return jsonify({
            "metrics": {
                "totalUsers": total_users,
                "totalWords": total_words,
                "totalFacts": total_facts,
                "totalInteractions": total_interactions
            },
            "recentWords": recent_words,
            "recentFacts": recent_facts # Send facts to React!
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500