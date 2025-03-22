from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask import current_app as app
from datetime import date

from .models import *
db.create_all()

@app.route("/")
def home():
    return "<h2>Welcome to Quiz Master App</h2>"

@app.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form.get("email")
        pwd = request.form.get("pwd")
        usr = User.query.filter_by(email=email).first() #LHS is attribute name in table and RHS is data fetched from form
        # Add password verification
        if usr and usr.pwd == pwd:  # Verify password matches
            if usr.role == 0:  # Admin
                print("logged in as Admin")
                return redirect(url_for('admin_dashboard'))
            elif usr.role == 1:  # Regular user
                print("logged in as User")
                scores = Score.query.filter_by(user_id=usr.id).all()
                return render_template("user_dash.html", user=usr, scores=scores)
        return render_template("login.html", msg="Invalid Credentials")
    
    return render_template("login.html")



@app.route("/signup", methods=["GET", "POST"])
def user_signup():
    if request.method == "POST":
        email = request.form.get("email")
        full_name = request.form.get("full_name")
        qual = request.form.get("qual")
        dob = request.form.get("dob")
        pwd = request.form.get("pwd")
        
        existing_user = User.query.filter_by(email=email).first()
        
        if existing_user:
            return render_template("login.html", msg="User already exists,Please login")
        
        new_user = User(email=email, full_name=full_name, dob=dob, qual=qual, pwd=pwd, role=1)
        db.session.add(new_user)
        db.session.commit()
        print(f"User {email} created successfully")

        return redirect(url_for("user_login", msg="Signup successful! Please login."))
        
    return render_template("signup.html", msg="")


@app.route("/admin_dash")
def admin_dashboard():
    subjects = Subject.query.all()
    return render_template("admin_dash.html", name=request.args.get('email'), subjects=subjects, users={}, msg="")
    

@app.route("/user_dash", endpoint='user_dash')
def user_dashboard():
    return render_template("user_dash.html", name=request.args.get('email'), users={'name'}, msg="")


@app.route("/quiz-mgmt")
def quiz_management():
    return render_template("quiz-mgmt.html", name=request.args.get('email'), msg="")


# Routes for Subjects (Admin functionality)
@app.route("/new-subject", methods=["GET", "POST"])
def manage_subjects():
    if request.method == "POST":
        subject_name = request.form.get("name")
        description = request.form.get("desc") # Add this line for debugg
        if not subject_name:
            return render_template("new-subject.html", msg="Please enter a subject name")
        
        new_subject = Subject(name=subject_name, desc=description)
        db.session.add(new_subject)
        db.session.commit()
        print(f"Subject {subject_name} created successfully")
        return redirect(url_for("admin_dashboard"))
    
    subjects = Subject.query.all()
    return render_template("new-subject.html", subjects=subjects, msg="")

# Route to handle showing chapters for a specific subject
@app.route("/show_chapters/<int:subject_id>")
def show_chapters(subject_id):
    # Get the subject
    subject = Subject.query.get_or_404(subject_id)
    
    # Get all chapters for this subject
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    
    return render_template("show_chapters.html",subject=subject, chapters=chapters, name=request.args.get('email'))

# Route to edit a subject 
@app.route('/edit_subject/<int:subject_id>', methods=['POST'])
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    # Get form data
    new_name = request.form.get("name")
    new_desc = request.form.get("desc")
    
    if new_name:
        subject.name = new_name
    if new_desc:
        subject.desc = new_desc
        
    db.session.commit()
    print(f"Subject {subject_id} updated to {new_name}")
    
    return redirect(url_for("admin_dashboard"))

# Route to Delete a Subject
@app.route('/delete_subject/<int:subject_id>')  # Add this route decorator
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    # Delete related chapters first
    for chapter in subject.chapters:
        db.session.delete(chapter)
    db.session.delete(subject)
    db.session.commit()
    print(f"Subject {subject.name} deleted successfully")
    return redirect(url_for("admin_dashboard"))


