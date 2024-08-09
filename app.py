from flask import Flask, session, request, render_template, redirect, make_response, flash
from flask_debugtoolbar import DebugToolbarExtension
from surveys import surveys

# Session keys
CURRENT_SURVEY_KEY = 'current_survey'
RESPONSES_KEY = 'responses'

app = Flask(__name__)
app.config['SECRET_KEY'] = "never-tell!"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)


@app.route("/")
def show_pick_survey_form():
    """Show pick-a-survey form."""
    return render_template("pick-survey.html", surveys=surveys)


@app.route("/", methods=["POST"])
def pick_survey():
    """Select a survey and begin."""
    survey_id = request.form.get('survey_code')

    if not survey_id or survey_id not in surveys:
        flash("Invalid survey selected.")
        return redirect("/")

    # Prevent re-taking a survey
    if request.cookies.get(f"completed_{survey_id}"):
        return render_template("already-done.html")

    session[CURRENT_SURVEY_KEY] = survey_id
    return render_template("survey_start.html", survey=surveys[survey_id])


@app.route("/begin", methods=["POST"])
def start_survey():
    """Initialize responses in session and redirect to first question."""
    session[RESPONSES_KEY] = []
    return redirect("/questions/0")


@app.route("/answer", methods=["POST"])
def handle_question():
    """Save response and redirect to next question."""
    choice = request.form['answer']
    text = request.form.get("text", "")

    # Update session with the new response
    responses = session.get(RESPONSES_KEY, [])
    responses.append({"choice": choice, "text": text})
    session[RESPONSES_KEY] = responses

    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]

    if len(responses) == len(survey.questions):
        return redirect("/complete")
    else:
        return redirect(f"/questions/{len(responses)}")


@app.route("/questions/<int:qid>")
def show_question(qid):
    """Display the current question."""
    responses = session.get(RESPONSES_KEY)
    survey_code = session.get(CURRENT_SURVEY_KEY)

    if responses is None or survey_code is None:
        return redirect("/")

    survey = surveys.get(survey_code)

    if survey is None or len(responses) >= len(survey.questions):
        return redirect("/complete")

    if len(responses) != qid:
        flash(f"Invalid question id: {qid}.")
        return redirect(f"/questions/{len(responses)}")

    question = survey.questions[qid]
    return render_template("question.html", question_num=qid, question=question)


@app.route("/complete")
def say_thanks():
    """Thank the user and prevent re-submission."""
    survey_id = session.get(CURRENT_SURVEY_KEY)
    responses = session.get(RESPONSES_KEY)

    if survey_id is None or responses is None:
        return redirect("/")

    survey = surveys.get(survey_id)

    if survey is None:
        flash("Invalid survey.")
        return redirect("/")

    response = make_response(render_template("completion.html", survey=survey, responses=responses))
    response.set_cookie(f"completed_{survey_id}", "yes", max_age=60)
    return response
