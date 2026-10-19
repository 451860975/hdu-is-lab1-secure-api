from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import jwt
import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "super‑secret‑key‑change‑me‑for‑production"

db = SQLAlchemy(app)

# 用户数据表
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

# 留言表（给第三个自定义接口）
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    user_id = db.Column(db.Integer)

with app.app_context():
    db.create_all()
    # 初始化测试用户，密码test1234
    test_pw = b"test1234"
    hashed = bcrypt.hashpw(test_pw, bcrypt.gensalt())
    if not User.query.filter_by(username="testuser").first():
        new_user = User(username="testuser", password_hash=hashed.decode("utf‑8"))
        db.session.add(new_user)
        db.session.commit()

# JWT校验中间件
def token_required(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message":"Token missing"}),401
        try:
            token = token.replace("Bearer ","")
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user_id = payload["user_id"]
        except Exception as e:
            return jsonify({"message":"Invalid token"}),401
        return func(current_user_id,*args,**kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# 接口1 POST /auth/login
@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg":"user not found"}),401
    if bcrypt.checkpw(password.encode("utf‑8"), user.password_hash.encode("utf‑8")):
        payload = {
            "user_id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }
        token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
        return jsonify({"access_token":token})
    return jsonify({"msg":"wrong password"}),401

# 接口2 GET /api/data 需要鉴权
@app.route("/api/data", methods=["GET"])
@token_required
def get_data(current_user_id):
    user_list = [{"id":u.id,"username":u.username} for u in User.query.all()]
    return jsonify({"users":user_list})

# 接口3 自定义接口 POST /api/post 提交留言
@app.route("/api/post", methods=["POST"])
@token_required
def create_post(current_user_id):
    raw_content = request.json.get("content","")
    # XSS防护：简单转义特殊字符
    safe_content = raw_content.replace("<","&lt;").replace(">","&gt;")
    new_post = Post(content=safe_content, user_id=current_user_id)
    db.session.add(new_post)
    db.session.commit()
    return jsonify({"post_id":new_post.id,"content":safe_content})

if __name__ == "__main__":
    app.run(debug=False)
