'''
uruchamianie: flask --app projekt run
trzeba przejść do strony "/login"

student loguje się nr indeksu (można je zobaczyć w pliku sql) i hasłem 'haslo'.

jeśli jest w komisji, otwiera się panel komisji, jeśli nie jest w komisji, to otwiera się panel studenta
'''




from flask import Flask, render_template, request, redirect, session
import psycopg2
import psycopg2.extras 
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sk'

conn = psycopg2.connect(host='lkdb', database='mrbd', password='ml439869ml439869')


@app.route('/login', methods=['GET', 'POST'])
def login():
    cur = conn.cursor()
    cur.execute('SELECT nr_indeksu, haslo, czy_w_komisji FROM "Studenci"')
    students=cur.fetchall()
    cur.close()
    users = dict()
    for student in students:
        users[student[0]] = {'password': student[1], 'role' : "student" if not student[2] else 'komisja'}
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username]['password'] == password:
            session['logged_in'] = True
            session['username'] = username
            if users[username]['role'] == 'komisja':    
                return redirect('/komisja')
            elif users[username]['role'] == 'student':
                return redirect('/student')
        return 'Niepoprawne dane logowania. Spróbuj ponownie.'

    return render_template('login.html')


@app.route("/komisja")
def council_dashboard():
    if 'logged_in' in session:
        cur = conn.cursor()
        cur.execute('SELECT nazwa, termin_rozpoczecia, termin_zakonczenia, publikacja FROM "Wybory"')
        data=cur.fetchall()
        cur.close()
        election_data = []
        for e in data:
            status = ''
            publish_button = False
            if e[1] > datetime.date(datetime.today()):
                status = f'Rozpoczęcie {e[1]}'
            elif e[2] >= datetime.date(datetime.today()):
                status = f'W toku, zakończenie {e[2]}'
            else:
                status = f"Zakończone {e[2]}"
                if not e[3]:
                    publish_button = True
            election_data.append({'name':e[0], 'status':status, 'published':e[3], "publish_button" : publish_button})
        return render_template('council_dashboard.html', elections=election_data)
    return redirect('/')
    
@app.route('/publish-election/<election_name>', methods=['POST'])
def publish_election(election_name):
    cur = conn.cursor()
    cur.execute(f'UPDATE "Wybory" SET publikacja = %s WHERE nazwa = %s', ('true', election_name))
    cur.close()
    conn.commit()
    return redirect('/komisja')

@app.route('/register-election')
def register_election():
    return render_template('register_election.html')

@app.route('/add-election', methods=['POST'])
def add_election():
    if request.method == 'POST':
        election_name = request.form['election_name']
        election_date1 = request.form['election_date1']
        election_date2 = request.form['election_date2']
        election_date3 = request.form['election_date3']
        election_places = request.form['places']
        cur = conn.cursor()
        cur.execute('INSERT INTO "Wybory" VALUES (%s, %s, %s, %s, %s)', (election_name, election_places, election_date1, election_date2, election_date3))
        cur.close()
        conn.commit()
        return redirect('/komisja')
    
@app.route('/register-student')
def register_student():
    return render_template('register_student.html')

@app.route('/add-student', methods=['POST'])
def add_student():
    if request.method == 'POST':
        id = request.form['nr_ind']
        name = request.form['name']
        surname = request.form['surname']
        komisja = request.form['isQualified'] == 'true'
        cur = conn.cursor()
        cur.execute('INSERT INTO "Studenci" (nr_indeksu, imie, nazwisko, czy_w_komisji) VALUES (%s, %s, %s, %s)', (id, name, surname, komisja))
        cur.close()
        conn.commit()
        return redirect('/komisja')

