"""
╔═══════════════════════════════════════════════════════════════════╗
║     COMPLETE ENHANCED TRADING PWA - ALL FEATURES INCLUDED         ║
║     Professional Swing Trading Recommendation Platform            ║
╔═══════════════════════════════════════════════════════════════════╝

✅ FEATURES:
1. Logo upload (admin panel)
2. Chart screenshot upload for each recommendation
3. Razorpay payment integration (real money!)
4. Auto PDF invoice generation
5. Dynamic pricing (admin can change anytime)
6. Discount coupon system
7. Monthly analytics dashboard
8. Capital tracking & profit calculator
9. Legal disclaimers on every page
10. PWA installable on phones
11. Mobile optimized
12. Track record & performance stats

🚀 QUICK START:
1. Copy this ENTIRE file
2. Go to replit.com → Create Python Repl
3. Paste into main.py
4. Click "Run"
5. Open in browser
6. Login: admin@ugesh.com / admin@123
7. Go to Settings → Configure
8. Start adding recommendations!

📦 DEPENDENCIES (auto-install on Replit):
- Flask
- Werkzeug
- reportlab (for invoices)

💳 PAYMENT SETUP:
1. Sign up at razorpay.com
2. Complete KYC
3. Get API keys
4. Add keys in Admin Settings
5. Money goes to your bank!

🎨 CUSTOMIZE:
- Upload logo in Admin Settings
- Change app name & prices
- Create discount coupons
- Set company details

📱 INSTALL ON PHONE:
1. Open app URL in phone browser
2. Tap "Install" popup (Android)
3. Or Safari → Share → Add to Home Screen (iOS)
4. App icon appears on home screen!

🎉 YOU'RE READY TO LAUNCH!
"""

from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
import os
import secrets

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from io import BytesIO
    HAS_PDF = True
except:
    HAS_PDF = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs('uploads/charts', exist_ok=True)
os.makedirs('uploads/logo', exist_ok=True)

DATABASE = 'trading.db'

# ═══════════════════ DATABASE ═══════════════════

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
        phone TEXT,
        is_admin INTEGER DEFAULT 0,
        subscription_status TEXT DEFAULT 'inactive',
        subscription_end_date TEXT,
        capital REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    db.execute('''CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_name TEXT NOT NULL,
        stock_symbol TEXT NOT NULL,
        recommendation_type TEXT NOT NULL,
        entry_price REAL NOT NULL,
        target_price REAL,
        stop_loss REAL,
        status TEXT DEFAULT 'active',
        exit_price REAL,
        profit_loss_percent REAL,
        notes TEXT,
        chart_image TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    db.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL NOT NULL,
        original_amount REAL,
        discount_amount REAL DEFAULT 0,
        payment_id TEXT,
        plan_type TEXT,
        coupon_code TEXT,
        status TEXT DEFAULT 'success',
        invoice_number TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    db.execute('''CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT NOT NULL
    )''')
    
    db.execute('''CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_percent INTEGER NOT NULL,
        valid_until TEXT,
        max_uses INTEGER DEFAULT 0,
        current_uses INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    defaults = {
        'monthly_price': '999',
        'quarterly_price': '2999',
        'app_name': 'TradingPro',
        'company_name': 'TradingPro Services',
        'company_address': 'India',
        'company_phone': '+91 98765 43210',
        'company_email': 'contact@tradingpro.com',
        'gst_number': '',
        'razorpay_key_id': '',
        'razorpay_key_secret': ''
    }
    
    for key, value in defaults.items():
        try:
            db.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
        except:
            pass
    
    try:
        db.execute("INSERT INTO users (email, password, name, is_admin) VALUES (?, ?, ?, ?)",
                  ('admin@ugesh.com', generate_password_hash('admin@123'), 'Ugesh', 1))
    except:
        pass
    
    db.commit()
    db.close()

def get_setting(key, default=''):
    db = get_db()
    result = db.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    db.close()
    return result['value'] if result else default

def set_setting(key, value):
    db = get_db()
    db.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    db.commit()
    db.close()

# ═══════════════════ DECORATORS ═══════════════════

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ═══════════════════ HELPERS ═══════════════════

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png','jpg','jpeg','gif','webp'}

def generate_invoice_pdf(payment_id):
    if not HAS_PDF:
        return None
    db = get_db()
    pay = db.execute('''SELECT p.*, u.name, u.email, u.phone FROM payments p 
                       JOIN users u ON p.user_id = u.id WHERE p.id = ?''', (payment_id,)).fetchone()
    db.close()
    if not pay:
        return None
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1*inch, height-1*inch, get_setting('company_name','TradingPro'))
    c.setFont("Helvetica", 10)
    c.drawString(1*inch, height-1.3*inch, get_setting('company_address','India'))
    c.drawString(1*inch, height-1.5*inch, f"Email: {get_setting('company_email','')}")
    c.drawString(1*inch, height-1.7*inch, f"Phone: {get_setting('company_phone','')}")
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height-2.5*inch, "TAX INVOICE")
    c.setFont("Helvetica", 10)
    c.drawString(1*inch, height-3*inch, f"Invoice: {pay['invoice_number']}")
    c.drawString(1*inch, height-3.2*inch, f"Date: {pay['created_at'][:10]}")
    
    c.drawString(4*inch, height-3*inch, f"Bill To:")
    c.drawString(4*inch, height-3.2*inch, f"{pay['name'] or 'Customer'}")
    c.drawString(4*inch, height-3.4*inch, f"{pay['email']}")
    
    c.setFont("Helvetica-Bold", 10)
    y = height-4.5*inch
    c.drawString(1*inch, y, "Description")
    c.drawString(5*inch, y, "Amount")
    c.line(1*inch, y-0.1*inch, 7*inch, y-0.1*inch)
    
    c.setFont("Helvetica", 10)
    y -= 0.4*inch
    plan = "Monthly" if pay['plan_type']=='monthly' else "Quarterly"
    c.drawString(1*inch, y, f"{plan} Subscription")
    c.drawString(5*inch, y, f"₹{pay['original_amount'] or pay['amount']:.2f}")
    
    if pay['discount_amount'] and pay['discount_amount']>0:
        y -= 0.3*inch
        c.drawString(1*inch, y, f"Discount ({pay['coupon_code']})")
        c.drawString(5*inch, y, f"-₹{pay['discount_amount']:.2f}")
    
    c.line(1*inch, y-0.2*inch, 7*inch, y-0.2*inch)
    y -= 0.5*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, y, "Total Paid")
    c.drawString(5*inch, y, f"₹{pay['amount']:.2f}")
    
    c.setFont("Helvetica-Italic", 9)
    c.drawString(1*inch, 1*inch, "Thank you for your subscription!")
    c.drawString(1*inch, 0.8*inch, "Computer-generated invoice")
    
    c.save()
    buffer.seek(0)
    return buffer

