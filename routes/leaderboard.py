# routes/leaderboard.py
from flask import Blueprint, request, jsonify, render_template_string
from utils.storage import load_scores
from utils.logging import log_event
from routes.rewards import log_reward_event, _load as load_reward_ledger   # ← helper

leaderboard_routes = Blueprint("leaderboard_routes", __name__)

MAINTENANCE_MODE      = False
ENABLE_REWARD_ISSUING = False   # flip to True to activate tier bonuses

# ------------------------------------------------------------------------- #
modern_leaderboard_template = """<!DOCTYPE html>
<html><head>
<title>🏆 Leaderboard</title>
<style>
 body{font-family:'Segoe UI',sans-serif;background:#ffffff;padding:20px;color:#002868;text-align:center;margin-bottom:200px;}
 h2{color:#0047ab;font-size:26px;margin-bottom:10px;}
 .rank-summary{margin-top:10px;font-size:18px;color:#333;}
 .progress-text{font-size:15px;color:#888;margin-bottom:10px;}
 table{width:100%;border-collapse:collapse;margin-top:20px;margin-bottom:20px;}
 th,td{padding:10px;border-bottom:1px solid #ddd;font-size:15px;}
 th{background:#0047ab;color:#fff;}
 tr.highlight{background:#ffeeba!important;animation:flash 1s ease-in-out;}
 tr:hover{background:#f1f1f1;}
 button{padding:10px 16px;margin:10px 6px;font-size:14px;border:none;border-radius:8px;background:#0047ab;color:#fff;cursor:pointer;}
 .footer{text-align:center;font-size:13px;font-style:italic;color:#666;margin-top:10px;}
 .history{margin-top:20px;text-align:left;}
 .history ul{list-style:none;padding-left:0;}
 .history li{padding:6px 0;border-bottom:1px solid #eee;}
 @keyframes flash{from{background:#fff3cd;}to{background:#ffeeba;}}
</style>
<script>
 function toggleHistory(){
   const h=document.getElementById("history");
   h.style.display=h.style.display==="none"?"block":"none";
 }
</script>
</head><body>
  <h2>🏆 Leaderboard</h2>
  {% if user_rank %}
    <div class="rank-summary">👤 Your Rank: {{ user_rank }}</div>
    <div class="progress-text">🔼 {{ progress_text }}</div>
  {% endif %}
  {% if scores %}
    <table>
      <tr><th>#</th><th>Username</th><th>Score</th></tr>
      {% for entry in scores %}
      <tr class="{% if entry.user_id == current_user_id %}highlight{% endif %}">
        <td>{% if loop.index==1 %}🥇{% elif loop.index==2 %}🥈{% elif loop.index==3 %}🥉{% else %}{{ loop.index }}{% endif %}</td>
        <td>{{ entry.display_name }}</td>
        <td>{{ entry.score }}</td>
      </tr>
      {% endfor %}
    </table>
    <div class="footer">showing {{ scores|length }}/{{ total_players }} players</div>
    <button onclick="toggleHistory()">📈 Your Leaderboard Progress</button>
    <div id="history" class="history" style="display:none;">
      <ul>{% for h in movement_history %}<li>{{ h|safe }}</li>{% endfor %}</ul>
    </div>
  {% endif %}
</body></html>"""

maintenance_template = """<!DOCTYPE html>
<html><head>
 <title>🚧 Maintenance</title>
 <style>
  body{display:flex;align-items:center;justify-content:center;height:100vh;margin:0;
       font-family:'Segoe UI',sans-serif;background:#f8f9fe;color:#2a3493;}
  .box{border:2px solid #2a3493;border-radius:10px;padding:24px;text-align:center;background:#ffffff;}
 </style>
</head><body>
  <div class="box">
    <h2>🚧 Leaderboard under maintenance</h2>
    <p>Please check back soon – we’re improving your experience.</p>
  </div>
</body></html>"""
# ------------------------------------------------------------------------- #
@leaderboard_routes.route("/leaderboard")
def get_leaderboard():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)
    for e in sorted_scores:
        e["display_name"] = e.get("first_name") or e.get("last_name") or e.get("username") or "Anonymous"
    return jsonify(sorted_scores)


@leaderboard_routes.route("/leaderboard-page")
def leaderboard_page():
    if MAINTENANCE_MODE:
        return render_template_string(maintenance_template)

    try:
        scores           = load_scores()
        filtered         = [s for s in scores if s.get("score", 0) > 0]
        sorted_scores    = sorted(filtered, key=lambda x: x["score"], reverse=True)
        current_user_id  = request.args.get("user_id", "")
        total_players    = len(scores)

        # display name helper
        for e in sorted_scores:
            e["display_name"] = e.get("first_name") or e.get("last_name") or e.get("username") or "Anonymous"

        user_index  = next((i for i, e in enumerate(sorted_scores) if e.get("user_id") == current_user_id), None)
        user_rank   = user_index + 1 if user_index is not None else None
        user_score  = sorted_scores[user_index]["score"] if user_index is not None else 0

        # progress text
        if user_rank:
            if user_rank > 25:
                threshold = sorted_scores[24]["score"]
                progress_text = f"{threshold - user_score + 1} punches left to enter top‑25"
            elif user_rank > 1:
                threshold = sorted_scores[user_index - 1]["score"]
                progress_text = f"{threshold - user_score + 1} punches left to reach top‑{user_rank - 1}"
            else:
                progress_text = "You're #1! 🏆"
        else:
            progress_text = "Punch more to enter the top‑25!"

        # ─── reward tiers & history ───────────────────────────────────────
        reward_tiers = [
            ("Entered top‑1",   1, 4000),
            ("Entered top‑2",   2, 2000),
            ("Entered top‑3",   3, 1000),
            ("Entered top‑10", 10,  550),
            ("Entered top‑25", 25,  250),
        ]

        ledger        = load_reward_ledger()
        user_rewards  = [r["event"] for r in ledger if r["user_id"] == current_user_id]
        movement_hist = []

        if user_rank:
            for label, threshold, bonus in reward_tiers:
                if user_rank <= threshold:
                    if label in user_rewards:
                        movement_hist.append(f"✅ {label}: +{bonus} punches — collected")
                    else:
                        movement_hist.append(f"🎯 {label}: +{bonus} punches — <span style='color:#888;'>uncollected</span>")
                        if ENABLE_REWARD_ISSUING:
                            log_reward_event(
                                user_id=current_user_id,
                                username=current_user_id,
                                reward_type="rank_bonus",
                                source_id=label,
                                change=bonus,
                                prev_score=user_score,
                                new_score=user_score + bonus,
                                meta={}
                            )
                            user_rewards.append(label)
        else:
            movement_hist.append("No rewards yet. Punch more to climb the leaderboard!")

        return render_template_string(
            modern_leaderboard_template,
            scores=sorted_scores[:50],
            current_user_id=current_user_id,
            total_players=total_players,
            user_rank=user_rank,
            progress_text=progress_text,
            movement_history=movement_hist,
        )

    except Exception as e:
        log_event(f"❌ Leaderboard crash: {e}")
        return render_template_string(maintenance_template), 500
