from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv  # Importe a função load_dotenv
import os  # Importe o módulo os para acessar as variáveis de ambiente
from urllib.parse import urlparse

load_dotenv('/etc/secrets/.env')

app = Flask(__name__)
csrf = CSRFProtect(app)  # Proteção CSRFfrom flask import Flask, render_template, request, redirect, url_for, session, flash


app.secret_key = os.getenv('SECRET_KEY')


# Função para conectar ao banco de dados
def conectar_banco_de_dados():
    try:
        mysql_url = os.getenv('MYSQL_URL')
        url = urlparse(mysql_url)

        conexao = mysql.connector.connect(
            host= url.hostname,
            user= url.username,
            password= url.password,
            database= url.path[1:],  # Remove a barra inicial do caminho
            port= url.port
        )
        return conexao
    except mysql.connector.Error as erro:
        print(f"Erro ao conectar ao banco de dados: {erro}")
        return None

# Função para verificar o login
def verificar_login(cursor, login, senha):
    try:
        cursor.execute("SELECT senha_login FROM login WHERE usuario_login = %s", (login,))
        resultado = cursor.fetchone()

        if resultado:
            senha_hash_armazenado = resultado[0]
            print(f"Hash armazenado: {senha_hash_armazenado}")  # Log para depuração
            if check_password_hash(senha_hash_armazenado, senha):
                print("Senha correta!")  # Log para depuração
                return True
            else:
                print("Senha incorreta!")  # Log para depuração
        else:
            print("Usuário não encontrado!")  # Log para depuração
        return False
    except mysql.connector.Error as erro:
        print(f"Erro na consulta: {erro}")
        return False

# Função para registrar um novo usuário
def registrar_usuario(cursor, login, senha):
    try:
        senha_hash = generate_password_hash(senha)
        cursor.execute(
            "INSERT INTO login (usuario_login, senha_login) VALUES (%s, %s)",
            (login, senha_hash)
        )
        return True
    except mysql.connector.Error as erro:
        print(f"Erro ao registrar usuário: {erro}")
        return False

# Rota principal (login)
@app.route('/', methods=['GET', 'POST'])
def login():
    print("Acessando a rota /login")  # Log para depuração
    if request.method == 'POST':
        print("Processando formulário de login")  # Log para depuração
        login = request.form.get('usuario_login')
        senha = request.form.get('senha_login')

        if not login or not senha:
            flash('Por favor, preencha todos os campos.', 'error')
        else:
            conexao = conectar_banco_de_dados()
            if conexao:
                cursor = conexao.cursor()
                if verificar_login(cursor, login, senha):
                    session['login'] = login
                    flash('Login realizado com sucesso!', 'success')
                    return redirect(url_for('sucesso'))
                else:
                    flash('Login ou senha incorretos.', 'error')
                cursor.close()
                conexao.close()
            else:
                flash('Erro ao conectar ao banco de dados.', 'error')
    return render_template('login.html')

# Rota de sucesso após o login
@app.route('/sucesso')
def sucesso():
    if 'login' in session:
        return render_template('sucesso.html', usuario=session['login'])
    else:
        flash('Você precisa fazer login para acessar esta página.', 'error')
        return redirect(url_for('login'))

# Rota de logout
@app.route('/logout')
def logout():
    session.pop('login', None)
    flash('Você foi deslogado com sucesso.', 'success')
    return redirect(url_for('login'))

# Rota de registro de usuários
def usuario_existe(cursor, login):
    try:
        cursor.execute("SELECT usuario_login FROM login WHERE usuario_login = %s", (login,))
        return cursor.fetchone() is not None
    except mysql.connector.Error as erro:
        print(f"Erro na consulta: {erro}")
        return False

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        login = request.form.get('usuario_login')
        senha = request.form.get('senha_login')
        confirmar_senha = request.form.get('confirmar_senha')

        if not login or not senha or not confirmar_senha:
            flash('Por favor, preencha todos os campos.', 'error')
        elif senha != confirmar_senha:
            flash('As senhas não coincidem.', 'error')
        else:
            conexao = conectar_banco_de_dados()
            if conexao:
                cursor = conexao.cursor()
                if usuario_existe(cursor, login):
                    flash('Usuário já existe.', 'error')
                elif registrar_usuario(cursor, login, senha):
                    conexao.commit()
                    flash('Usuário registrado com sucesso! Faça login.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('Erro ao registrar usuário.', 'error')
                cursor.close()
                conexao.close()
            else:
                flash('Erro ao conectar ao banco de dados.', 'error')
    return render_template('registrar.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)