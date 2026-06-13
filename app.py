import streamlit as st
import sqlite3
import pandas as pd

# ---------------- DATABASE ---------------- #

conn = sqlite3.connect("studybuddy.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    subject TEXT,
    exam TEXT,
    study_time TEXT,
    mode TEXT
)
""")

conn.commit()

# ---------------- FUNCTIONS ---------------- #

def register_user(name, email, password, subject, exam, study_time, mode):
    try:
        c.execute("""
        INSERT INTO users
        (name,email,password,subject,exam,study_time,mode)
        VALUES (?,?,?,?,?,?,?)
        """,
        (name,email,password,subject,exam,study_time,mode))
        conn.commit()
        return True
    except:
        return False


def login_user(email, password):
    c.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    )
    return c.fetchone()


def get_all_users():
    return pd.read_sql_query("SELECT * FROM users", conn)


def calculate_match(user, candidate):
    score = 0

    if user["subject"] == candidate["subject"]:
        score += 50

    if user["study_time"] == candidate["study_time"]:
        score += 30

    if user["exam"] == candidate["exam"]:
        score += 20

    return score


def find_matches(user_email):
    users = get_all_users()

    current_user = users[users["email"] == user_email].iloc[0]

    matches = []

    for _, row in users.iterrows():

        if row["email"] == user_email:
            continue

        score = calculate_match(current_user, row)

        matches.append({
            "Name": row["name"],
            "Subject": row["subject"],
            "Exam": row["exam"],
            "Study Time": row["study_time"],
            "Mode": row["mode"],
            "Match Score": score
        })

    matches_df = pd.DataFrame(matches)

    if not matches_df.empty:
        matches_df = matches_df.sort_values(
            by="Match Score",
            ascending=False
        )

    return matches_df


# ---------------- SESSION ---------------- #

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "email" not in st.session_state:
    st.session_state.email = ""

# ---------------- UI ---------------- #
st.markdown("""
<div style='text-align:center; padding:30px 0;'>
    <h1 style='color:#6366F1;'>📚 Study Buddy Matcher</h1>
    <h3>Find Your Perfect Study Partner</h3>
    <p style='font-size:18px; color:gray;'>
        Connect with students studying the same subjects,
        preparing for the same exams, and available at the same time.
    </p>
</div>
""", unsafe_allow_html=True)

menu = ["Login", "Register"]

if not st.session_state.logged_in:

    choice = st.sidebar.selectbox("Menu", menu)

    # REGISTER

    if choice == "Register":

        st.subheader("Create Account")

        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        subject = st.selectbox(
            "Subject",
            ["Maths", "Physics", "Chemistry", "Python", "DBMS"]
        )

        exam = st.selectbox(
            "Preparing For",
            ["Semester Exam", "Placement", "Competitive Exam"]
        )

        study_time = st.selectbox(
            "Preferred Study Time",
            ["Morning", "Afternoon", "Evening", "Night"]
        )

        mode = st.selectbox(
            "Study Mode",
            ["Online", "In-Person"]
        )

        if st.button("Register"):

            success = register_user(
                name,
                email,
                password,
                subject,
                exam,
                study_time,
                mode
            )

            if success:
                st.success("Registration Successful!")
            else:
                st.error("Email already exists!")

    # LOGIN

    elif choice == "Login":

        st.subheader("Login")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            user = login_user(email, password)

            if user:
                st.session_state.logged_in = True
                st.session_state.email = email
                st.rerun()

            else:
                st.error("Invalid Credentials")

# DASHBOARD

else:

    st.success(f"Logged in as {st.session_state.email}")

    tab1, tab2 = st.tabs(
        ["Find Study Buddies", "All Students"]
    )

    with tab1:

        st.subheader("Recommended Study Buddies")

        matches = find_matches(
            st.session_state.email
        )

        if matches.empty:
            st.info("No matches found.")
        else:
            st.dataframe(matches)

    with tab2:

        st.subheader("Registered Students")

        df = get_all_users()

        st.dataframe(
            df[
                [
                    "name",
                    "subject",
                    "exam",
                    "study_time",
                    "mode"
                ]
            ]
        )

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.email = ""
        st.rerun()