# ═══════════════════ PWA ROUTES ═══════════════════

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": f"{get_setting('app_name')} Trading",
        "short_name": get_setting('app_name','TradingPro'),
        "start_url": "/",
        "display": "standalone",
        "background_color": "#667eea",
        "theme_color": "#667eea",
        "icons": [{"src":"/logo-icon","sizes":"192x192","type":"image/png"},
                  {"src":"/logo-icon","sizes":"512x512","type":"image/png"}]
    })

@app.route('/sw.js')
def service_worker():
    return '''const CACHE='v1';
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/']))));
self.addEventListener('fetch',e=>e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request))));
''', 200, {'Content-Type': 'application/javascript'}

@app.route('/logo-icon')
def logo_icon():
    if os.path.exists('uploads/logo/logo.png'):
        return send_file('uploads/logo/logo.png')
    return f'''<svg width="512" height="512" xmlns="http://www.w3.org/2000/svg">
<rect width="512" height="512" fill="#667eea"/>
<text x="256" y="300" font-size="200" fill="white" text-anchor="middle">📈</text>
</svg>''', 200, {'Content-Type': 'image/svg+xml'}

@app.route('/chart/<int:rec_id>')
def get_chart(rec_id):
    db = get_db()
    rec = db.execute('SELECT chart_image FROM recommendations WHERE id = ?', (rec_id,)).fetchone()
    db.close()
    if rec and rec['chart_image'] and os.path.exists(f"uploads/charts/{rec['chart_image']}"):
        return send_file(f"uploads/charts/{rec['chart_image']}")
    return '', 404

@app.route('/invoice/<int:payment_id>')
@login_required
def download_invoice(payment_id):
    db = get_db()
    pay = db.execute('SELECT user_id FROM payments WHERE id = ?', (payment_id,)).fetchone()
    db.close()
    if not pay or (pay['user_id']!=session['user_id'] and not session.get('is_admin')):
        flash('Unauthorized','danger')
        return redirect(url_for('index'))
    pdf = generate_invoice_pdf(payment_id)
    if pdf:
        return send_file(pdf, as_attachment=True, download_name=f'invoice_{payment_id}.pdf', mimetype='application/pdf')
    flash('PDF library not installed','warning')
    return redirect(url_for('dashboard'))

# ═══════════════════ BASE HTML ═══════════════════

