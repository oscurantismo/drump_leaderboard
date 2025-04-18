# routes/leaderboard.py
from flask import Blueprint, request, jsonify, render_template_string
from utils.storage import load_scores
from utils.logging import log_event
from routes.rewards import log_reward_event, _load as load_reward_ledger   # ← helper

leaderboard_routes = Blueprint("leaderboard_routes", __name__)

MAINTENANCE_MODE      = False
ENABLE_REWARD_ISSUING = False   # flip to True to activate tier bonuses

# ------------------------------------------------------------------------- #
modern_leaderboard_template = """
<!DOCTYPE html>
<html>
<head>
 <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
 <title>🏆 Leaderboard</title>
 <style>
  :root{
    --primary:#2a3493;   /* DRUMP colours */
    --offwhite:#f8f9fe;
    --deepred:#8e0004;
    --badge:#FFCC68;
    --gold:#ffcc00; --silver:#c0c0c0; --bronze:#cd7f32;
  }
  /* ---------- Layout ---------- */
  body{margin:0;width:100%;height:100vh;font-family:'Segoe UI',sans-serif;
       background:#ffe242 radial-gradient(circle at center,#ffe242 0%,#ffde28 40%,#ffd608 70%);
       display:flex;flex-direction:column;align-items:center;overflow-x:hidden;color:#000;}
  h2{margin:16px 0 12px;font-size:26px;color:#000;text-shadow:0 1px 0 #fff;}
  /* ---------- Podium ---------- */
  .podium{display:flex;gap:18px;margin-top:10px;}
  .podium .slot{display:flex;flex-direction:column;align-items:center;gap:4px;}
  .podium .circ{width:76px;height:76px;border-radius:50%;display:flex;align-items:center;justify-content:center;
                border:6px solid var(--gold);font-weight:bold;font-size:24px;background:#fff;}
  .slot.silver .circ{border-color:var(--silver);}
  .slot.bronze .circ{border-color:var(--bronze);}
  .slot .name{background:#fff;border:2px solid #000;border-radius:10px;padding:4px 8px;font-size:13px;font-weight:600;}
  .slot .score{font-size:12px;color:#deepred;margin-top:-2px;}
  /* ---------- Table ---------- */
  table{width:90%;border-collapse:separate;border-spacing:0 10px;margin:24px auto;font-size:14px;}
  th{background:#000;color:#fff;padding:10px 4px;border-radius:12px;}
  td{background:#fff;padding:12px 6px;border-radius:12px;}
  tr.me td{background:var(--primary);color:var(--offwhite);}
  td:nth-child(1){width:12%;}
  td:nth-child(2){text-align:left;font-weight:600;width:48%;}
  td:nth-child(3),td:nth-child(4){text-align:center;width:20%;}
  .progress{font-size:11px;color:var(--deepred);}
  /* ---------- Utility ---------- */
  .wrap{flex:1;overflow-y:auto;width:100%;display:flex;flex-direction:column;align-items:center;padding-bottom:120px;}
 </style>
</head>
<body>
 <h2>🏆 Leaderboard</h2>

 <!-- ======= TOP‑3 PODIUM ======= -->
 {% if scores|length >= 1 %}
 <div class="podium">
   {% set top=scores[:3] %}
   {% for slot,index in [(1,1),(0,0),(2,2)] %}{# silver, gold, bronze ordering #}
   {% if top|length > index %}
     {% set p = top[index] %}
     <div class="slot {{ 'silver' if slot==1 else 'gold' if slot==0 else 'bronze' }}">
       <div class="circ">{{ loop.index }}</div>
       <div class="name">{{ p.display_name }}</div>
       <div class="score">🥾 {{ p.score }}</div>
     </div>
   {% endif %}
   {% endfor %}
 </div>
 {% endif %}

 <!-- ======= RANKS 4+ TABLE ======= -->
 <div class="wrap">
 <table>
   <tr><th>No.</th><th>Name</th><th>Punches</th><th>Next&nbsp;Level</th></tr>
   {% for entry in scores[3:50] %}
     {% set idx = loop.index + 3 %}
     {% set next_score = scores[idx-1].score if idx-1 < scores|length else entry.score %}
     {% set remaining = (next_score - entry.score + 1) if idx-1 < scores|length else 0 %}
     <tr class="{{ 'me' if entry.user_id == current_user_id else '' }}">
       <td>{{ idx }}</td>
       <td>{{ entry.display_name }}</td>
       <td>{{ entry.score }}</td>
       <td class="progress">{% if remaining > 0 %}🥾 {{ remaining }}<br>More{% else %}—{% endif %}</td>
     </tr>
   {% endfor %}
 </table>
 </div>
</body>
</html>
"""

maintenance_template = """<!DOCTYPE html>
<html>
<head>
  <meta name="viewport"
        content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
  <title>🚧 Maintenance</title>
  <style>
    /* full‑width background (avoid vw to skip scrollbar pixels) */
    html,body{
      height:100%;
      width:100%;          /* ⬅ changed from 100vw */
      margin:0;
      overflow-x:hidden;
      font-family:'Segoe UI',sans-serif;
      background:#f8f9fe;
      color:#2a3493;
    }
    /* centre the notice */
    body{
      display:flex;
      align-items:center;
      justify-content:center;
      padding:0 16px;
      box-sizing:border-box;
    }
    .box{
      width:100%;
      max-width:420px;
      background:#fff;
      border:2px solid #2a3493;
      border-radius:10px;
      padding:24px;
      text-align:center;
      box-sizing:border-box;
    }
  </style>
</head>
<body>
  <div class="box">
    <h2 style="margin:0 0 6px">🚧 Leaderboard under maintenance</h2>
    <p style="margin:0">Please check back soon – we’re improving your experience.</p>
  </div>
</body>
</html>"""


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
