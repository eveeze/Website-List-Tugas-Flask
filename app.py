from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Task
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from flask import flash , get_flashed_messages
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize database and create tables
with app.app_context():
    db.create_all()

# Flask-Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def view_tasks():
    if current_user.is_admin == 1:
        return redirect(url_for('admin_users'))
    else:
        tasks = current_user.tasks
        task_count = len(tasks)
        completed_task_count = sum(1 for task in tasks if task.is_completed)
        messages = get_flashed_messages(with_categories=True)
        return render_template('tasks.html', tasks=tasks, task_count=task_count, messages=messages, completed_task_count=completed_task_count)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and password == user.password:
            login_user(user)
            flash('Berhasil Login!', 'success') 
            return redirect(url_for('view_tasks'))
        else:
            flash('Username atau password salah.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']  # Ambil nilai konfirmasi password
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Username sudah digunakan.', 'danger')
        elif password != confirm_password:  # Periksa apakah password sama dengan konfirmasi password
            flash('Konfirmasi password tidak cocok.', 'danger')
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    with app.test_request_context():
        get_flashed_messages()
    logout_user()
    flash('Logout berhasil.', 'success')
    return redirect(url_for('login'))

@app.route('/task/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        deadline_str = request.form['deadline']
        priority = int(request.form['priority'])
        user_id = current_user.get_id()

        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M') if deadline_str else None
        except ValueError:
            flash('Format waktu tidak valid.', 'danger')
            return redirect(url_for('add_task'))

        new_task = Task(title=title, description=description, deadline=deadline, priority=priority, user_id=user_id)
        
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for('view_tasks'))
        except IntegrityError as e:
            db.session.rollback()
            print(f"IntegrityError: {str(e)}")
            return 'Terjadi kesalahan saat menambahkan tugas'

    elif request.method == 'GET':
        return render_template('add_task.html')

@app.route('/task/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        task.deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')
        task.priority = int(request.form['priority'])

        try:
            db.session.commit()
            return redirect(url_for('view_tasks'))
        except IntegrityError as e:
            db.session.rollback()
            print(f"IntegrityError: {str(e)}")
            return 'Terjadi kesalahan saat mengedit tugas'

    return render_template('edit.html', task=task)

@app.route('/task/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    try:
        db.session.delete(task)
        db.session.commit()
        flash('Tugas berhasil dihapus.', 'success')
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError: {str(e)}")
        flash('Terjadi kesalahan saat menghapus tugas.', 'danger')
    
    return redirect(url_for('view_tasks'))
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.is_admin == 1:
        users = User.query.all()
        users_with_task_count = [(user, len(user.tasks)) for user in users]
        return render_template('admin_users.html', users_with_task_count=users_with_task_count)
    else:
        flash('Anda tidak memiliki izin untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('view_tasks'))
@app.route('/search', methods=['POST'])
@login_required
def search_tasks():
    search_query = request.form.get('search_query')
    filtered_tasks = []

    if search_query:
        filtered_tasks = Task.query.filter(
            (Task.title.contains(search_query)) | (Task.description.contains(search_query))
        ).filter_by(user_id=current_user.get_id()).all()

    return render_template('search_results.html', tasks=filtered_tasks)
@app.route('/task/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)

    task.is_completed = 1

    try:
        db.session.commit()
        flash('Tugas berhasil ditandai sebagai selesai.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Terjadi kesalahan saat menandai tugas sebagai selesai.', 'danger')

    return redirect(url_for('view_tasks'))
@app.route('/completed_tasks')
@login_required
def completed_tasks():
    completed_tasks = Task.query.filter_by(user_id=current_user.get_id(), is_completed=1).all()
    return render_template('completed_tasks.html', completed_tasks=completed_tasks)
@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.is_admin == 1:
        user_to_delete = User.query.get_or_404(user_id)
        if user_to_delete:
            try:
                db.session.delete(user_to_delete)
                db.session.commit()
                flash('Pengguna berhasil dihapus.', 'success')
            except:
                db.session.rollback()
                flash('Terjadi kesalahan saat menghapus pengguna.', 'danger')
        else:
            flash('Pengguna tidak ditemukan.', 'danger')
    else:
        flash('Anda tidak memiliki izin untuk menghapus pengguna.', 'danger')

    return redirect(url_for('admin_users'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        username = request.form['username']
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == old_password:  # Validasi password lama
            user.password = new_password  # Ubah kata sandi ke yang baru
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('login'))  # Redirect ke halaman login setelah perubahan

        flash('Invalid username or old password', 'danger')

    return render_template('change_password.html')
if __name__ == '__main__':
    app.run(debug=True)
