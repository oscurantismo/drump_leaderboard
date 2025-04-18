# routes/leaderboard.py
from flask import Blueprint, request, jsonify, render_template_string
from utils.storage import load_scores
from utils.logging import log_event
from routes.rewards import log_reward_event, _load as load_reward_ledger   # ← helper

leaderboard_routes = Blueprint("leaderboard_routes", __name__)

MAINTENANCE_MODE      = False
ENABLE_REWARD_ISSUING = False   # flip to True to activate tier bonuses

# ------------------------------------------------------------------------- #
# ------------------------------------------------------------------ #
modern_leaderboard_template = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport"
      content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>🏆 Leaderboard</title>
<style>
 /*  ─────────  Theme tokens  ───────── */
 :root{
   --blue:#2a3493;
   --off:#f8f9fe;
   --dark:#000;
   --red:#d11b1b;
   --bg:#ffe242;
 }
 /*  ─────────  Layout  ───────── */
 html,body{margin:0;width:100%;height:100%;overflow-x:hidden;
           font-family:'Commissioner',sans-serif;background:var(--bg);
           background:var(--bg) radial-gradient(circle,#ffe242 0%,#ffde28 35%,#ffd608 65%);
           color:var(--dark);}
 h1{display:none;}
 /* Top‑3 section */
 .podium{display:flex;justify-content:center;gap:22px;margin-top:40px;}
 .slot{display:flex;flex-direction:column;align-items:center;gap:6px;}
 .slot .ring{
   width:92px;height:92px;border-radius:50%;background:#fff;display:flex;
   align-items:center;justify-content:center;font-weight:900;font-size:28px;
   border:6px solid var(--blue);}
 .slot.gold  .ring{border-color:var(--red);}
 .slot .badge{
   background:#fff;border:2px solid #000;border-radius:10px;padding:4px 10px;
   font-weight:600;font-size:13px;max-width:96px;text-overflow:ellipsis;white-space:nowrap;overflow:hidden;}
 .slot .score{font-size:12px;margin-top:-2px;}
 /* Crown for 1st */
 .crown{position:absolute;top:-26px;left:50%;transform:translateX(-50%);
        width:44px;height:26px;background:var(--red);clip-path:polygon(0 100%,0 50%,25% 0,50% 50%,75% 0,100% 50%,100% 100%);}
 /*  ─────────  Table  ───────── */
 table{width:92%;margin:34px auto 140px;border-collapse:separate;border-spacing:0 12px;font-size:14px;}
 th{background:#000;color:#fff;padding:10px;border-radius:12px;font-weight:700;}
 td{background:#fff;padding:14px 10px;border-radius:12px;text-align:center;}
 td.name{text-align:left;font-weight:700;}
 tr.me td{background:var(--blue);color:var(--off);}
 .progress{font-size:11px;color:var(--red);line-height:16px;}
</style>
</head>
<body>

<!-- =====================  TOP‑3 PODIUM  ===================== -->
{% if top_first %}
<div class="podium">

  {% if top_second %}
  <div class="slot silver">
    <div class="ring">2nd</div>
    <div class="badge">{{ top_second.display_name }}</div>
    <div class="score">🥾 {{ top_second.score }} Punches</div>
  </div>
  {% endif %}

  <div class="slot gold" style="position:relative;">
    <div class="crown"></div>
    <div class="ring">1st</div>
    <div class="badge">{{ top_first.display_name }}</div>
    <div class="score">🥾 {{ top_first.score }} Punches</div>
  </div>

  {% if top_third %}
  <div class="slot bronze">
    <div class="ring">3rd</div>
    <div class="badge">{{ top_third.display_name }}</div>
    <div class="score">🥾 {{ top_third.score }} Punches</div>
  </div>
  {% endif %}

</div>
{% endif %}

<!-- =====================  RANKS 4+ TABLE  ===================== -->
<table>
  <tr><th>No.</th><th>Name</th><th>Punches</th><th>Next&nbsp;Level</th></tr>
  {% for entry in scores[3:50] %}
    {% set idx = loop.index + 3 %}
    {% set next_score = scores[idx-1].score if idx-1 < scores|length else entry.score %}
    {% set remain = (next_score - entry.score + 1) if idx-1 < scores|length else 0 %}
    <tr class="{{ 'me' if entry.user_id == current_user_id else '' }}">
      <td>{{ idx }}</td>
      <td class="name">{{ entry.display_name }}</td>
      <td>{{ entry.score }}</td>
      <td class="progress">{% if remain > 0 %}🥾 {{ remain }}<br>More{% else %}—{% endif %}</td>
    </tr>
  {% endfor %}
</table>

</body>
</html>"""
# ------------------------------------------------------------------ #



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
         # extract top‑3 first, second, third AFTER sorting
         top_first  = sorted_scores[0]  if len(sorted_scores) > 0 else None
         top_second = sorted_scores[1]  if len(sorted_scores) > 1 else None
         top_third  = sorted_scores[2]  if len(sorted_scores) > 2 else None


        return render_template_string(
            modern_leaderboard_template,
            scores=sorted_scores,
            current_user_id=current_user_id,
            total_players=total_players,
            user_rank=user_rank,
            progress_text=progress_text,
            movement_history=movement_hist,
        )

    except Exception as e:
        log_event(f"❌ Leaderboard crash: {e}")
        return render_template_string(maintenance_template), 500
