from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from bri_engine import calculate_bri
import database as db

app = Flask(__name__)
app.secret_key = "cognisense-secret-key-change-in-production"

# ─── Mock linked rehabilitation centers ───────────────────────────────────────
LINKED_CENTERS = [
    {"name": "Serene Recovery Center",  "type": "Rehabilitation & Mental Health"},
    {"name": "MindBridge Wellness",      "type": "Psychological Support Services"},
    {"name": "Horizon Rehab Institute",  "type": "Burnout & Stress Recovery"},
]

# ─── Ember keyword responses ──────────────────────────────────────────────────
EMBER_RESPONSES = {
    "tired":        "That kind of tiredness runs deeper than sleep can fix. What's been weighing on you most?",
    "exhausted":    "Exhaustion is your body sending an urgent message. Are you able to take even a small break today?",
    "overwhelmed":  "When everything piles up, even breathing feels hard. Let's slow down — what's pressing hardest right now?",
    "hopeless":     "Hopeless is a heavy word to carry. I hear you. Would it help to talk through what's making things feel stuck?",
    "anxious":      "Anxiety has a way of making everything feel urgent at once. You don't have to solve it all right now.",
    "burned out":   "Burnout isn't weakness — it's what happens when effort goes unrecognised for too long.",
    "can't focus":  "When focus slips, it's often a sign your mind needs rest more than it needs to try harder.",
    "drained":      "Feeling drained is real and valid. What's been taking the most from you lately?",
    "angry":        "Anger usually means something important isn't being heard. What's underneath it for you?",
    "sad":          "Sadness deserves space, not just solutions. It's okay to just feel it for a moment.",
    "scared":       "Fear is information. What does it feel like it's trying to tell you right now?",
    "failing":      "Feeling like you're failing doesn't mean you are. What does failure look like to you right now?",
    "fine":         "Sometimes 'fine' is doing a lot of work. How are you actually doing?",
    "stressed":     "Stress is your system saying 'too much at once.' What would feel like relief right now?",
    "default":      "I'm here. Take your time — there's no right way to say what you're feeling.",
}

# ─── Cognitive reframe rules ───────────────────────────────────────────────────
REFRAME_RULES = [
    (["i'm a failure", "i am a failure", "i failed"],
     "I didn't succeed this time — and that's information, not a verdict on who I am."),
    (["i can't do this", "i cannot do this"],
     "This feels really hard right now — and I can take it one small step at a time."),
    (["nobody cares", "no one cares"],
     "I haven't found the right people yet — connection takes time and I deserve it."),
    (["i'm worthless", "i am worthless", "i'm useless"],
     "I'm going through something difficult — my worth isn't measured by my output."),
    (["everything is falling apart"],
     "Some things feel unstable right now — I can focus on what's within my control."),
    (["i'll never get better", "i will never get better"],
     "Recovery isn't linear — feeling this way right now doesn't mean I'll feel this way forever."),
    (["i'm so stupid", "i am so stupid"],
     "I'm learning and that means I'll get things wrong — that's how growth actually works."),
    (["i'm so tired", "i am so tired"],
     "My body and mind are asking for rest — listening to that is strength, not weakness."),
    (["i give up", "i want to give up"],
     "I need a break, not a full stop — pausing is allowed and sometimes necessary."),
    (["i hate myself"],
     "Part of me is really struggling right now — that part deserves care, not punishment."),
]


def get_reframe(thought: str) -> str:
    thought_lower = thought.lower().strip()
    for triggers, reframe in REFRAME_RULES:
        for trigger in triggers:
            if trigger in thought_lower:
                return reframe
    # Generic fallback
    return "This thought is one perspective — is there another way to look at this situation that's equally true?"