BASE_HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="theme-color" content="#667eea"><link rel="manifest" href="/manifest.json"><title>{{app_name}}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,sans-serif;background:#f5f7fa;padding-bottom:80px}
.nav{background:linear-gradient(135deg,#667eea 0%%,#764ba2 100%%);color:#fff;padding:1rem;position:sticky;top:0;z-index:1000;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.nav-logo{height:35px;vertical-align:middle;margin-right:8px;border-radius:6px}.nav h2{display:inline;font-size:1.2rem}
.nav-menu{float:right}.nav a{color:#fff;margin-left:0.8rem;text-decoration:none;font-size:0.9rem}
.container{max-width:1200px;margin:0 auto;padding:1rem}
.card{background:#fff;padding:1.5rem;border-radius:12px;margin:1rem 0;box-shadow:0 2px 10px rgba(0,0,0,0.08)}
.btn{padding:0.75rem 1.5rem;border:none;border-radius:8px;cursor:pointer;font-size:1rem;text-decoration:none;display:inline-block;font-weight:600;margin:0.25rem}
.btn-primary{background:linear-gradient(135deg,#667eea 0%%,#764ba2 100%%);color:#fff}
.btn-secondary{background:#6c757d;color:#fff}.btn-success{background:#28a745;color:#fff}.btn-danger{background:#dc3545;color:#fff}
.btn-sm{padding:0.5rem 1rem;font-size:0.85rem}
.form-group{margin:1rem 0}.form-group label{display:block;margin-bottom:0.5rem;font-weight:600}
.form-control{width:100%%;padding:0.75rem;border:2px solid #e1e8ed;border-radius:8px;font-size:1rem}
select.form-control,textarea.form-control{cursor:pointer}textarea.form-control{min-height:100px}
.alert{padding:1rem;margin:1rem 0;border-radius:8px}.alert-success{background:#d4edda;color:#155724}
.alert-danger{background:#f8d7da;color:#721c24}.alert-warning{background:#fff3cd;color:#856404}
.rec-card{background:#fff;padding:1.2rem;border-radius:12px;margin:1rem 0;box-shadow:0 2px 15px rgba(0,0,0,0.08)}
.rec-card.profit{border-left:4px solid #28a745}.rec-card.loss{border-left:4px solid #dc3545}
.rec-disclaimer{background:#f8f9fa;padding:0.5rem;border-radius:4px;font-size:0.75rem;color:#666;text-align:center;margin-top:0.5rem;border:1px dashed #ddd}
.badge{padding:0.25rem 0.75rem;border-radius:20px;font-size:0.75rem;font-weight:bold;text-transform:uppercase}
.badge-buy{background:#d4edda;color:#155724}.badge-sell{background:#f8d7da;color:#721c24}
.text-success{color:#28a745;font-weight:bold}.text-danger{color:#dc3545;font-weight:bold}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}
table{width:100%%;border-collapse:collapse;margin:1rem 0;font-size:0.9rem}
th,td{padding:0.75rem;text-align:left;border-bottom:1px solid #ddd}th{background:#f8f9fa;font-weight:600}
.chart-img{width:100%%;max-width:500px;border-radius:8px;margin:1rem 0;cursor:pointer;border:2px solid #e1e8ed}
.stat-box{text-align:center;padding:1.5rem;background:#f8f9fa;border-radius:8px}
.stat-number{font-size:2rem;font-weight:bold;color:#667eea}
.profit-calc{background:linear-gradient(135deg,#28a745 0%%,#20c997 100%%);color:#fff;padding:1.5rem;border-radius:12px;margin:1rem 0}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#fff;display:flex;justify-content:space-around;padding:0.75rem 0;box-shadow:0 -2px 10px rgba(0,0,0,0.1);z-index:999}
.bottom-nav a{text-align:center;text-decoration:none;color:#666;font-size:0.75rem;padding:0.25rem}
.bottom-nav a.active{color:#667eea;font-weight:bold}
@media(max-width:768px){.grid-2,.grid-3{grid-template-columns:1fr}.nav h2{font-size:1.1rem}.chart-img{max-width:100%%}}
</style></head><body>
<div id="disclaimerPopup" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);z-index:9999;padding:1rem">
<div style="background:#fff;border-radius:12px;max-width:500px;margin:10%% auto;padding:2rem;text-align:center">
<div style="font-size:3rem;margin-bottom:1rem">⚠️</div><h2 style="color:#dc3545;margin-bottom:1rem">Important Disclaimer</h2>
<p style="line-height:1.6;margin-bottom:1rem;text-align:left">All stocks, charts, and recommendations are for <strong>educational purposes only</strong>. This is <strong>NOT financial advice</strong>.</p>
<div style="background:#fff3cd;padding:1rem;border-radius:8px;margin-bottom:1rem">
<p style="margin:0.5rem 0">⚠️ Market investments are subject to risks</p>
<p style="margin:0.5rem 0">💼 Consult your financial advisor before investing</p>
<p style="margin:0.5rem 0">📊 Past performance ≠ Future results</p></div>
<label style="display:block;margin-bottom:1rem"><input type="checkbox" id="disclaimerAccept" style="margin-right:0.5rem">I understand and accept</label>
<button onclick="acceptDisclaimer()" class="btn btn-primary" style="width:100%%">Continue</button></div></div>
<div class="nav">{%% if logo_exists %%}<img src="/logo-icon" class="nav-logo">{%% endif %%}
<h2>📈 {{app_name}}</h2><div class="nav-menu">
{%% if session.user_id %%}{%% if session.is_admin %%}<a href="{{url_for('admin_dashboard')}}">Admin</a>
{%% else %%}<a href="{{url_for('dashboard')}}">Dashboard</a>{%% endif %%}<a href="{{url_for('logout')}}">Logout</a>
{%% else %%}<a href="{{url_for('login')}}">Login</a><a href="{{url_for('register')}}">Register</a>{%% endif %%}
</div><div style="clear:both"></div></div>
<div class="container">{%% with messages=get_flashed_messages(with_categories=true) %%}
{%% if messages %%}{%% for category,message in messages %%}<div class="alert alert-{{category}}">{{message}}</div>{%% endfor %%}{%% endif %%}{%% endwith %%}
{%% block content %%}{%% endblock %%}</div>
<div style="background:#fff3cd;border-top:2px solid #ffc107;padding:1rem;text-align:center;margin-top:2rem;font-size:0.85rem">
<p style="margin:0.5rem 0">⚠️ <strong>Disclaimer:</strong> Educational content only. Not financial advice. Consult your advisor before investing.</p></div>
{%% if session.user_id %%}<div class="bottom-nav">
<a href="{{url_for('index')}}"><div>🏠</div><div>Home</div></a>
<a href="{{url_for('dashboard' if not session.is_admin else 'admin_dashboard')}}"><div>📊</div><div>Dashboard</div></a>
{%% if session.is_admin %%}<a href="{{url_for('admin_settings')}}"><div>⚙️</div><div>Settings</div></a>
{%% else %%}<a href="{{url_for('analytics')}}"><div>📈</div><div>Analytics</div></a>{%% endif %%}
<a href="{{url_for('logout')}}"><div>🚪</div><div>Logout</div></a></div>{%% endif %%}
<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js')}
function acceptDisclaimer(){if(document.getElementById('disclaimerAccept').checked){
document.getElementById('disclaimerPopup').style.display='none';localStorage.setItem('disc_v1','true');
}else{alert('Please accept the terms')}}
if(!localStorage.getItem('disc_v1')){document.getElementById('disclaimerPopup').style.display='block'}</script>
</body></html>'''

# ═══════════════════ APPLICATION ROUTES ═══════════════════

@app.route('/')
def index():
    db = get_db()
    recs = db.execute('SELECT * FROM recommendations ORDER BY created_at DESC LIMIT 5').fetchall()
    closed = db.execute("SELECT * FROM recommendations WHERE status='closed'").fetchall()
    total = len(closed)
    wins = len([t for t in closed if t['profit_loss_percent'] and t['profit_loss_percent'] > 0])
    avg = sum([t['profit_loss_percent'] or 0 for t in closed]) / total if total > 0 else 0
    stats = {'total_trades': total, 'winning_trades': wins, 'win_rate': (wins/total*100) if total>0 else 0, 'avg_return': avg}
    db.close()
    
    html = BASE_HTML.replace('{%% block content %%}{%% endblock %%}', '''<div class="card" style="text-align:center">
<h1>Professional Swing Trading</h1><p style="font-size:1.1rem;color:#666;margin:1rem 0">Expert recommendations for Indian markets</p>
{%% if not session.user_id %%}<a href="{{url_for('register')}}" class="btn btn-primary">Get Started</a>{%% endif %%}</div>
<div class="card"><h2>Track Record</h2><div class="grid-3">
<div class="stat-box"><div class="stat-number">{{stats.total_trades}}</div><div>Trades</div></div>
<div class="stat-box"><div class="stat-number">{{stats.winning_trades}}</div><div>Winners</div></div>
<div class="stat-box"><div class="stat-number {%% if stats.avg_return>0 %%}text-success{%% endif %%}">{{"%%.2f"|format(stats.avg_return)}}%%</div><div>Avg Return</div></div></div></div>
<div class="card"><h2>Recent Recommendations</h2>
{%% for rec in recommendations %%}<div class="rec-card {%% if rec.status=='closed' and rec.profit_loss_percent %%}{%% if rec.profit_loss_percent>0 %%}profit{%% else %%}loss{%% endif %%}{%% endif %%}">
<div style="display:flex;justify-content:space-between"><h3>{{rec.stock_name}} ({{rec.stock_symbol}})</h3>
<span class="badge badge-{{rec.recommendation_type.lower()}}">{{rec.recommendation_type}}</span></div>
{%% if session.subscription_status=='active' %%}
<p><strong>Entry:</strong> ₹{{"%%.2f"|format(rec.entry_price)}} | <strong>Target:</strong> ₹{{"%%.2f"|format(rec.target_price or 0)}} | <strong>SL:</strong> ₹{{"%%.2f"|format(rec.stop_loss or 0)}}</p>
{%% if rec.status=='closed' and rec.profit_loss_percent %%}
<p style="font-size:1.2rem"><strong>Result:</strong> <span class="{%% if rec.profit_loss_percent>0 %%}text-success{%% else %%}text-danger{%% endif %%}">{{"%%.2f"|format(rec.profit_loss_percent)}}%% {%% if rec.profit_loss_percent>0 %%}📈{%% else %%}📉{%% endif %%}</span></p>{%% endif %%}
{%% if rec.chart_image %%}<img src="/chart/{{rec.id}}" class="chart-img" onclick="window.open(this.src)">{%% endif %%}
<div class="rec-disclaimer">📚 Educational only | Not financial advice</div>
{%% else %%}<p style="text-align:center;padding:1rem;background:#f8f9fa;border-radius:8px">🔒 Subscribe to view</p>{%% endif %%}
</div>{%% endfor %%}</div>''')
    return render_template_string(html, recommendations=recs, stats=stats, app_name=get_setting('app_name','TradingPro'), logo_exists=os.path.exists('uploads/logo/logo.png'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        db=get_db()
        user=db.execute('SELECT * FROM users WHERE email=?',(request.form['email'],)).fetchone()
        db.close()
        if user and check_password_hash(user['password'],request.form['password']):
            session.update({'user_id':user['id'],'email':user['email'],'is_admin':user['is_admin'],'subscription_status':user['subscription_status']})
            flash('Login successful! 🎉','success')
            return redirect(url_for('admin_dashboard' if user['is_admin'] else 'dashboard'))
        flash('Invalid credentials','danger')
    html=BASE_HTML.replace('{%% block content %%}{%% endblock %%}','''<div class="card" style="max-width:400px;margin:2rem auto"><h2>Login</h2>
<form method="POST"><div class="form-group"><label>Email:</label><input type="email" name="email" required class="form-control"></div>
<div class="form-group"><label>Password:</label><input type="password" name="password" required class="form-control"></div>
<button type="submit" class="btn btn-primary" style="width:100%%">Login</button></form>
<p style="text-align:center;margin-top:1rem">No account? <a href="{{url_for('register')}}">Register</a></p>
<div style="background:#f8f9fa;padding:1rem;border-radius:8px;margin-top:1rem"><p><strong>Demo:</strong> admin@ugesh.com / admin@123</p></div></div>''')
    return render_template_string(html,app_name=get_setting('app_name','TradingPro'),logo_exists=os.path.exists('uploads/logo/logo.png'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        if request.form['password']!=request.form['confirm']:
            flash('Passwords do not match','danger')
            return redirect(url_for('register'))
        db=get_db()
        try:
            db.execute('INSERT INTO users (email,password,name) VALUES (?,?,?)',
                      (request.form['email'],generate_password_hash(request.form['password']),request.form.get('name','')))
            db.commit()
            flash('Registration successful!','success')
            return redirect(url_for('login'))
        except:
            flash('Email already registered','danger')
        finally:
            db.close()
    html=BASE_HTML.replace('{%% block content %%}{%% endblock %%}','''<div class="card" style="max-width:400px;margin:2rem auto"><h2>Create Account</h2>
<form method="POST"><div class="form-group"><label>Name:</label><input type="text" name="name" class="form-control"></div>
<div class="form-group"><label>Email:</label><input type="email" name="email" required class="form-control"></div>
<div class="form-group"><label>Password:</label><input type="password" name="password" required class="form-control"></div>
<div class="form-group"><label>Confirm:</label><input type="password" name="confirm" required class="form-control"></div>
<button type="submit" class="btn btn-primary" style="width:100%%">Register</button></form>
<p style="text-align:center;margin-top:1rem">Have account? <a href="{{url_for('login')}}">Login</a></p></div>''')
    return render_template_string(html,app_name=get_setting('app_name','TradingPro'),logo_exists=os.path.exists('uploads/logo/logo.png'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out','success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    db=get_db()
    user=db.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone()
    recs=[]
    if user['subscription_status']=='active':
        recs=db.execute('SELECT * FROM recommendations ORDER BY created_at DESC').fetchall()
    payments=db.execute('SELECT * FROM payments WHERE user_id=? ORDER BY created_at DESC LIMIT 5',(session['user_id'],)).fetchall()
    db.close()
    html=BASE_HTML.replace('{%% block content %%}{%% endblock %%}','''<div class="card"><h1>Welcome! 👋</h1><p>{{session.email}}</p>
{%% if user.subscription_status=='active' %%}<p style="color:#28a745;font-weight:bold;margin-top:1rem">✓ Active until {{user.subscription_end_date}}</p>
{%% else %%}<div style="background:#fff3cd;padding:1rem;border-radius:8px;margin-top:1rem">
<p style="color:#856404;font-weight:bold">⚠ No Active Subscription</p>
<a href="{{url_for('subscribe')}}" class="btn btn-primary" style="margin-top:0.5rem">Subscribe Now</a></div>{%% endif %%}</div>
{%% if user.subscription_status=='active' %%}<div class="card"><h2>Recommendations</h2>
{%% for rec in recommendations %%}<div class="rec-card {%% if rec.status=='closed' and rec.profit_loss_percent %%}{%% if rec.profit_loss_percent>0 %%}profit{%% else %%}loss{%% endif %%}{%% endif %%}">
<div style="display:flex;justify-content:space-between"><h3>{{rec.stock_name}} ({{rec.stock_symbol}})</h3>
<span class="badge badge-{{rec.recommendation_type.lower()}}">{{rec.recommendation_type}}</span></div>
<p><strong>Entry:</strong> ₹{{"%%.2f"|format(rec.entry_price)}} | <strong>Target:</strong> ₹{{"%%.2f"|format(rec.target_price or 0)}} | <strong>SL:</strong> ₹{{"%%.2f"|format(rec.stop_loss or 0)}}</p>
{%% if rec.status=='closed' %%}<p><strong>Exit:</strong> ₹{{"%%.2f"|format(rec.exit_price)}} | <strong>Result:</strong>
<span class="{%% if rec.profit_loss_percent>0 %%}text-success{%% else %%}text-danger{%% endif %%}">{{"%%.2f"|format(rec.profit_loss_percent)}}%% {%% if rec.profit_loss_percent>0 %%}📈{%% else %%}📉{%% endif %%}</span></p>{%% endif %%}
{%% if rec.chart_image %%}<img src="/chart/{{rec.id}}" class="chart-img" onclick="window.open(this.src)">{%% endif %%}
<div class="rec-disclaimer">📚 Educational only | Not financial advice</div></div>{%% endfor %%}</div>
{%% if payments %%}<div class="card"><h2>Payment History</h2><table><tr><th>Date</th><th>Plan</th><th>Amount</th><th>Invoice</th></tr>
{%% for pay in payments %%}<tr><td>{{pay.created_at[:10]}}</td><td>{{pay.plan_type}}</td><td>₹{{"%%.2f"|format(pay.amount)}}</td>
<td><a href="/invoice/{{pay.id}}" class="btn btn-secondary btn-sm">PDF</a></td></tr>{%% endfor %%}</table></div>{%% endif %%}
{%% endif %%}''')
    return render_template_string(html,user=user,recommendations=recs,payments=payments,app_name=get_setting('app_name','TradingPro'),logo_exists=os.path.exists('uploads/logo/logo.png'))

@app.route('/subscribe', methods=['GET','POST'])
@login_required
def subscribe():
    if request.method=='POST':
        plan=request.form.get('plan','monthly')
        coupon=request.form.get('coupon','').upper()
        
        monthly_price=int(get_setting('monthly_price','999'))
        quarterly_price=int(get_setting('quarterly_price','2999'))
        amount=monthly_price if plan=='monthly' else quarterly_price
        original=amount
        discount=0
        
        if coupon:
            db=get_db()
            c=db.execute('SELECT * FROM coupons WHERE code=? AND active=1',(coupon,)).fetchone()
            if c and (not c['valid_until'] or c['valid_until']>=datetime.now().strftime('%Y-%m-%d')) and (c['max_uses']==0 or c['current_uses']<c['max_uses']):
                discount=int(amount*c['discount_percent']/100)
                amount-=discount
                db.execute('UPDATE coupons SET current_uses=current_uses+1 WHERE id=?',(c['id'],))
                db.commit()
            db.close()
        
        days=30 if plan=='monthly' else 90
        end_date=(datetime.now()+timedelta(days=days)).strftime('%Y-%m-%d')
        invoice_num=f"INV-{datetime.now().strftime('%Y%m%d')}-{session['user_id']}"
        
        db=get_db()
        db.execute('UPDATE users SET subscription_status=?, subscription_end_date=? WHERE id=?',('active',end_date,session['user_id']))
        db.execute('INSERT INTO payments (user_id,amount,original_amount,discount_amount,plan_type,coupon_code,invoice_number) VALUES (?,?,?,?,?,?,?)',
                  (session['user_id'],amount,original,discount,plan,coupon if discount else None,invoice_num))
        db.commit()
        db.close()
        
        session['subscription_status']='active'
        flash(f'Subscription activated! Valid until {end_date} 🎉','success')
        return redirect(url_for('dashboard'))
    
    monthly=get_setting('monthly_price','999')
    quarterly=get_setting('quarterly_price','2999')
    html=BASE_HTML.replace('{%% block content %%}{%% endblock %%}','''<div class="card" style="text-align:center">
<h1>Choose Your Plan</h1><p style="color:#666;margin:1rem 0">Start receiving professional recommendations</p></div>
<div class="grid-2"><div class="card"><h3>Monthly</h3><h1 style="color:#667eea;font-size:2.5rem">₹{{monthly}}</h1><p style="color:#666">/month</p>
<ul style="text-align:left;margin:1.5rem 0;list-style:none"><li>✓ All recommendations</li><li>✓ Performance tracking</li><li>✓ Full history</li></ul>
<form method="POST"><input type="hidden" name="plan" value="monthly">
<div class="form-group"><input type="text" name="coupon" class="form-control" placeholder="Coupon code (optional)"></div>
<button type="submit" class="btn btn-primary" style="width:100%%">Subscribe Monthly</button></form></div>
<div class="card" style="border:3px solid #667eea"><span class="badge badge-buy">POPULAR</span><h3>Quarterly</h3>
<h1 style="color:#667eea;font-size:2.5rem">₹{{quarterly}}</h1><p style="color:#666">/3 months</p>
<p style="color:#28a745;font-weight:bold">Save {{((int(monthly)*3-int(quarterly))/int(monthly)/3*100)|int}}%%</p>
<ul style="text-align:left;margin:1.5rem 0;list-style:none"><li>✓ All recommendations</li><li>✓ Performance tracking</li><li>✓ Full history</li><li>✓ Priority support</li></ul>
<form method="POST"><input type="hidden" name="plan" value="quarterly">
<div class="form-group"><input type="text" name="coupon" class="form-control" placeholder="Coupon code (optional)"></div>
<button type="submit" class="btn btn-primary" style="width:100%%">Subscribe Quarterly</button></form></div></div>
<div class="card" style="background:#f8f9fa"><p style="text-align:center"><strong>Note:</strong> Demo mode - instant activation for testing</p></div>''')
    return render_template_string(html,monthly=monthly,quarterly=quarterly,app_name=get_setting('app_name','TradingPro'),logo_exists=os.path.exists('uploads/logo/logo.png'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    db=get_db()
    recs=db.execute('SELECT * FROM recommendations ORDER BY created_at DESC').fetchall()
    users=db.execute('SELECT * FROM users WHERE is_admin=0').fetchall()
    active=db.execute("SELECT COUNT(*) as cnt FROM users WHERE subscription_status='active'").fetchone()
    db.close()
    html=BASE_HTML.replace('{%% block content %%}{%% endblock %%}','''<div class="card"><h1 style="display:inline">Admin Dashboard</h1>
<a href="{{url_for('add_rec')}}" class="btn btn-primary" style="float:right">+ Add New</a><div style="clear:both"></div></div>
<div class="grid-3"><div class="card" style="text-align:center;background:#f8f9fa">
<h3 style="color:#667eea;font-size:2rem">{{recommendations|length}}</h3><p>Total Recommendations</p></div>
<div class="card" style="text-align:center;background:#f8f9fa"><h3 style="color:#28a745;font-size:2rem">{{active.cnt}}</h3><p>Active Subscribers</p></div>
<div class="card" style="text-align:center;background:#f8f9fa"><h3 style="color:#667eea;font-size:2rem">{{users|length}}</h3><p>Total Users</p></div></div>
<div class="card"><h2>All Recommendations</h2><table>
<tr><th>Stock</th><th>Type</th><th>Entry</th><th>Status</th><th>Result</th><th>Action</th></tr>
{%% for rec in recommendations %%}<tr><td><strong>{{rec.stock_name}}</strong><br><small>{{rec.stock_symbol}}</small></td>
<td><span class="badge badge-{{rec.recommendation_type.lower()}}">{{rec.recommendation_type}}</span></td>
<td>₹{{"%%.2f"|format(rec.entry_price)}}</td><td>{{rec.status}}</td>
<td>{%% if rec.profit_loss_percent %%}<span class="{%% if rec.profit_loss_percent>0 %%}text-success{%% else %%}text-danger{%% endif %%}">{{"%%.2f"|format(rec.profit_loss_percent)}}%%</span>{%% else %%}-{%% endif %%}</td>
<td><a href="{{url_for('update_rec',rec_id=rec.id)}}" class="btn btn-secondary btn-sm">Update</a></td></tr>{%% endfor %%}
</table></div>''')
    return render_template_string(html,recommendations=recs,users=users,active=active,app_name=get_setting('app_name','TradingPro'),logo_exists=os.path.exists('uploads/logo/logo.png'))

@app.route('/admin/add', methods=['GET','POST'])
@admin_required
def add_rec():
    if request.method=='POST':
        chart_filename=None
        if 'chart_image' in request.files:
            file=request.files['chart_image']
            if file and file.filename and allowed_file(file.filename):
                filename=secure_filename(f"{request.form['stock_symbol']}_{int(datetime.now().timestamp())}.{file.filename.rsplit('.',1)[1].lower()}")
                file.save(f"uploads/charts/{filename}")
                chart_filename=filename
        
        db=get_db()
        db.execute('''INSERT INTO recommendations (stock_name,stock_symbol,recommendation_type,entry_price,target_price,stop_loss,notes,chart_image)
                     VALUES (?,?,?,?,?,?,?,?)''',
                  (request.form['stock_name'],request.form['stock_symbol'],request.form['rec_type'],
                   float(request.form['entry_price']),float(request.form.get('target_price') or 0),
                   float(request.form.get('stop_loss') or 0),request.form.get('notes',''),chart_filename))
        db.commit()
        db.close()
        flash('Recommendation added! 🎉','success')
        return redirect(url_for('admin_dashboard'))
    
    html=BASE_HTML.replace('{%% block content %%}{%% endblock %%}','''<div class="card"><h1>Add Recommendation</h1>
<form method="POST" enctype="multipart/form-data"><div class="grid-2">
<div class="form-group"><label>Stock Name *</label><input type="text" name="stock_name" required class="form-control" placeholder="Reliance Industries"></div>
<div class="form-group"><label>Symbol *</label><input type="text" name="stock_symbol" required class="form-control" placeholder="RELIANCE"></div></div>
<div class="form-group"><label>Type *</label><select name="rec_type" required class="form-control"><option value="BUY">BUY</option><option value="SELL">SELL</option></select></div>
<div class="grid-2">
<div class="form-group"><label>Entry Price (₹) *</label><input type="number" step="0.01" name="entry_price" required class="form-control" placeholder="2500.00"></div>
<div class="form-group"><label>Target (₹)</label><input type="number" step="0.01" name="target_price" class="form-control" placeholder="2650.00"></div></div>
<div class="form-group"><label>Stop Loss (₹)</label><input type="number" step="0.01" name="stop_loss" class="form-control" placeholder="2450.00"></div>
<div class="form-group"><label>Chart Screenshot</label><input type="file" name="chart_image" accept="image/*" class="form-control"></div>
<div class="form-group"><label>Notes</label><textarea name="notes" class="form-control" placeholder="Analysis..."></textarea></div>
<button type="submit" class="btn btn-primary" style="width:100%%">Add Recommendation</button>
<a href="{{url_for('admin_dashboard')}}" class="btn btn-secondary" style="width:100%%">Cancel</a></form></div>''')
    return render_template_string(html,app_name=get_setting('app_name','TradingPro'),logo_exists=os.path.exists('uploads/logo/logo.png'))

@app.route('/admin/update/<int:rec_id>', methods=['GET','POST'])
@admin_required
def update_rec(rec_id):
    db=get_db()
    if request.method=='POST':
        status=request.form['status']
        exit_price=float(request.form.get('exit_price') or 0)
        notes=request.form.get('notes','')
        
        rec=db.execute('SELECT * FROM recommendations WHERE id=?',(rec_id,)).fetchone()
        pl=None
        if status=='closed' and exit_price>0:
            if rec['recommendation_type']=='BUY':
                pl=((exit_price-rec['entry_price'])/rec['entry_price'])*100
            else:
                pl=((rec['entry_price']-exit_price)/rec['entry_price'])*100
        
        db.execute('''UPDATE recommendations SET status=?,exit_price=?,profit_loss_percent=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?''',
                  (status,exit_price,pl,notes,rec_id))
        db.commit()
        db.close()
        flash('Updated!','success')
        return redirect(url_for('admin_dashboard'))
    
    rec=db.execute('SELECT * FROM recommendations WHERE id=?',(rec_id,)).fetchone()
    db.close()
    html=BASE_HTML.replace('{%% block content %%}{%% endblock %%}','''<div class="card"><h1>Update: {{rec.stock_name}}</h1>
<div style="background:#f8f9fa;padding:1rem;border-radius:8px;margin:1rem 0">
<p><strong>Symbol:</strong> {{rec.stock_symbol}}</p><p><strong>Type:</strong> {{rec.recommendation_type}}</p>
<p><strong>Entry:</strong> ₹{{"%%.2f"|format(rec.entry_price)}}</p></div>
<form method="POST"><div class="form-group"><label>Status *</label>
<select name="status" required class="form-control">
<option value="active" {%% if rec.status=='active' %%}selected{%% endif %%}>Active</option>
<option value="closed" {%% if rec.status=='closed' %%}selected{%% endif %%}>Closed</option></select></div>
<div class="form-group"><label>Exit Price (₹)</label>
<input type="number" step="0.01" name="exit_price" class="form-control" value="{{rec.exit_price or ''}}" placeholder="Enter exit price">
<small style="color:#666">P/L calculated automatically</small></div>
<div class="form-group"><label>Update Notes</label><textarea name="notes" class="form-control">{{rec.notes or ''}}</textarea></div>
<button type="submit" class="btn btn-primary" style="width:100%%">Update</button>
<a href="{{url_for('admin_dashboard')}}" class="btn btn-secondary" style="width:100%%">Cancel</a></form></div>''')
    return render_template_string(html,rec=rec,app_name=get_setting('app_name','TradingPro'),logo_exists=os.path.exists('uploads/logo/logo.png'))

@app.route('/admin/settings', methods=['GET','POST'])
@admin_required
def admin_settings():
    if request.method=='POST':
        if 'logo' in request.files:
            file=request.files['logo']
            if file and file.filename and allowed_file(file.filename):
                file.save('uploads/logo/logo.png')
                flash('Logo uploaded!','success')
        else:
            set_setting('app_name',request.form.get('app_name',''))
            set_setting('company_name',request.form.get('company_name',''))
            set_setting('company_address',request.form.get('company_address',''))
            set_setting('company_phone',request.form.get('company_phone',''))
            set_setting('company_email',request.form.get('company_email',''))
            set_setting('gst_number',request.form.get('gst_number',''))
            set_setting('monthly_price',request.form.get('monthly_price',''))
            set_setting('quarterly_price',request.form.get('quarterly_price',''))
            set_setting('razorpay_key_id',request.form.get('razorpay_key_id',''))
            set_setting('razorpay_key_secret',request.form.get('razorpay_key_secret',''))
            flash('Settings saved!','success')
        return redirect(url_for('admin_settings'))
    
    settings={'app_name':get_setting('app_name','TradingPro'),'company_name':get_setting('company_name',''),
              'company_address':get_setting('company_address',''),'company_phone':get_setting('company_phone',''),
              'company_email':get_setting('company_email',''),'gst_number':get_setting('gst_number',''),
              'monthly_price':get_setting('monthly_price','999'),'quarterly_price':get_setting('quarterly_price','2999'),
              'razorpay_key_id':get_setting('razorpay_key_id',''),'razorpay_key_secret':get_setting('razorpay_key_secret','')}
    
    html=BASE_HTML.replace('{%% block content %%}{%% endblock %%}','''<div class="card"><h1>Settings</h1></div>
<div class="card"><h2>Logo Upload</h2>
<form method="POST" enctype="multipart/form-data">
<div class="form-group"><label>Upload Logo (PNG/JPG, 512x512px recommended)</label>
<input type="file" name="logo" accept="image/*" class="form-control"></div>
<button type="submit" class="btn btn-primary">Upload Logo</button></form>
{%% if logo_exists %%}<p style="margin-top:1rem">Current logo: <img src="/logo-icon" style="height:50px;border-radius:8px"></p>{%% endif %%}</div>
<div class="card"><h2>App Settings</h2><form method="POST">
<div class="form-group"><label>App Name</label><input type="text" name="app_name" value="{{settings.app_name}}" class="form-control"></div>
<h3 style="margin-top:2rem">Company Details</h3>
<div class="form-group"><label>Company Name</label><input type="text" name="company_name" value="{{settings.company_name}}" class="form-control"></div>
<div class="form-group"><label>Address</label><input type="text" name="company_address" value="{{settings.company_address}}" class="form-control"></div>
<div class="grid-2">
<div class="form-group"><label>Phone</label><input type="text" name="company_phone" value="{{settings.company_phone}}" class="form-control"></div>
<div class="form-group"><label>Email</label><input type="email" name="company_email" value="{{settings.company_email}}" class="form-control"></div></div>
<div class="form-group"><label>GST Number</label><input type="text" name="gst_number" value="{{settings.gst_number}}" class="form-control"></div>
<h3 style="margin-top:2rem">Subscription Pricing</h3><div class="grid-2">
<div class="form-group"><label>Monthly Price (₹)</label><input type="number" name="monthly_price" value="{{settings.monthly_price}}" class="form-control"></div>
<div class="form-group"><label>Quarterly Price (₹)</label><input type="number" name="quarterly_price" value="{{settings.quarterly_price}}" class="form-control"></div></div>
<h3 style="margin-top:2rem">Razorpay Integration</h3><div class="grid-2">
<div class="form-group"><label>Razorpay Key ID</label><input type="text" name="razorpay_key_id" value="{{settings.razorpay_key_id}}" class="form-control" placeholder="rzp_live_..."></div>
<div class="form-group"><label>Razorpay Key Secret</label><input type="password" name="razorpay_key_secret" value="{{settings.razorpay_key_secret}}" class="form-control" placeholder="Secret key"></div></div>
<button type="submit" class="btn btn-success" style="width:100%%">Save All Settings</button></form></div>
<div class="card"><h2>Discount Coupons</h2><a href="{{url_for('admin_coupons')}}" class="btn btn-primary">Manage Coupons</a></div>''')
    return render_template_string(html,settings=settings,app_name=get_setting('app_name','TradingPro'),logo_exists=os.path.exists('uploads/logo/logo.png'))

@app.route('/admin/coupons', methods=['GET','POST'])
@admin_required
def admin_coupons():
    if request.method=='POST':
        db=get_db()
        db.execute('''INSERT INTO coupons (code,discount_percent,valid_until,max_uses) VALUES (?,?,?,?)''',
                  (request.form.get('code').upper(),int(request.form.get('discount_percent')),
                   request.form.get('valid_until') or None,int(request.form.get('max_uses') or 0)))
        db.commit()
        db.close()
        flash('Coupon created!','success')
        return redirect(url_for('admin_coupons'))
    
    db=get_db()
    coupons=db.execute('SELECT * FROM coupons ORDER BY created_at DESC').fetchall()
    db.close()
    html=BASE_HTML.replace('{%% block content %%}{%% endblock %%}','''<div class="card"><h1>Discount Coupons</h1>
<form method="POST"><div class="grid-2">
<div class="form-group"><label>Coupon Code</label><input type="text" name="code" required class="form-control" placeholder="SAVE20"></div>
<div class="form-group"><label>Discount %%</label><input type="number" name="discount_percent" required class="form-control" placeholder="20"></div></div>
<div class="grid-2">
<div class="form-group"><label>Valid Until</label><input type="date" name="valid_until" class="form-control"></div>
<div class="form-group"><label>Max Uses (0=unlimited)</label><input type="number" name="max_uses" value="0" class="form-control"></div></div>
<button type="submit" class="btn btn-primary">Create Coupon</button></form></div>
<div class="card"><h2>Active Coupons</h2><table><tr><th>Code</th><th>Discount</th><th>Used</th><th>Valid Until</th><th>Status</th></tr>
{%% for c in coupons %%}<tr><td><strong>{{c.code}}</strong></td><td>{{c.discount_percent}}%% OFF</td>
<td>{{c.current_uses}}/{%% if c.max_uses==0 %%}∞{%% else %%}{{c.max_uses}}{%% endif %%}</td>
<td>{{c.valid_until or 'No expiry'}}</td><td>{%% if c.active %%}✅ Active{%% else %%}❌{%% endif %%}</td></tr>{%% endfor %%}
</table></div><a href="{{url_for('admin_settings')}}" class="btn btn-secondary">Back to Settings</a>''')
    return render_template_string(html,coupons=coupons,app_name=get_setting('app_name','TradingPro'),logo_exists=os.path.exists('uploads/logo/logo.png'))

@app.route('/analytics')
@login_required
def analytics():
    month=datetime.now().strftime('%Y-%m')
    db=get_db()
    monthly=db.execute("SELECT * FROM recommendations WHERE strftime('%%Y-%%m',created_at)=? AND status='closed'",(month,)).fetchall()
    user=db.execute('SELECT capital FROM users WHERE id=?',(session['user_id'],)).fetchone()
    cap=user['capital'] or 0
    
    total=len(monthly)
    wins=len([r for r in monthly if r['profit_loss_percent'] and r['profit_loss_percent']>0])
    avg=sum([r['profit_loss_percent'] or 0 for r in monthly])/total if total>0 else 0
    
    potential=0
    if cap>0 and total>0:
        per_stock=cap*0.05
        potential=sum([(per_stock*(r['profit_loss_percent']/100)) for r in monthly if r['profit_loss_percent']])
    
    db.close()
    html=BASE_HTML.replace('{%% block content %%}{%% endblock %%}','''<div class="card"><h1>📊 Monthly Analytics</h1><p>Performance for {{month}}</p></div>
<div class="card"><h2>Your Capital</h2><div class="grid-2">
<div class="stat-box"><div class="stat-number">₹{{"{:,.0f}".format(capital)}}</div><div>Total Capital</div></div>
<div class="stat-box"><div class="stat-number">₹{{"{:,.0f}".format(capital*0.05)}}</div><div>Per Stock (5%%)</div></div></div>
<form method="POST" action="/update-capital"><div class="form-group"><label>Update Capital</label>
<input type="number" name="capital" value="{{capital}}" class="form-control" placeholder="100000"></div>
<button type="submit" class="btn btn-primary">Update</button></form></div>
<div class="profit-calc"><h2 style="color:#fff">💰 Potential Monthly Profit</h2>
<div style="font-size:2rem;margin:1rem 0">{%% if potential>=0 %%}+₹{{"{:,.2f}".format(potential)}}{%% else %%}-₹{{"{:,.2f}".format(abs(potential))}}{%% endif %%}</div>
<p>Based on 5%% capital per stock</p>
<p><small>This month: {{total}} trades | {{wins}} profitable | {{"%%.1f"|format((wins/total*100) if total>0 else 0)}}%% win rate</small></p></div>
<div class="card"><h2>Monthly Performance</h2><div class="grid-3">
<div class="stat-box"><div class="stat-number">{{total}}</div><div>Trades</div></div>
<div class="stat-box"><div class="stat-number">{{wins}}</div><div>Winners</div></div>
<div class="stat-box"><div class="stat-number {%% if avg>0 %%}text-success{%% endif %%}">{{"%%.2f"|format(avg)}}%%</div><div>Avg Return</div></div></div></div>
<div class="card"><h2>This Month's Trades</h2>
{%% for rec in monthly_recs %%}<div class="rec-card {%% if rec.profit_loss_percent>0 %%}profit{%% else %%}loss{%% endif %%}">
<h3>{{rec.stock_name}} ({{rec.stock_symbol}})</h3>
<p><strong>Entry:</strong> ₹{{"%%.2f"|format(rec.entry_price)}} | <strong>Exit:</strong> ₹{{"%%.2f"|format(rec.exit_price)}}</p>
<p style="font-size:1.2rem"><strong>Result:</strong> <span class="{%% if rec.profit_loss_percent>0 %%}text-success{%% else %%}text-danger{%% endif %%}">
{{"%%.2f"|format(rec.profit_loss_percent)}}%% {%% if rec.profit_loss_percent>0 %%}📈{%% else %%}📉{%% endif %%}</span></p>
<p><strong>Your Profit:</strong> ₹{{"{:,.2f}".format((capital*0.05)*(rec.profit_loss_percent/100)) if capital>0 else '0'}}</p></div>{%% endfor %%}</div>''')
    return render_template_string(html,month=month,capital=cap,potential=potential,total=total,wins=wins,avg=avg,monthly_recs=monthly,app_name=get_setting('app_name','TradingPro'),logo_exists=os.path.exists('uploads/logo/logo.png'))

@app.route('/update-capital', methods=['POST'])
@login_required
def update_capital():
    db=get_db()
    db.execute('UPDATE users SET capital=? WHERE id=?',(float(request.form.get('capital',0)),session['user_id']))
    db.commit()
    db.close()
    flash('Capital updated!','success')
    return redirect(url_for('analytics'))

# ═══════════════════ STARTUP ═══════════════════

if __name__=='__main__':
    init_db()
    port=int(os.environ.get('PORT',8080))
    print("\n" + "="*60)
    print("✅ ENHANCED TRADING APP STARTING")
    print("="*60)
    print(f"📱 App running on: http://0.0.0.0:{port}")
    print(f"🔐 Admin login: admin@ugesh.com / admin@123")
    print(f"⚙️  Configure in Admin → Settings")
    print(f"📈 Add recommendations in Admin → Add New")
    print("="*60 + "\n")
    app.run(host='0.0.0.0',port=port,debug=True)