# Routes for Chapters (Admin functionality)
@app.route('/new-chapter/<int:subject_id>', methods=['GET', 'POST'])
def new_chapter(subject_id):
    if request.method == "POST":
        name = request.form.get("name")
        desc = request.form.get("desc")
        print(f"Received data: name={name}, desc={desc}")
        if not name or not desc:
            return render_template("new-chapter.html", subject_id=subject_id, msg="Please fill all fields")
            
        new_chapter = Chapter(name=name, desc=desc, subject_id=subject_id)
        db.session.add(new_chapter)
        db.session.commit()
        print(f"Chapter {name} created successfully for subject {subject_id}")
        return redirect(url_for("admin_dashboard"))
    # Pass the subject_id to the template
    return render_template("new-chapter.html", subject_id=subject_id, msg="")

# Route to handle showing quizzes for a specific chapter
@app.route("/show_quiz/<int:subject_id>/<int:chapter_id>")
def show_quizzes(subject_id, chapter_id):
    # Get the subject and chapter
    subject = Subject.query.get_or_404(subject_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Get all quizzes for this chapter
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    
    return render_template("show_quiz.html", subject=subject,chapter=chapter,quizzes=quizzes,name=request.args.get('email'))


# Route to edit a chapter 
@app.route('/edit_chapter/<int:chapter_id>', methods=['POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    new_name = request.form.get('name')
    new_desc = request.form.get('desc')
    try:
        if new_name:
            chapter.name = new_name
        if new_desc:
            chapter.desc = new_desc
        db.session.commit()
        print(f"Chapter {chapter_id} updated to {new_name} with desc {new_desc}")
    except Exception as e:
        db.session.rollback()
        print(f"Error updating chapter: {e}")
        return render_template("show_chapters.html", subject=chapter.subject, chapters=Chapter.query.filter_by(subject_id=chapter.subject_id).all(), name=request.args.get('email'), msg="Error updating chapter")
    
    return redirect(url_for('show_chapters', subject_id=chapter.subject_id))

# Route to delete a chapter
@app.route('/delete_chapter/<int:chapter_id>')
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    Quiz.query.filter_by(chapter_id=chapter.id).delete()
    Question.query.filter_by(chapter_id=chapter.id).delete()
    db.session.delete(chapter)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# Routes for Quizzes (Admin functionality)
@app.route('/new_quiz/<int:subject_id>/<int:chapter_id>', methods=['GET', 'POST'])
def new_quiz(subject_id, chapter_id):
    subject = Subject.query.get_or_404(subject_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if request.method == 'POST':
        title = request.form['title']
        duration = request.form['duration']
        is_active = 'is_active' in request.form  # Checkbox
        
        # Correct usage: use chapter_id, not chapter_name
        quiz = Quiz(
            title=title,
            subject_id=subject_id,
            chapter_id=chapter_id,  # Use chapter_id from URL parameter
            duration=duration,
            created_by_id=1,  # Replace with actual user ID (e.g., from session)
            is_active=is_active
        )
        
        # try:
        db.session.add(quiz)
        db.session.commit()
            # flash('Quiz created successfully!', 'success')
        return redirect(url_for('show_quiz', subject_id=subject_id, chapter_id=chapter_id))
        # except Exception as e:
        #     db.session.rollback()
        #     flash(f'Error creating quiz: {str(e)}', 'error')
    
    return render_template('new-quiz.html', subject=subject, chapter=chapter)


@app.route('/show_quiz/<int:subject_id>/<int:chapter_id>')
def show_quiz(subject_id, chapter_id):
    subject = Subject.query.get_or_404(subject_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template('show_quiz.html', subject=subject, chapter=chapter, quizzes=quizzes, name="Admin")

# Route to edit a Quiz
@app.route('/edit_quiz/<int:quiz_id>', methods=['POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Get form data
    new_title = request.form.get('title')
    new_duration = request.form.get('duration')
    is_active = 'is_active' in request.form
    
    # Update quiz properties
    if new_title:
        quiz.title = new_title
    if new_duration:
        quiz.duration = new_duration
    
    quiz.is_active = is_active
    
    db.session.commit()
    print(f"Quiz {quiz_id} updated successfully")
    
    # Redirect back to show_quiz
    return redirect(url_for('show_quiz', subject_id=quiz.subject_id, chapter_id=quiz.chapter_id))


# Route to delete a Quiz
@app.route('/delete_quiz/<int:quiz_id>')
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Store the chapter_id and subject_id for redirect
    chapter_id = quiz.chapter_id
    subject_id = quiz.subject_id
    
    # Delete related questions and options first
    for question in Question.query.filter_by(quiz_id=quiz_id).all():
        Option.query.filter_by(question_id=question.id).delete()
    
    Question.query.filter_by(quiz_id=quiz_id).delete()
    
    # Delete the quiz
    db.session.delete(quiz)
    db.session.commit()
    
    print(f"Quiz {quiz_id} deleted successfully")
    
    # Redirect back to show_quizzes
    return redirect(url_for('show_quizzes', subject_id=subject_id, chapter_id=chapter_id))






# Routes for New Questions (Admin functionality)
@app.route("/new-question/<int:quiz_id>", methods=["GET", "POST"])
def manage_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    msg = ""

    if request.method == "POST":
        question_text = request.form.get("question_text")
        chapter_name = request.form.get("chapter_name")
        
        new_question = Question(quiz_id=quiz_id, chapter_name=chapter_name, question_text=question_text)
        
        db.session.add(new_question)
        db.session.commit()
        msg = "Question created successfully"
        
    
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    subjects = Subject.query.all()
    return render_template("new-question.html", quiz=quiz, questions=questions, subjects=subjects, msg=msg)


# Routes for Options (Admin functionality)
@app.route("/quiz_ques.html/<int:question_id>", methods=["GET", "POST"])
def manage_options(question_id):
    question = Question.query.get_or_404(question_id)
    if request.method == "POST":
        option_text = request.form.get("option_text")
        is_correct = bool(request.form.get("is_correct", False))
        
        new_option = Option(question_id=question_id, option_text=option_text, is_correct=is_correct)
        try:
            db.session.add(new_option)
            db.session.commit()
            print(f"Option for Question {question_id} created successfully")
            return redirect(url_for("manage_options", question_id=question_id, msg="Option created successfully"))
        except Exception as e:
            db.session.rollback()
            print(f"Error creating option: {e}")
            return render_template("quiz_ques.html.html", msg="Error creating option")
    
    options = Option.query.filter_by(question_id=question_id).all()
    return render_template("quiz_ques.html.html", question=question, options=options, msg="")


# Routes for User Taking Quiz (User functionality)
@app.route("/user/quiz/<int:quiz_id>", methods=["GET", "POST"])
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == "POST":
        user = User.query.filter_by(email=request.args.get('email')).first()  # Assume user is logged in
        if not user:
            return redirect(url_for('user_login'))
        
        score = 0
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        total_questions = len(questions)
        
        for question in questions:
            selected_option_id = request.form.get(f"question_{question.id}")
            if selected_option_id:
                selected_option = Option.query.get(selected_option_id)
                if selected_option and selected_option.is_correct:
                    score += 1

# Calculate percentage or points (e.g., 100 points max)
        final_score = (score / total_questions) * 100 if total_questions > 0 else 0
        
        # Record score
        new_score = Score(user_id=user.id, quiz_id=quiz_id, score=final_score, attempt_date=str(date.today()))
        # Update or create quiz attempt
        quiz_attempt = QuizAttempt.query.filter_by(user_id=user.id, quiz_id=quiz_id).first()
        if quiz_attempt:
            quiz_attempt.attempt_count += 1
            quiz_attempt.last_attempt_date = str(date.today())
        else:
            quiz_attempt = QuizAttempt(user_id=user.id, quiz_id=quiz_id, attempt_count=1, last_attempt_date=str(date.today()))
        
        try:
            db.session.add(new_score)
            db.session.add(quiz_attempt)
            db.session.commit()
            print(f"Quiz {quiz_id} completed with score {final_score}")
            return redirect(url_for('user_dash', msg=f"Quiz completed! Score: {final_score}%"))
        except Exception as e:
            db.session.rollback()
            print(f"Error recording score: {e}")
            return render_template("take_quiz.html", msg="Error submitting quiz", quiz=quiz)
    
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template("take_quiz.html", quiz=quiz, questions=questions, msg="")

# Routes for Quiz Scores (User functionality)
@app.route("/quiz_scores")
def quiz_scores():
    # Get user from email parameter
    email = request.args.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return redirect(url_for('user_login'))
    
    # Get all scores for the user
    scores = Score.query.filter_by(user_id=user.id).all()
    
    # Get attempt counts for each quiz
    attempts = QuizAttempt.query.filter_by(user_id=user.id).all()
    
    return render_template("quiz_scores.html", user=user, scores=scores, attempts=attempts)

# NEWLY ADDED ROUTES FOR QUIZ INTERFACE
# View Quiz Details
@app.route('/view_quiz/<int:quiz_id>')
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    email = request.args.get('email')
    
    return render_template('view_quiz.html', quiz=quiz, email=email)

# Start Quiz
@app.route('/take_quiz/<int:quiz_id>')
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    email = request.args.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return redirect(url_for('user_login'))
    
    if not quiz.questions:
        return redirect(url_for('user_dash', email=email, msg="This quiz has no questions."))
    
    # Initialize user answers list (empty for now)
    user_answers = [None] * len(quiz.questions)
    
    # Calculate start and end time
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=int(quiz.duration))
    
    # Redirect to the first question
    return redirect(url_for('quiz_question', 
                           quiz_id=quiz_id,
                           question_number=1,
                           email=email,
                           start_time=start_time.timestamp(),
                           end_time=end_time.timestamp()))

# Display Quiz Question
@app.route('/quiz/<int:quiz_id>/question/<int:question_number>')
def quiz_question(quiz_id, question_number):
    quiz = Quiz.query.get_or_404(quiz_id)
    email = request.args.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return redirect(url_for('user_login'))
    
    # Get all questions for this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    total_questions = len(questions)
    
    # Check if question exists
    if question_number > total_questions or question_number < 1:
        return redirect(url_for('user_dash', email=email))
    
    # Get the current question (adjust for 0-indexing)
    question = questions[question_number - 1]
    
    # Get question options
    options = Option.query.filter_by(question_id=question.id).all()
    
    # Get user answers from URL parameters
    user_answers = []
    for i in range(total_questions):
        param_name = f'answer_{i+1}'
        if param_name in request.args:
            user_answers.append(int(request.args.get(param_name)))
        else:
            user_answers.append(None)
    
    # Calculate time left
    start_time = datetime.fromtimestamp(float(request.args.get('start_time')))
    end_time = datetime.fromtimestamp(float(request.args.get('end_time')))
    time_left = end_time - datetime.now()
    
    # Format time left for display
    minutes = time_left.seconds // 60
    seconds = time_left.seconds % 60
    time_left_str = f"{minutes:02d}:{seconds:02d}"
    
    # Check if time is up
    if time_left.total_seconds() <= 0:
        # Auto-submit the quiz
        return redirect(url_for('submit_quiz', 
                               quiz_id=quiz_id,
                               email=email,
                               **{f'answer_{i+1}': ans for i, ans in enumerate(user_answers) if ans is not None}))
    
    return render_template('quiz_ques.html',
                          quiz=quiz,
                          question=question,
                          options=options,
                          current_question=question_number,
                          total_questions=total_questions,
                          user_answers=user_answers,
                          time_left=time_left_str,
                          show_progress_bar=True,
                          email=email)

# Save Answer and Navigate
@app.route('/save_answer', methods=['POST'])
def save_answer():
    # Get form data
    question_id = request.form.get('question_id')
    quiz_id = request.form.get('quiz_id')
    action = request.form.get('action')
    selected_answer = request.form.get('answer')
    email = request.form.get('email')
    
    # Get current question number from form
    current_question = int(request.form.get('current_question'))
    
    # Get quiz and calculate total questions
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    total_questions = len(questions)
    
    # Build URL parameters with all answers
    url_params = {}
    
    # Add existing answers from form fields
    for i in range(1, total_questions + 1):
        param_name = f'answer_{i}'
        if param_name in request.form and request.form.get(param_name) is not None:
            url_params[param_name] = request.form.get(param_name)
    
    # Update current answer
    if selected_answer is not None:
        url_params[f'answer_{current_question}'] = selected_answer
    
    # Add time parameters
    url_params['start_time'] = request.form.get('start_time')
    url_params['end_time'] = request.form.get('end_time')
    url_params['email'] = email
    
    # Handle different actions
    if action == 'save_next' and current_question < total_questions:
        # Go to next question
        return redirect(url_for('quiz_question',
                               quiz_id=quiz_id,
                               question_number=current_question + 1,
                               **url_params))
    elif action == 'save_next' and current_question == total_questions:
        # If on last question, go to previous question
        return redirect(url_for('quiz_question',
                               quiz_id=quiz_id,
                               question_number=current_question - 1,
                               **url_params))
    elif action == 'submit':
        # Submit the quiz
        return redirect(url_for('submit_quiz',
                               quiz_id=quiz_id,
                               **url_params))
    
    # Default: stay on current question
    return redirect(url_for('quiz_question',
                           quiz_id=quiz_id,
                           question_number=current_question,
                           **url_params))

# Submit Quiz
@app.route('/submit_quiz/<int:quiz_id>')
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    email = request.args.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return redirect(url_for('user_login'))
    
    # Get all questions for this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    # Calculate score
    correct_count = 0
    attempted_count = 0
    
    for i, question in enumerate(questions):
        param_name = f'answer_{i+1}'
        if param_name in request.args and request.args.get(param_name) is not None:
            attempted_count += 1
            selected_answer = int(request.args.get(param_name))
            
            # Get options for this question
            options = Option.query.filter_by(question_id=question.id).all()
            
            # Check if selected answer is correct
            if selected_answer < len(options) and options[selected_answer].is_correct:
                correct_count += 1
    
    # Calculate time taken
    start_time = datetime.fromtimestamp(float(request.args.get('start_time')))
    end_time = datetime.now()
    time_taken = end_time - start_time
    
    # Format time taken
    minutes = time_taken.seconds // 60
    seconds = time_taken.seconds % 60
    time_taken_str = f"{minutes} minutes {seconds} seconds"
    
    # Calculate score percentage
    score_percentage = (correct_count / len(questions)) * 100 if questions else 0
    
    # Save quiz score to database
    new_score = Score(
        user_id=user.id,
        quiz_id=quiz_id,
        score=score_percentage,
        attempt_date=str(date.today())
    )
    
    # Update or create attempt count
    quiz_attempt = QuizAttempt.query.filter_by(
        user_id=user.id,
        quiz_id=quiz_id
    ).first()
    
    if quiz_attempt:
        quiz_attempt.attempt_count += 1
        quiz_attempt.last_attempt_date = str(date.today())
    else:
        quiz_attempt = QuizAttempt(
            user_id=user.id,
            quiz_id=quiz_id,
            attempt_count=1,
            last_attempt_date=str(date.today())
        )
    
    # Save to database
    try:
        db.session.add(new_score)
        db.session.add(quiz_attempt)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving quiz results: {e}")
    
    # Show quiz summary
    return render_template('quiz_summary.html',
                          quiz=quiz,correct_count=correct_count,attempted_count=attempted_count,total_questions=len(questions),
                          time_taken=time_taken_str,email=email)