# ─── Context processor — inject common data to all templates ──────────────────
@app.context_processor
def inject_globals():
    today_session = db.get_recent_sessions(1)
    today_bri = today_session[0]["bri_score"] if today_session else None
    streak = db.get_streak()
    sharing_enabled = session.get("sharing_enabled", False)
    return dict(
        today_bri=today_bri,
        streak=streak,
        sharing_enabled=sharing_enabled
    )


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    recent = db.get_recent_sessions(5)
    trend_direction = db.get_7day_trend_direction()
    risk_counts = db.get_risk_counts(7)
    consecutive_rising = db.get_consecutive_rising_count()
    show_pattern_warning = consecutive_rising >= 3

    # Determine current state label
    today = db.get_recent_sessions(1)
    current_state = "No Data"
    if today:
        rl = today[0]["risk_level"]
        current_state = {"Low": "Stable", "Medium": "Elevated", "High": "At Risk"}.get(rl, "No Data")

    return render_template(
        "index.html",
        recent=recent,
        trend_direction=trend_direction,
        risk_counts=risk_counts,
        show_pattern_warning=show_pattern_warning,
        current_state=current_state,
        linked_centers=LINKED_CENTERS,
    )


@app.route("/checkin")
def checkin():
    recent = db.get_recent_sessions(5)
    return render_template("checkin.html", recent=recent)


@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.form.get("checkin_text", "").strip()
    if not text:
        flash("Please write something before submitting.", "warning")
        return redirect(url_for("checkin"))

    result = calculate_bri(text)

    session_id = db.save_session(
        bri_score=result["bri_score"],
        risk_level=result["risk_level"],
        tone_label=result["tone_label"],
        neg_score=result["neg_score"],
        keyword_hits=result["keyword_hits"],
    )

    # If sharing enabled, log to all linked centers
    if session.get("sharing_enabled", False):
        for center in LINKED_CENTERS:
            db.save_sharing_log_entry(
                session_id=session_id,
                bri_score=result["bri_score"],
                risk_level=result["risk_level"],
                center_name=center["name"]
            )

    # Store result in session for results page
    session["last_result"] = {
        "session_id": session_id,
        "bri_score": result["bri_score"],
        "risk_level": result["risk_level"],
        "tone_label": result["tone_label"],
        "neg_score": result["neg_score"],
        "keyword_hits": result["keyword_hits"],
        "emotions": result["emotions"],
    }

    return redirect(url_for("results"))


@app.route("/results")
def results():
    result = session.get("last_result")
    if not result:
        flash("No recent result found. Please do a check-in first.", "warning")
        return redirect(url_for("checkin"))

    consecutive_rising = db.get_consecutive_rising_count()
    show_pattern_warning = consecutive_rising >= 3

    # SVG arc calculation for gauge (semicircle, max angle = 180 degrees)
    bri_score = result["bri_score"]
    # Arc is a semicircle: circumference portion for score
    # SVG path r=80, so circumference of half = π*80 ≈ 251.2
    arc_circumference = 251.2
    arc_offset = arc_circumference - (bri_score / 100) * arc_circumference

    return render_template(
        "results.html",
        result=result,
        arc_offset=arc_offset,
        arc_circumference=arc_circumference,
        show_pattern_warning=show_pattern_warning,
    )


@app.route("/history")
def history():
    heatmap = db.get_7day_heatmap()
    all_sessions = db.get_sessions_last_n_days(7)
    consecutive_rising = db.get_consecutive_rising_count()
    show_pattern_warning = consecutive_rising >= 3

    # Stats
    scores = [s["bri_score"] for s in all_sessions]
    avg_bri = round(sum(scores) / len(scores), 1) if scores else 0
    highest = max(scores) if scores else 0
    lowest = min(scores) if scores else 0
    total = len(scores)

    trend_direction = db.get_7day_trend_direction()

    return render_template(
        "history.html",
        heatmap=heatmap,
        all_sessions=all_sessions,
        show_pattern_warning=show_pattern_warning,
        avg_bri=avg_bri,
        highest=highest,
        lowest=lowest,
        total=total,
        trend_direction=trend_direction,
    )


@app.route("/chat")
def chat():
    if "chat_history" not in session:
        session["chat_history"] = []
    return render_template("chat.html", chat_history=session["chat_history"])


