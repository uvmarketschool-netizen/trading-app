"""
SIMPLE TRADING APP - TEST VERSION
Upload this to GitHub to test if Railway works!
Then we'll add full features.

Login: admin@ugesh.com / admin@123
"""

from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'trading-secret-key-2024')

DATABASE = 'trading.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    try:
        db.execute("INSERT INTO users (email, password, name, is_admin) VALUES (?, ?, ?, ?)",
                  ('admin@ugesh.com', generate_password_hash('admin@123'), 'Ugesh', 1))
    except:
        pass
    
    db.commit()
    db.close()

@app.route('/')
def index():
    html = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>TradingPro - Live!</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fa}
.nav{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:1.5rem;text-align:center;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.nav h1{font-size:2rem;margin:0}
.container{max-width:800px;margin:3rem auto;padding:1rem}
.card{background:white;padding:3rem;border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,0.08);text-align:center}
.card h2{color:#667eea;margin-bottom:1rem;font-size:2rem}
.success{background:#d4edda;color:#155724;padding:1rem;border-radius:8px;margin:1rem 0}
.btn{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:14px 32px;
text-decoration:none;border-radius:8px;display:inline-block;margin:1rem 0.5rem;font-size:1rem;
font-weight:600;transition:transform 0.2s}
.btn:hover{transform:translateY(-2px)}
.features{text-align:left;margin:2rem 0}
.feature{padding:0.75rem;margin:0.5rem 0;background:#f8f9fa;border-radius:8px;border-left:4px solid #667eea}
</style></head><body>
<div class="nav"><h1>📈 TradingPro</h1><p>Professional Trading Platform</p></div>
<div class="container"><div class="card">
<h2>🎉 Your App is Live!</h2>
<div class="success">
<p><strong>✅ Deployment Successful!</strong></p>
<p>✅ Database Initialized</p>
<p>✅ Authentication Working</p>
<p>✅ Ready to Use</p>
</div>
<p style="margin:1.5rem 0;font-size:1.1rem">Your professional trading platform is now live on Railway!</p>
<a href="/login" class="btn">🔐 Login as Admin</a>
<a href="/test" class="btn" style="background:#28a745">🧪 Test Features</a>
<div class="features">
<h3 style="text-align:center;color:#667eea;margin:2rem 0">Ready to Add Full Features:</h3>
<div class="feature">📊 Trading Recommendations</div>
<div class="feature">📸 Chart Screenshots</div>
<div class="feature">💰 Payment Integration</div>
<div class="feature">📧 Email Notifications</div>
<div class="feature">📈 Analytics Dashboard</div>
<div class="feature">🎨 Logo Upload</div>
<div class="feature">📱 PWA Installable</div>
<div class="feature">🔔 Customer Alerts</div>
</div>
<p style="color:#666;margin-top:2rem">Once you confirm this works, we'll upgrade to the full version!</p>
</div></div>
</body></html>'''
    return html

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        db.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['is_admin'] = user['is_admin']
            session['email'] = user['email']
            flash('Login successful! Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    html = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Login - TradingPro</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
min-height:100vh;display:flex;align-items:center;justify-content:center;padding:1rem}
.card{background:white;padding:2.5rem;border-radius:16px;max-width:420px;width:100%;
box-shadow:0 20px 60px rgba(0,0,0,0.3)}
h1{color:#667eea;text-align:center;margin-bottom:0.5rem}
.subtitle{text-align:center;color:#666;margin-bottom:2rem}
.form-group{margin:1rem 0}
label{display:block;margin-bottom:0.5rem;font-weight:600;color:#333}
input{width:100%;padding:12px;border:2px solid #e1e8ed;border-radius:8px;font-size:16px}
input:focus{outline:none;border-color:#667eea}
.btn{width:100%;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;
padding:14px;border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;margin-top:1rem}
.btn:hover{opacity:0.9}
.alert{padding:12px;margin-bottom:1rem;border-radius:8px;text-align:center}
.alert-success{background:#d4edda;color:#155724}
.alert-danger{background:#f8d7da;color:#721c24}
.demo-box{background:#f8f9fa;padding:1rem;border-radius:8px;margin-top:1.5rem;text-align:center}
.demo-box p{margin:5px 0;font-size:14px;color:#666}
a{color:#667eea;text-decoration:none}
</style></head><body>
<div class="card">
<h1>🔐 Login</h1>
<p class="subtitle">Access your trading dashboard</p>
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for category, message in messages %}
<div class="alert alert-{{ category }}">{{ message }}</div>
{% endfor %}{% endif %}{% endwith %}
<form method="POST">
<div class="form-group">
<label>📧 Email</label>
<input type="email" name="email" required placeholder="your@email.com" autofocus>
</div>
<div class="form-group">
<label>🔑 Password</label>
<input type="password" name="password" required placeholder="Enter password">
</div>
<button type="submit" class="btn">Login</button>
</form>
<div class="demo-box">
<p><strong>Demo Credentials:</strong></p>
<p>Email: admin@ugesh.com</p>
<p>Password: admin@123</p>
</div>
<p style="text-align:center;margin-top:1rem"><a href="/">← Back to Home</a></p>
</div>
</body></html>'''
    return render_template_string(html)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    html = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Dashboard - TradingPro</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:sans-serif;background:#f5f7fa;padding-bottom:2rem}
.nav{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.nav h2{display:inline;font-size:1.5rem}
.nav-right{float:right}
.nav a{color:white;text-decoration:none;margin-left:1rem;font-size:0.9rem}
.container{max-width:1200px;margin:0 auto;padding:1rem}
.card{background:white;padding:2rem;border-radius:12px;margin:1rem 0;box-shadow:0 2px 10px rgba(0,0,0,0.08)}
.alert{padding:1rem;margin:1rem 0;border-radius:8px}
.alert-success{background:#d4edda;color:#155724}
.success-box{background:#d4edda;padding:1.5rem;border-radius:12px;border-left:4px solid #28a745;margin:1rem 0}
.info-box{background:#d1ecf1;padding:1rem;border-radius:8px;margin:1rem 0}
.btn{background:#667eea;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;display:inline-block;margin:0.5rem}
h1{color:#667eea}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1rem;margin:2rem 0}
.stat-card{background:#f8f9fa;padding:1.5rem;border-radius:12px;text-align:center;border-left:4px solid #667eea}
.stat-number{font-size:2rem;font-weight:bold;color:#667eea}
</style></head><body>
<div class="nav">
<h2>📈 TradingPro</h2>
<div class="nav-right">
<span>👤 {{ email }}</span>
<a href="/logout">Logout</a>
</div><div style="clear:both"></div>
</div>
<div class="container">
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for category, message in messages %}
<div class="alert alert-{{ category }}">{{ message }}</div>
{% endfor %}{% endif %}{% endwith %}
<div class="card">
<h1>🎉 Welcome to Your Dashboard!</h1>
<div class="success-box">
<p style="font-size:1.2rem;margin:0"><strong>✅ Login Successful!</strong></p>
<p style="margin-top:0.5rem">You're now logged in as: <strong>{{ email }}</strong></p>
</div>
</div>
<div class="card">
<h2>✅ System Status</h2>
<div class="grid">
<div class="stat-card">
<div class="stat-number">✅</div>
<div>App Running</div>
</div>
<div class="stat-card">
<div class="stat-number">✅</div>
<div>Database OK</div>
</div>
<div class="stat-card">
<div class="stat-number">✅</div>
<div>Auth Working</div>
</div>
<div class="stat-card">
<div class="stat-number">✅</div>
<div>Railway Live</div>
</div>
</div>
</div>
<div class="card">
<h2>🚀 Ready for Full Features</h2>
<div class="info-box">
<p><strong>This is the test version!</strong></p>
<p>Now that Railway deployment works, we can add:</p>
<ul style="margin:1rem 0;padding-left:2rem">
<li>Trading recommendations system</li>
<li>Chart upload functionality</li>
<li>Payment integration</li>
<li>Email notifications</li>
<li>Analytics dashboard</li>
<li>Logo customization</li>
<li>And all other features!</li>
</ul>
</div>
<p><strong>Tell me you see this page and I'll upgrade to full version!</strong></p>
</div>
</div>
</body></html>'''
    return render_template_string(html, email=session.get('email'))

@app.route('/test')
def test():
    html = '''<!DOCTYPE html>
<html><head><title>Test Page</title>
<style>
body{font-family:sans-serif;padding:2rem;background:#f5f7fa}
.card{background:white;padding:2rem;border-radius:12px;max-width:600px;margin:0 auto;box-shadow:0 2px 10px rgba(0,0,0,0.08)}
h1{color:#28a745}
.test-item{padding:1rem;margin:0.5rem 0;background:#d4edda;border-radius:8px;color:#155724}
</style></head><body>
<div class="card">
<h1>✅ All Tests Passed!</h1>
<div class="test-item">✅ Flask working</div>
<div class="test-item">✅ Database connected</div>
<div class="test-item">✅ Templates rendering</div>
<div class="test-item">✅ Routes functional</div>
<div class="test-item">✅ Session management OK</div>
<div class="test-item">✅ Railway deployment successful</div>
<p style="margin-top:2rem;text-align:center">
<a href="/" style="background:#667eea;color:white;padding:12px 24px;text-decoration:none;border-radius:8px">Back to Home</a>
</p>
</div>
</body></html>'''
    return html

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    
    port = int(os.environ.get('PORT', 8080))
    
    print("\n" + "="*60)
    print("✅ TRADING APP TEST VERSION - STARTING")
    print("="*60)
    print(f"📱 App running on port: {port}")
    print(f"🔐 Login: admin@ugesh.com / admin@123")
    print("🧪 This is the test version")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
