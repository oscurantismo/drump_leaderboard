from flask import Blueprint, request, jsonify, render_template_string
from utils.storage import load_scores
from utils.logging import log_event

leaderboard_routes = Blueprint("leaderboard_routes", __name__)

@leaderboard_routes.route("/leaderboard")
def get_leaderboard():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)
    
    # Add display names
    for entry in sorted_scores:
        entry["display_name"] = (
            entry.get("first_name") or
            entry.get("last_name") or
            entry.get("username") or
            "Anonymous"
        )
    return jsonify(sorted_scores)

@leaderboard_routes.route("/leaderboard-page")
def leaderboard_page():
    try:
        scores = load_scores()
        filtered_scores = [s for s in scores if s.get("score", 0) > 0]
        sorted_scores = sorted(filtered_scores, key=lambda x: x["score"], reverse=True)[:25]
        current_user_id = request.args.get("user_id", "")
        total_players = len(filtered_scores)

        # Add display_name to each entry
        for entry in sorted_scores:
            entry["display_name"] = (
                entry.get("first_name") or
                entry.get("last_name") or
                entry.get("username") or
                "Anonymous"
            )

        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🏆 Leaderboard</title>
            <style>
                body {
                    font-family: 'Arial Black', sans-serif;
                    background: #ffffff;
                    padding: 20px;
                    color: #002868;
                    text-align: center;
                }
                h2 {
                    color: #b22234;
                    margin-bottom: 20px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                    margin-bottom: 60px;
                }
                th, td {
                    padding: 12px;
                    border-bottom: 2px solid #ddd;
                    font-size: 16px;
                }
                th {
                    background: #002868;
                    color: white;
                }
                tr.highlight {
                    background-color: #ffeeba;
                    animation: flash 1s ease-in-out;
                }
                tr:hover {
                    background-color: #f1f1f1;
                }
                .footer {
                    text-align: right;
                    font-size: 13px;
                    font-style: italic;
                    color: #888;
                    margin-top: -40px;
                    margin-bottom: 80px;
                }
                @keyframes flash {
                    from { background-color: #fff3cd; }
                    to { background-color: #ffeeba; }
                }
            </style>
        </head>
        <body>
            <h2>🏆 Leaderboard</h2>
            {% if scores %}
            <table>
                <tr><th>#</th><th>Username</th><th>Score</th></tr>
                {% for entry in scores %}
                <tr class="{% if entry.user_id == current_user_id %}highlight{% endif %}">
                    <td>{{ loop.index }}</td>
                    <td>{{ entry.display_name }}</td>
                    <td>{{ entry.score }}</td>
                </tr>
                {% endfor %}
            </table>
            <div class="footer">showing {{ scores|length }}/76 players</div>
            {% else %}
            <div style="margin-top: 40px; font-size: 20px;">
                🤖<br><br>
                <strong>Oops, we seem to have crashed.</strong><br>
                We're working to fix the issue. Check back in a while.
            </div>
            {% endif %}
        </body>
        </html>
        """, scores=sorted_scores, current_user_id=current_user_id, total_players=total_players)

    except Exception as e:
        log_event(f"❌ Leaderboard crash: {e}")
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🏆 Leaderboard</title>
            <style>
                body {
                    font-family: 'Arial Black', sans-serif;
                    background: #ffffff;
                    padding: 20px;
                    color: #002868;
                    text-align: center;
                }
                .error-box {
                    margin-top: 100px;
                    font-size: 20px;
                    color: #333;
                }
                .error-box strong {
                    font-size: 22px;
                    display: block;
                    margin-bottom: 10px;
                }
            </style>
        </head>
        <body>
            <div class="error-box">
                🛠️<br><br>
                <strong>Oops, we seem to have crashed.</strong>
                We're working to fix the issue. Check back in a while.
            </div>
        </body>
        </html>
        """)