@app.route("/chat/respond", methods=["POST"])
def chat_respond():
    user_msg = request.form.get("message", "").strip()
    if not user_msg:
        return redirect(url_for("chat"))

    # Find Ember response
    msg_lower = user_msg.lower()
    ember_reply = EMBER_RESPONSES["default"]
    for keyword, response in EMBER_RESPONSES.items():
        if keyword != "default" and keyword in msg_lower:
            ember_reply = response
            break

    # Determine sentiment dot color
    from bri_engine import calculate_bri
    sentiment = calculate_bri(user_msg)
    risk = sentiment["risk_level"]
    dot_color = {"Low": "green", "Medium": "amber", "High": "red"}.get(risk, "grey")

    history = session.get("chat_history", [])
    history.append({"role": "user", "text": user_msg, "dot": dot_color})
    history.append({"role": "ember", "text": ember_reply})
    session["chat_history"] = history
    session.modified = True

    return redirect(url_for("chat"))


@app.route("/chat/clear", methods=["POST"])
def chat_clear():
    session.pop("chat_history", None)
    return redirect(url_for("chat"))


@app.route("/toolkit")
def toolkit():
    streak = db.get_streak()
    reframe_result = session.pop("reframe_result", None)
    return render_template("toolkit.html", streak=streak, reframe_result=reframe_result)


@app.route("/toolkit/reframe", methods=["POST"])
def toolkit_reframe():
    thought = request.form.get("thought", "").strip()
    if not thought:
        flash("Please enter a thought to reframe.", "warning")
        return redirect(url_for("toolkit"))
    reframe = get_reframe(thought)
    session["reframe_result"] = {"original": thought, "reframe": reframe}
    return redirect(url_for("toolkit") + "#reframe")


@app.route("/rehab-center")
def rehab_center():
    risk_counts = db.get_risk_counts(7)
    daily_breakdown = db.get_daily_breakdown(7)
    high_risk_sessions = [s for s in db.get_sessions_last_n_days(7) if s["risk_level"] == "High"]
    trend_direction = db.get_7day_trend_direction()
    sharing_enabled = session.get("sharing_enabled", False)

    return render_template(
        "rehab_center.html",
        risk_counts=risk_counts,
        daily_breakdown=daily_breakdown,
        high_risk_sessions=high_risk_sessions,
        trend_direction=trend_direction,
        linked_centers=LINKED_CENTERS,
        sharing_enabled=sharing_enabled,
    )


@app.route("/privacy")
def privacy():
    all_sessions = db.get_all_sessions()
    sharing_log = db.get_sharing_log()
    session_count = db.get_session_count()
    sharing_count = db.get_sharing_count()
    sharing_enabled = session.get("sharing_enabled", False)
    privacy_score = 55 if sharing_enabled else 95
    privacy_meter = privacy_score  # 0–100

    return render_template(
        "privacy.html",
        all_sessions=all_sessions,
        sharing_log=sharing_log,
        session_count=session_count,
        sharing_count=sharing_count,
        sharing_enabled=sharing_enabled,
        privacy_score=privacy_score,
        privacy_meter=privacy_meter,
    )


@app.route("/privacy/toggle-sharing", methods=["POST"])
def toggle_sharing():
    current = session.get("sharing_enabled", False)
    session["sharing_enabled"] = not current
    state = "enabled" if session["sharing_enabled"] else "disabled"
    flash(f"Data sharing has been {state}.", "success" if session["sharing_enabled"] else "warning")
    referrer = request.referrer or url_for("privacy")
    return redirect(referrer)


@app.route("/privacy/delete-session/<int:session_id>", methods=["POST"])
def delete_session(session_id):
    success = db.delete_session_by_id(session_id)
    if success:
        flash("Session deleted successfully.", "success")
    else:
        flash("Session not found.", "error")
    return redirect(url_for("privacy"))


@app.route("/privacy/delete-all", methods=["POST"])
def delete_all():
    db.delete_all_sessions()
    flash("All sessions and sharing logs have been permanently deleted.", "success")
    return redirect(url_for("privacy"))


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    db.init_db()
    app.run(debug=True)