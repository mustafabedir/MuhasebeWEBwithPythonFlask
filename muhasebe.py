from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,TextField,StringField,TextAreaField,PasswordField, validators, SelectField, DateField
from passlib.hash import sha256_crypt
from functools import wraps
from IPython.display import display, HTML



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "loggedIn" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfayi Gotrme Yetkin Yok", "danger")
            return redirect(url_for("index"))
    return decorated_function

class RegisterForm(Form):
    username = StringField("Kullanici Adi", validators=[
        validators.length(min=4,max=35),
        validators.DataRequired(message="Kullanici Adi Girin")])
    password = PasswordField("Sifre", validators=[
        validators.DataRequired(message="Parola Belirleyin"),
        validators.EqualTo(fieldname = "confirm", message= "parolaniz uyusmuyor")
    ])
    confirm = PasswordField("Sifre Dogrula")

class LoginForm(Form):
    username = StringField("Kullanici Adi")
    password = PasswordField("Parola")

class MusteriForm(Form):
    tckn = StringField("TC Kimlik No")
    name = StringField("Musteri Ad - Soyad", validators=[validators.DataRequired(message="Bos")])
    phone = StringField("Musteri Telefon")
    email = StringField("Musteri E-Mail")

class SirketForm(Form):
    islemad = StringField("Islem Ad")
    aciklama = StringField("Aciklama")
    tutar = StringField("Tutar")

class CariForm(Form):
    hizmetad = StringField("Hizmet Ad")
    aciklama = StringField("Aciklama")
    tarih = DateField('Start Date', format='%d.%m.%Y', validators=(validators.Optional(),)) 
    tutar = StringField("Tutar")
    musteri = SelectField('County:', coerce=int, choices=[])

class TahsilatForm(Form):
    tutar = StringField("Tutar")
    aciklama = StringField("Aciklama")
    cari = StringField("Cari")

app = Flask(__name__)
app.secret_key="blog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "password"
app.config["MYSQL_DB"] = "muhasebedb"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


#index
@app.route("/")
def index():
    return render_template("index.html")

