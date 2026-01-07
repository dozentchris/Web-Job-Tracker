from flask import Flask, render_template, request, redirect, url_for, flash, session
from job_manager import JobManager  
import time
import webbrowser 
import threading 
import uuid
import os  

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret')

job_manager = JobManager("bewerbungen.json") 

@app.before_request
def init_session():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        # JEDER Benutzer hat EIGENE JSON-Datei!
        user_file = f"bewerbungen_{session['user_id']}.json"
        global job_manager  # Dynamisch pro User
        job_manager = JobManager(user_file)
        session['jobs'] = {job.firma: job.__dict__ for job in job_manager.jobs}

@app.route('/', methods=['GET', 'POST'])
def index():
    # Session ←→ JobManager sync
    session_jobs = session.get('jobs', {})
    
    if request.method == 'POST':
        firma = request.form['firma']
        job_manager.add_job(firma, request.form['position'], request.form['status'])
        session['jobs'] = {job.firma: job.__dict__ for job in job_manager.jobs}
        return redirect(url_for('index'))
    
    return render_template('index.html', jobs=list(session_jobs.values()))         

@app.route('/stats')
def stats():
    jobs = session.get('jobs', {}) 
    total = len(jobs)
    offen = len([j for j in jobs.values() if j['status'] == 'offen'])
    offen_prozent = round((offen/total*100), 1) if total > 0 else 0
    return render_template('stats.html', total=total, offen=offen, offen_prozent=offen_prozent)

@app.route('/delete/<firma>')
def delete_job(firma):
    for i, job in enumerate(job_manager.jobs):
        if job.firma == firma:
            job_manager.delete_job(i)
            session['jobs'] = {j.firma: j.__dict__ for j in job_manager.jobs}
            flash('🗑️ Bewerbung gelöscht!')
            return redirect(url_for('index'))
    flash('❌ Job nicht gefunden!')
    return redirect(url_for('index'))

@app.route('/edit/<firma>', methods=['GET', 'POST'])
def edit_job(firma):
    if request.method == 'POST':
        for i, job in enumerate(job_manager.jobs):
            if job.firma == firma:
                job_manager.update_job(i, 
                    request.form['firma'], 
                    request.form['position'], 
                    request.form['status'])
                session['jobs'] = {j.firma: j.__dict__ for j in job_manager.jobs}
                flash('✏️ Aktualisiert!')
                return redirect(url_for('index'))
    
    for job in job_manager.jobs:
        if job.firma == firma:
            return render_template('edit.html', job=job.__dict__, firma=firma)
    flash('❌ Job nicht gefunden!')
    return redirect(url_for('index'))
    
if __name__ == '__main__':
    
    def open_browser():
        # 0.8 Sekunden warten, dann öffnen
        time.sleep(0.8)
        webbrowser.open('http://127.0.0.1:5000')
    
    # Browser im Hintergrund öffnen
    threading.Timer(1.0, open_browser).start()
    
    app.run(debug=True, use_reloader=False)
   
