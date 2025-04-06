from flask import Blueprint, request, jsonify, render_template_string
from utils.storage import load_scores
from utils.logging import log_event

leaderboard_routes = Blueprint("leaderboard_routes", __name__)

@leaderboard_routes.route("/leaderboard")
def leaderboard():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:25]
    return jsonify(sorted_scores)


@leaderboard_routes.route("/leaderboard-page")
def leaderboard_page():
    scores = load_scores()
    filtered_scores = [s for s in scores if s.get("score", 0) > 0]
    sorted_scores = sorted(filtered_scores, key=lambda x: x["score"], reverse=True)[:25]
    current_user_id = request.args.get("user_id", "")
    total_players = len(filtered_scores)

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Leaderboard</title>
        <style>
            body {
                font-family: 'Arial Black', sans-serif;
                background: #ffffff;
                padding: 20px;
                color: #002868;
                text-align: center;
                position: relative;
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
                background-color: #ffeeba !important;
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
                margin-bottom: 20px;
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
                <td>{{ entry.username }}</td>
                <td>{{ entry.score }}</td>
            </tr>
            {% endfor %}
        </table>
        <div class="footer">showing {{ scores|length }}/{{ total_players }} players</div>
        {% else %}
        <p>No scores submitted yet.</p>
        {% endif %}
    </body>
    </html>
    """

    log_event("📊 Leaderboard viewed")
    return render_template_string(html, scores=sorted_scores, current_user_id=current_user_id, total_players=total_players)
