"""
Mini appli web volontairement vulnerable, pour le TP DevSecOps.
NE JAMAIS l'exposer sur Internet. Usage local uniquement.
"""
import os
import sqlite3
import subprocess

from flask import Flask, request, send_file

app = Flask(__name__)

# Secret et mot de passe ecrits en dur dans le code
app.secret_key = "super-secret-key-123"
ADMIN_PASSWORD = "admin123"

DB = "app.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    c.execute("DELETE FROM users")
    c.execute("INSERT INTO users (username, password) VALUES ('admin', ?)", (ADMIN_PASSWORD,))
    c.execute("INSERT INTO users (username, password) VALUES ('alice', 'alice2026')")
    conn.commit()
    conn.close()


PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>{title}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 680px; margin: 40px auto; padding: 0 16px; color: #1c2b3a; }}
nav a {{ margin-right: 14px; color: #2457a6; }}
input, button {{ padding: 6px 10px; margin: 4px 0; }}
pre {{ background: #f1f3f5; padding: 10px; overflow-x: auto; }}
</style></head>
<body>
<nav><a href="/">Accueil</a><a href="/login">Connexion</a><a href="/search">Recherche</a><a href="/ping">Ping</a><a href="/upload">Fichiers</a></nav>
<hr>
{body}
</body></html>"""


def page(title, body):
    return PAGE.format(title=title, body=body)


@app.route("/")
def index():
    return page("Accueil", "<h1>Intranet de test</h1><p>Petite appli de démonstration pour le TP.</p>")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = """<h1>Connexion</h1>
<form method="post">
<input name="username" placeholder="Identifiant"><br>
<input name="password" type="password" placeholder="Mot de passe"><br>
<button>Se connecter</button></form>"""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = sqlite3.connect(DB)
        # Requete construite par concatenation
        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        try:
            user = conn.execute(query, (username, password)).fetchone()
        except sqlite3.Error as e:
            return page("Erreur", f"<p>Erreur SQL : {e}</p>")
        finally:
            conn.close()
        if user:
            return page("Bienvenue", f"<h1>Bienvenue {user[1]}</h1>")
        return page("Connexion", form + "<p>Identifiants incorrects.</p>")
    return page("Connexion", form)


@app.route("/search")
def search():
    q = request.args.get("q", "")
    body = """<h1>Recherche</h1>
<form><input name="q" placeholder="Rechercher"><button>OK</button></form>"""
    if q:
        # Saisie renvoyee telle quelle dans la page
        body += f"<p>Aucun résultat pour {q}</p>"
    return page("Recherche", body)


@app.route("/ping", methods=["GET", "POST"])
def ping():
    body = """<h1>Tester un hôte</h1>
<form method="post"><input name="host" placeholder="ex. 8.8.8.8"><button>Ping</button></form>"""
    if request.method == "POST":
        host = request.form.get("host", "")
        flag = "-n" if os.name == "nt" else "-c"
        # Commande systeme construite avec la saisie utilisateur
        try:
            out = subprocess.check_output(f"ping {flag} 1 {host}", shell=True, stderr=subprocess.STDOUT, timeout=10)
            body += f"<pre>{out.decode(errors='ignore')}</pre>"
        except Exception as e:
            body += f"<pre>{e}</pre>"
    return page("Ping", body)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    body = """<h1>Fichiers</h1>
<form method="post" enctype="multipart/form-data"><input type="file" name="file"><button>Envoyer</button></form>"""
    if request.method == "POST":
        f = request.files.get("file")
        if f and f.filename:
            # Aucun controle du nom ni du type de fichier
            f.save(os.path.join(UPLOAD_DIR, f.filename))
            body += f'<p>Fichier envoyé. <a href="/download?file={f.filename}">Le télécharger</a></p>'
    files = "".join(f'<li><a href="/download?file={n}">{n}</a></li>' for n in os.listdir(UPLOAD_DIR))
    body += f"<h2>Fichiers présents</h2><ul>{files}</ul>"
    return page("Fichiers", body)


@app.route("/download")
def download():
    name = request.args.get("file", "")
    # Chemin construit directement avec la saisie utilisateur
    return send_file(os.path.join(UPLOAD_DIR, name))


if __name__ == "__main__":
    init_db()
    # Mode debug actif et ecoute sur toutes les interfaces
    app.run(host="0.0.0.0", port=5000, debug=True)