#login
@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method=="POST" and form.validate():
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select * from kullanici where ad = %s"
        result = cursor.execute(sorgu, (username,))

        if result>0:
            data = cursor.fetchone()
            real_password = data["sifre"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Basariyla Giris Yaptiniz", "success")
                session["loggedIn"]=True
                session["username"]=username    
                return redirect(url_for("dashboard"))
            else:
                flash("Kullanici Adi ya da Sifre Yanlis", "danger")
                return redirect(url_for("login"))
        else:
            flash("Kullanici Adi ya da Sifre Yanlis", "danger")
            return redirect(url_for("login"))
            mysql.connection.commit()
        cursor.close()
    else:
        return render_template("login.html", form = form)
        mysql.connection.commit()
        cursor.close()

#register
@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    form = RegisterForm(request.form)
    if request.method=="POST" and form.validate():
        username = form.username.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu = "Insert Into kullanici(ad, sifre) values(%s,%s)"
        cursor.execute(sorgu, (username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Basariyla Kayit Oldunuz", "success")

        return redirect(url_for("index"))
    else:
        return render_template("register.html", form = form)

#dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

#logout
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("index"))

#addmusteri
@app.route("/addmusteri", methods=["GET", "POST"])
@login_required
def addmusteri():
    form = MusteriForm(request.form)
    if request.method=="POST" and form.validate():
        tckn = form.tckn.data
        name = form.name.data
        phone = form.phone.data
        email = form.email.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert Into musteri(tckn, ad, telefon, email) values(%s,%s,%s,%s)"
        cursor.execute(sorgu, (tckn, name, phone, email))
        mysql.connection.commit()
        cursor.close()
        flash("Basariyla Kayit Oldunuz", "success")

        return redirect(url_for("musteriler"))
    else:
        return render_template("addmusteri.html", form = form)

#addsirket
@app.route("/addsirket", methods = ["GET", "POST"])
@login_required
def addsirket():
    form = SirketForm(request.form)
    if request.method=="POST" and form.validate():
        islemad = form.islemad.data
        aciklama = form.aciklama.data
        tutar = form.tutar.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert Into sirket(islemad, aciklama, tutar) values(%s,%s,%s)"
        cursor.execute(sorgu, (islemad,aciklama,tutar))    
        mysql.connection.commit()
        cursor.close()
        flash("Basariyle Kayit Olundu", "success")
        return redirect(url_for("dashboard"))
    else:
        return render_template("addsirket.html", form = form)

#addcari
@app.route("/addcari", methods = ["GET", "POST"])
@login_required
def addcari():
    form  = CariForm(request.form)
    cursor = mysql.connection.cursor()
    sorgu = "select * from musteri"
    result = cursor.execute(sorgu,)
    form.musteri.choices = [(musteri['musteriid'],musteri['ad']) for musteri in cursor.fetchall()]
    if request.method == "POST" and form.validate():
        hizmetad = form.hizmetad.data
        aciklama = form.aciklama.data
        tarih = form.tarih.data
        tutar = form.tutar.data
        musteri = form.musteri.data
        sorgu2 = "insert into cari (hizmetad, aciklama, tarih, tutar, musteriid) values(%s,%s,%s,%s,%s)"
        cursor.execute(sorgu2,(hizmetad,aciklama,tarih,tutar,musteri))
        mysql.connection.commit()
        cursor.close()
        flash("Basariyla cari Ekledin", "success")
        return redirect(url_for("cariler"))

    else:
        return render_template("addcari.html", form = form)

#musteriler
@app.route("/musteriler", methods=["GET", "POST"])
@login_required
def musteriler():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from musteri"
    result = cursor.execute(sorgu,)

    if result>0:
        musterilers = cursor.fetchall()
        return render_template("musteriler.html", musterilers= musterilers)
    else:
        return render_template("musteriler.html")

#cariler
@app.route("/cariler", methods=["GET","POST"])
@login_required
def cariler():
    cursor = mysql.connection.cursor()
    sorgu = "select cari.cariid, cari.hizmetad, cari.aciklama,cari.tarih,cari.tutar, musteri.ad from cari inner join musteri on cari.musteriid = musteri.musteriid"
    result = cursor.execute(sorgu,)
    
    if result>0:
        carilers = cursor.fetchall()
        return render_template("cariler.html", carilers = carilers)
    else:
        return render_template("cariler.html")

#sirketler
@app.route("/sirketler", methods=["GET","POST"])
@login_required
def sirketler():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from sirket"
    result = cursor.execute(sorgu,)

    if result >0:
        sirketlers = cursor.fetchall()
        return render_template("sirketler.html", sirketlers = sirketlers)
    else:
        return render_template("sirketler.html")

#deletemusteriler
@app.route("/deletemusteri/<string:id>")
@login_required
def deletemusteri(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from musteri where musteriid = %s"
    result = cursor.execute(sorgu,(id))

    if result >0:
        sorgu2 = "Delete From musteri where musteriid = %s"
        cursor.execute(sorgu2,(id))
        mysql.connection.commit()
        flash("Musteri Basariyla Siilindi", "success")
        return redirect(url_for("musteriler"))

    else:
        flash("Musteri Yok", "danger")
        return redirect(url_for("dashboard"))

#deletecariler
@app.route("/deletecariler/<string:id>")
@login_required
def deletecariler(id):
    cursor = mysql.connection.cursor()
    sorgu =  "select * from cari where cariid = %s"
    result = cursor.execute(sorgu,(id,))

    if result>0:
        sorgu2 = "delete from cari where cariid = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        flash("cariler basariyla silindi","success")
        return redirect(url_for("cariler"))
    else:
        flash("cari bulunamadi")
        return redirect(url_for("dashboard"))

#deletesirketler
@app.route("/deletesirket/<string:id>")
@login_required
def deletesirket(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from sirket where sirketid =  %s"
    result = cursor.execute(sorgu, (id,))

    if result >0:
        sorgu2 = "delete from sirket where sirketid = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        flash("basariyla sirket gideri silindi","success")
        return redirect(url_for("dashboard"))

    else:
        flash("sirket  gideri bulunamadi","danger")
        return redirect(url_for("dashboard"))
    
#guncellemusteri
@app.route("/editmusteri/<string:id>",methods=["GET","POST"])
@login_required
def editmusteri(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "select * from musteri where musteriid = %s"
        result = cursor.execute(sorgu,(id,))

        if result ==0:
            flash("boyle bir musteri yok", "danger")
            return redirect(url_for("dashboard"))

        else:
            musteri = cursor.fetchone()
            form = MusteriForm()

            form.tckn.data = musteri["tckn"]
            form.name.data = musteri["ad"]
            form.phone.data = musteri["telefon"]
            form.email.data = musteri["email"]

            return render_template("updatemusteri.html", form = form)
    else:
        form = MusteriForm(request.form)
        newtckn = form.tckn.data
        newname = form.name.data
        newphone = form.phone.data
        newemail = form.email.data

        sorgu2 = "Update musteri set tckn = %s , ad = %s, telefon = %s , email = %s where musteriid = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newtckn,newname,newphone,newemail,id))
        mysql.connection.commit()

        flash("Musteri basariyla guncellendi", "success")
        return redirect(url_for("musteriler"))


#guncellesirket
@app.route("/editsirket/<string:id>",methods=["GET","POST"])
@login_required
def editsirket(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "select * from sirket where sirketid = %s"
        result = cursor.execute(sorgu,(id,))

        if result ==0:
            flash("boyle bir sirket yok", "danger")
            return redirect(url_for("dashboard"))

        else:
            sirket = cursor.fetchone()
            form = SirketForm()

            form.islemad.data = sirket["islemad"]
            form.aciklama.data = sirket["aciklama"]
            form.tutar.data = sirket["tutar"]
            

            return render_template("updatesirket.html", form = form)
    else:
        form = SirketForm(request.form)
        newislemad = form.islemad.data
        newaciklama = form.aciklama.data
        newtutar = form.tutar.data
        

        sorgu2 = "Update sirket set islemad = %s , aciklama = %s, tutar = %s  where sirketid = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newislemad,newaciklama,newtutar,id))
        mysql.connection.commit()

        flash("sirket basariyla guncellendi", "success")
        return redirect(url_for("dashboard"))

#guncellecari
@app.route("/editcariler/<string:id>", methods=["GET","POST"])
@login_required
def editcariler(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "select * from cari where cariid = %s "
        result = cursor.execute(sorgu,(id,))
        if result ==0:
            flash("Boyle bir Cari yok ya da yetkiniz yok","danger")
            return redirect(url_for("dashboard"))
        else:
            cari = cursor.fetchone()
            form = CariForm()
            form.hizmetad.data = cari["hizmetad"]
            form.aciklama.data = cari["aciklama"]
            form.tarih.data = cari["tarih"]
            form.tutar.data = cari["tutar"]
            cursor2 = mysql.connection.cursor()
            sorgu2 = "select * from musteri"
            cursor2.execute(sorgu2,)
            form.musteri.choices = [(musteri['musteriid'],musteri['ad']) for musteri in cursor2.fetchall()]
            return render_template("updatecariler.html", form = form)

    else:
        form = CariForm(request.form)
        newislemad = form.hizmetad.data
        newaciklama = form.aciklama.data
        newtutar = form.tutar.data
        newmusteri = form.musteri.data

        sorgu3 = "Update cari Set hizmetad = %s , aciklama = %s ,  tutar = %s , musteriid = %s where cariid = %s "
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu3,(newislemad, newaciklama, newtutar, newmusteri, id))
        mysql.connection.commit() 

        flash("cari basariyla guncellendi", "success")
        return redirect(url_for("cariler"))

#cariode
@app.route("/odecari/<string:id>", methods=["GET", "POST"])
@login_required
def odecari(id):
    form  = TahsilatForm(request.form)
    form2 = CariForm(request.form)
    cursor = mysql.connection.cursor()
    form.cari.data = id
    if request.method == "POST" and form.validate():
        tutar = form.tutar.data
        aciklama = form.aciklama.data
        cari = form.cari.data
        sorgu2 = "insert into tahsilat (tutar, aciklama, cariid) values(%s,%s,%s)"
        cursor.execute(sorgu2,(tutar,aciklama,cari))
        
        #cari
        tutarcari = form2.tutar.data

        if tutarcari ==0:
            sorgu3 = "Update cari Set tutar = tutar - %s where cariid = %s"
            cursor.execute(sorgu3,(tutarcari,id))
            
        
        mysql.connection.commit()
        cursor.close()
        flash("Basasriyla Odeme Yaptin", "success")
        return redirect(url_for("fatura"))

    else:
        return render_template("odecari.html", form = form)

#fatura
@app.route("/fatura", methods=["GET", "POST"])
@login_required
def fatura():
    cursor = mysql.connection.cursor()
    sorgu = "select tahsilat.tahsilatid, tahsilat.tutar, tahsilat.aciklama, cari.hizmetad, musteri.ad, musteri.tckn from tahsilat inner join cari on tahsilat.cariid = cari.cariid inner join musteri on musteri.musteriid = cari.musteriid"

    result = cursor.execute(sorgu,)
    
    if result>0:
        faturalar = cursor.fetchall()
        return render_template("fatura.html", faturalar = faturalar)
    else:
        return render_template("fatura.html")

#deletefatura
@app.route("/deletefatura/<string:id>")
@login_required
def deletefatura(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from tahsilat where tahsilatid =  %s"
    result = cursor.execute(sorgu, (id,))

    if result >0:
        sorgu2 = "delete from tahsilat where tahsilatid = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        flash("basariyla fatura gideri silindi","success")
        return redirect(url_for("fatura"))

    else:
        flash("sirket  gideri bulunamadi","danger")
        return redirect(url_for("fatura"))






if __name__=="__main__":
    app.run(debug=True)