@app.route('/student')
def student_dashboard():
    if 'logged_in' in session:
        cur = conn.cursor()
        cur.execute('SELECT nazwa, termin_zglaszania, termin_rozpoczecia, termin_zakonczenia, publikacja FROM "Wybory" JOIN "Wybory_Wyborcy" ON "Wybory".nazwa = "Wybory_Wyborcy".nazwa_wyborow WHERE nr_indeksu_wyborcy=%s', (session['username'],))
        data=cur.fetchall()
        cur.execute('SELECT nazwa_wyborow, czy_zaglosowal FROM "Wybory_Wyborcy" WHERE nr_indeksu_wyborcy=%s', (session['username'],))
        data2 = dict(cur.fetchall())
        cur.close()
        election_data = []
        for e in data:
            time = 0
            voted = data2[e[0]]
            register = True
            register_info = ''
            if e[2] > datetime.date(datetime.today()):
                time = -1
            elif e[3] >= datetime.date(datetime.today()):
                time = 0
            else:
                time = 1
            if e[1] < datetime.date(datetime.today()):
                register_info = f"Termin zgłaszania minął {e[1]}"
                register = False
            status_dict = {-1:f'Rozpoczęcie {e[2]}', 0:f"W trakcie, głosuj do {e[3]}", 1:f"Zakończone {e[3]}"}
            election_data.append({'name':e[0], "voted" : voted, 'time':time, "status": status_dict[time], 'published':e[4], "register":register, "register_info" : register_info})
        return render_template('student_dashboard.html', elections = election_data)
    return redirect('/login')

@app.route('/election/<election_name>/vote',  methods=['POST'])
def vote(election_name):
    cur = conn.cursor()
    cur.execute('SELECT imie, nazwisko FROM "Wybory_Kandydaci" JOIN "Studenci" ON "Wybory_Kandydaci".nr_indeksu_kandydata = "Studenci".nr_indeksu WHERE nazwa_wyborow=%s', (election_name,))
    tup_list = cur.fetchall()
    cur.close()
    candidates = []
    for el in tup_list:
        candidates.append({"name":el[0], 'surname':el[1]})
    return render_template('vote_page.html', election_name=election_name, candidates=candidates)


@app.route('/submit-vote', methods=['POST'])
def submit_vote():
    if request.method == 'POST':
        candidate_id = request.form['voteCheckbox']
        election_name = request.form['electionName']
        cur = conn.cursor()
        cur.execute('UPDATE "Wybory_Kandydaci" SET liczba_glosow=liczba_glosow+1 WHERE nr_indeksu_kandydata=%s AND nazwa_wyborow = %s', (candidate_id, election_name))
        cur.execute('UPDATE "Wybory_Wyborcy" SET czy_zaglosowal=true WHERE nr_indeksu_wyborcy=%s AND nazwa_wyborow = %s', (session['username'], election_name))
        cur.close()
        return redirect('/student')


@app.route('/results/<election_name>/',  methods=['POST'])
def display_results(election_name):
    if request.method == 'POST':   
        cur = conn.cursor()
        cur.execute('SELECT imie, nazwisko, liczba_glosow FROM "Wybory_Kandydaci" JOIN "Studenci" ON "Wybory_Kandydaci".nr_indeksu_kandydata = "Studenci".nr_indeksu WHERE "nazwa_wyborow" = %s ORDER BY liczba_glosow DESC;', (election_name,))
        data = cur.fetchall()
        cur.execute('SELECT liczba_posad FROM "Wybory" WHERE nazwa= %s', (election_name,))
        places = cur.fetchall()[0][0]
        cur.close()
        candidates = []
        for el in data:
            candidates.append({"name":el[0], 'surname':el[1], "votes": el[2]})
        return render_template('vote_results.html', election_name=election_name, candidates=candidates, places = places)

@app.route('/candidates/<election_name>/', methods=['POST'])
def add_candidate(election_name):
    if request.method == 'POST':
        cur = conn.cursor()
        cur.execute('SELECT nr_indeksu, imie, nazwisko FROM "Studenci" WHERE nr_indeksu NOT IN ((SELECT nr_indeksu_kandydata FROM "Wybory_Kandydaci" WHERE nazwa_wyborow=%s)) AND czy_w_komisji=false', (election_name,))
        data = cur.fetchall()
        cur.close()
        candidates = []
        for el in data:
            candidates.append({"name":el[1], 'surname':el[2], "id": el[0]})
        return render_template("add_candidates.html", election_name = election_name, candidates=candidates)

@app.route('/submit-candidates', methods=['POST'])
def submit_candidates():
    if request.method == 'POST':
        selected_candidate_ids = request.form.getlist('candidateIds[]')
        election_name = request.form["electionName"]
        cur = conn.cursor()
        for candidate in selected_candidate_ids:
            cur.execute('INSERT INTO "Wybory_Kandydaci" VALUES (%s, %s)', (election_name, candidate))
        cur.close()
        return redirect("/student")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

