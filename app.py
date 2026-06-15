import streamlit as st
import sqlite3
import pandas as pd

# CUSTOM CSS
st.markdown("""
<style>
.stButton > button {
    background-color: #4F46E5;
    color: white;
    border-radius: 10px;
    border: none;
}

.stButton > button:hover {
    background-color: #4338CA;
}

.stSuccess {
    border-radius: 10px;
}

.stTextInput > div > div > input {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# rest of your code starts here
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
    phone TEXT,
    mode TEXT
)
""")

conn.commit()
c.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_email TEXT,
    receiver_email TEXT,
    status TEXT DEFAULT 'Pending'
)
""")

conn.commit()
# ---------------- FUNCTIONS ---------------- #

def register_user(name, email, password, subject, exam, study_time, phone, mode):
    try:
        c.execute("""
        INSERT INTO users
        (name,email,password,subject,exam,study_time,phone,mode)
        VALUES (?,?,?,?,?,?,?)
        """,
        (name,email,password,subject,exam,study_time,phone,mode))
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

def get_user_email(name):
    c.execute(
        "SELECT email FROM users WHERE name = ?",
        (name,)
    )
    result = c.fetchone()

    if result:
        return result[0]
    return None

def get_user_details(email):
    c.execute(
        """
        SELECT name, email, phone
        FROM users
        WHERE email = ?
        """,
        (email,)
    )
    return c.fetchone()

def update_request_status(sender_email, receiver_email, status):
    c.execute(
        """
        UPDATE requests
        SET status = ?
        WHERE sender_email = ? AND receiver_email = ?
        """,
        (status, sender_email, receiver_email)
    )
    conn.commit()

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

st.image(
    "https://images.unsplash.com/photo-1522202176988-66273c2fd55f",
    use_container_width=True
)

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
        phone = st.text_input("Phone Number")

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
                phone,
                mode
            )

            if success:
                st.success("Registration Successful!")
            else:
                st.error("Email already exists!")

    # LOGIN

    elif choice == "Login":

         left, center, right = st.columns([1, 2, 1])

         with center:

                st.subheader("Login")

                email = st.text_input("Email")

                password = st.text_input(
                "Password",
                type="password")
        

                login_btn = st.button(
                "Login",
                use_container_width=True
                )
        

                if login_btn:

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

    tab1, tab2, tab3 = st.tabs(
        ["Find Study Buddies", "Student Directory","Requests"]
    )

    with tab1:

        st.subheader("Recommended Study Buddies")

        matches = find_matches(
            st.session_state.email
        )

        if matches.empty:
            st.info("No matches found.")
        else:
             st.write(matches)

             for _, row in matches.iterrows():
              with st.container(border=True):
               score_percent = min(row["Match Score"] * 50, 100)

               st.write(f"👤 Name: {row['Name']}")
               st.write(f"📚 Subject: {row['Subject']}")
               st.write(f"📄 Exam: {row['Exam']}")
               st.write(f"⏰ Study Time: {row['Study Time']}")
               st.write(f"💻 Mode: {row['Mode']}")
               st.write(f"⭐ Match Score: {score_percent:.0f}%")

            
    

              st.progress(score_percent / 100)
              if st.button(
              f"🤝 Connect with {row['Name']}",
             key=f"connect_{row['Name']}"
             ):
               

               receiver_email = get_user_email(row["Name"])

               c.execute("""
SELECT *
FROM requests
WHERE sender_email = ?
AND receiver_email = ?
AND status = 'Pending'
""",
(
    st.session_state.email,
    receiver_email
))

existing = c.fetchone()

if existing:
    st.warning("Request already sent!")  
else:
    c.execute("""
    INSERT INTO requests
    (sender_email, receiver_email)
    VALUES (?, ?)
    """,
    (
        st.session_state.email,
        receiver_email
    ))        
                 

    conn.commit()
    st.success("Connection request sent!")

    st.divider()

    with tab2:

        st.subheader("Registered Students")
        df = get_all_users()

        search = st.text_input("🔍 Search by Subject")

    if search:
        df = df[df["subject"].str.contains(search, case=False)]

        col1, col2 = st.columns(2)

        with col1:
         st.metric("Total Students", len(df))

        with col2:
         st.metric("Subjects", df["subject"].nunique())
         
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
    with tab3:
        st.subheader("Connection Requests")
        c.execute(
            """
            SELECT sender_email
            FROM requests
            WHERE receiver_email = ?
            AND status = 'Pending'
            """,
            (st.session_state.email,)
        )

        requests = c.fetchall()
    

    if requests:
     for i, req in enumerate(requests):

        st.info(f"📩 Request from: {req[0]}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                f"✅ Accept {req[0]}",
                key=f"accept_{i}"
            ):
                update_request_status(
                    req[0],
                    st.session_state.email,
                    "Accepted"
                )
                st.success("Request accepted!")

                sender_details = get_user_details(req[0])

                if sender_details:
                    st.write("### Contact Details")
                    st.write(f"👤 Name: {sender_details[0]}")
                    st.write(f"📧 Email: {sender_details[1]}")
                    st.write(f"📱 Phone: {sender_details[2]}")

        with col2:
            if st.button(
                f"❌ Reject {req[0]}",
                key=f"reject_{i}"
            ):
                update_request_status(
                    req[0],
                    st.session_state.email,
                    "Rejected"
                )
                st.warning("Request rejected!")
    else:
     st.write("No requests yet.")

if st.button("Logout"):
          st.session_state.logged_in = False
          st.session_state.email = ""
          st.rerun()