from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, FloatField
from wtforms.validators import DataRequired, NumberRange
from datetime import datetime
import pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

##CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///cost_detail.db"
# Create the extension
db = SQLAlchemy()
# initialise the app with the extension
db.init_app(app)


##CREATE TABLE

class TourName(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tour_title = db.Column(db.String(250), nullable=False, unique=True)
    member_num = db.Column(db.Integer, nullable=True)
    all_member = db.Column(db.String(250), nullable=True)

class Cost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tour_title = db.Column(db.String(250), nullable=False)
    item = db.Column(db.String(250), nullable=False)
    all_member = db.Column(db.String(250), nullable=False)
    who_pay = db.Column(db.String(250), nullable=False)
    money = db.Column(db.Float, nullable=False)
    who_apportion = db.Column(db.String(250), nullable=False)
    insert_time = db.Column(db.String(25), nullable=False)
    update_time = db.Column(db.String(25), nullable=False)



# Create table schema in the database. Requires application context.
with app.app_context():
    db.create_all()

# the tour title input and check
class TitleInput(FlaskForm):
    title = StringField("Apportionment Title", validators=[DataRequired()])
    submit = SubmitField("Confirm")

class CostInput(FlaskForm):
    item = StringField("Cost Item", validators=[DataRequired()])
    who_pay = SelectField("Who Pay", validators=[DataRequired()])
    money = FloatField("Money", validators=[DataRequired(), NumberRange(min=0,message='Must over 0.')])

class Calculator:
    def __init__(self, tour_title):
        self.tour_title = tour_title
        # .all() -> 讓scalars()的內容變成list
        self.tour_base = db.session.execute(db.select(Cost).where(Cost.tour_title == self.tour_title)).scalars().all()
        self.all_member = eval(self.tour_base[0].all_member)
        self.debt = {}
        self.result = {}
        self.calculator()

    def calculator(self):
        for man in self.all_member:
            self.debt[man] = []
        for detail in self.tour_base:
            pay_man = detail.who_pay
            money = detail.money
            apportion_men = eval(detail.who_apportion)
            print(apportion_men)
            apportion_num = len(apportion_men)
            apportion_money = money / apportion_num
            print(apportion_money)
            for man in self.all_member:
                # 是需要分帳的人
                if man in apportion_men:
                    # 是代墊的人
                    if man == pay_man:
                        self.debt[man].append(money - apportion_money)
                    else:
                        self.debt[man].append(-1 * apportion_money)
                else:
                    if man == pay_man:
                        self.debt[man].append(money)
                    else:
                        self.debt[man].append(0)
        print(self.debt)
        for (man, value) in self.debt.items():
            self.result[man] = sum(value)
        print(self.result)
        # return self.result

    def summary(self):
        final_result = []
        temporary_result = {}
        for (man, value) in self.result.items():
            temporary_result[man] = {}
        print(temporary_result)

        while True:
            max_man = [man for (man, value) in self.result.items() if value == max(self.result.values())][0]
            min_man = [man for (man, value) in self.result.items() if value == min(self.result.values())][0]
            max_value = [value for (man, value) in self.result.items() if value == max(self.result.values())][0]
            min_value = [value for (man, value) in self.result.items() if value == min(self.result.values())][0]
            print(f"{min_man}  {min_value}")
            print(f"{max_man}  {max_value}")
            # 重頭到尾只有一個人，類似自己記帳
            if max_value == min_value == 0:
                expense = sum([cost.money for cost in self.tour_base])
                print(f"Your total cost is {expense}")
                temporary_result[min_man][max_man] = round(expense, 2)
                final_result.append(f"Your total cost is {round(expense, 2)}")
                break
            # 分帳完成(加判斷round是因為float計算誤差會導致錯誤)
            elif max_value + min_value == 0 or round(round(max_value + min_value, 4), 3) == 0:
                temporary_result[min_man][max_man] = round(-min_value, 2)
                final_result.append(f"{min_man} give {max_man} $ {round(-min_value, 2)}")
                break
            # 繼續分帳
            elif max_value != min_value:
                # 收到一個人還的錢後，還不夠要繼續收
                if max_value + min_value > 0:
                    temporary_result[min_man][max_man] = round(-min_value, 2)
                    print(f"{min_man} give {max_man} $ {round(-min_value, 2)}")
                    final_result.append(f"{min_man} give {max_man} $ {round(-min_value, 2)}")
                    self.result[max_man] = max_value + min_value
                    self.result[min_man] = 0
                    print("t_1")
                    print(f"{min_man}  {self.result[min_man]}")
                    print(f"{max_man}  {self.result[max_man]}")

                # 還一個人的錢後，還有欠別人的
                elif max_value + min_value < 0:
                    temporary_result[min_man][max_man] = round(max_value, 2)
                    print(temporary_result)
                    print(f"{min_man} give {max_man} $ {round(max_value, 2)}")
                    final_result.append(f"{min_man} give {max_man} $ {round(max_value, 2)}")
                    self.result[max_man] = 0
                    self.result[min_man] = max_value + min_value

                    print(f"{min_man}  {self.result[min_man]}")
                    print(f"{max_man}  {self.result[max_man]}")
                    print("t_2")

                else:
                    print("!!!!!!!!!!!!!!!!!!!!")
                    break
            else:
                print("????????????????????")
                break
        print(temporary_result)
        return temporary_result


@app.route('/')
def check_tour_name():
    all_title = [title.tour_title for title in db.session.execute(db.select(TourName)).scalars()]
    print(all_title)
    input_title = request.args.get('tour_name_submit')
    print(input_title)

    if input_title == "OK":
        # 檢查tour_name是否在table裡
        tour_title = request.args.get('tour_title')
        tour_base = db.session.execute(db.select(TourName).where(TourName.tour_title == tour_title)).scalar()
        print(tour_title)
        # 有在database裡
        if tour_base:
            print("Inside")
            print(tour_base.tour_title)
            all_member = tour_base.all_member
            print(all_member)
            return redirect(url_for('home', tour_title=tour_title))
        # 沒輸入任何字
        elif len(tour_title) == 0:
            er = 'Must input title.'
            print(er)
            return render_template("check_tour_name.html", all_title=all_title, er=er)
        # 沒有在database裡
        else:
            print("Create new")
            # new_title = TourName(
            #     tour_title = tour_title
            # )
            # db.session.add(new_title)
            # db.session.commit()
            return redirect(url_for('add_num', input_member=True, tour_title=tour_title))
    return render_template("check_tour_name.html", all_title=all_title)

@app.route('/num')
def add_num():
    tour_title = request.args.get('tour_title')
    # 有member資料
    if request.args.get('input_member') == "False":
        if request.args.get('member_submit') == "GO":
            print("OOOOOOOOOOOOOOO")
            # all_member = ""
            # member_num = int(request.args.get('member_num'))
            # print(member_num)
            # for i in range(member_num):
            #     all_member += request.args.get(f"member_{i + 1}") + ","
            # members = all_member[:-1]
            all_member = []
            member_num = int(request.args.get('member_num'))
            print(member_num)
            for i in range(member_num):
                all_member.append(request.args.get(f"member_{i + 1}"))

            if "" in all_member:
                empt_index = []
                for i in range(len(all_member)):
                    if all_member[i] == "":
                        empt_index.append(i)
                er = 'Must input name.'
                print(er)
                return render_template('member_num.html', input_member=True, member_num=member_num,
                                       tour_title=tour_title, all_member=all_member, empt_index=empt_index, er=er)

            else:
                members = str(all_member)
                print(request.args.get('tour_title'))

                new_title = TourName(
                    tour_title=tour_title,
                    all_member = members,
                    member_num = member_num
                )
                db.session.add(new_title)
                db.session.commit()

                # member_update = db.session.execute(db.select(TourName).where(TourName.tour_title ==
                #                                                              request.args.get('tour_title'))).scalar()
                # member_update.all_member = members
                # member_update.member_num = member_num
                # db.session.commit()
                print(members)
            # else:
            #     tour_title = request.args.get('tour_title')
            #     print(tour_title)
            #     print("GGGGGGGGGGGGGGGGG")
            #     members = db.session.execute(db.select(TourName).where(TourName.title ==
            #                                                            tour_title)).scalar().all_member
            #     print(members)
        return redirect(url_for('home', tour_title=tour_title))
    #     input_cost = CostInput()
    #     input_cost.who_pay.choices = []
    #     return render_template('member_num.html', form_cost=input_cost)
    # 沒有member資料
    elif request.args.get('input_member') == "True":
        print("EEEEEEEEEEEEEE")
        if request.method == "GET":
            print(request.args.get('member_submit'))
            print(request.args.get('member_num_submit'))
            if request.args.get('member_num_submit') == "OK" and request.args.get('member_submit') == None:
                print("YYYYYYYYYYYYY")
                member_num = request.args.get('member_num')
                if len(member_num) == 0:
                    er = 'Must input number.'
                    print(er)
                    return render_template('member_num.html', input_member_num=True, tour_title=tour_title, er=er)
                elif type(eval(member_num)) is not int:
                    er = 'Must input an integer.'
                    print(er)
                    return render_template('member_num.html', input_member_num=True, tour_title=tour_title, er=er)
                else:
                    return render_template('member_num.html', input_member=True, member_num=int(member_num),
                                           tour_title=tour_title)

            else:
                print("UUUUUUUUUUUUUUU")
        else:
            print("IIIIIIIIIIIIIIIIII")

        return render_template('member_num.html', input_member_num=True, tour_title=tour_title)
    else:
        print("XXXXXXXXXXXXXXXXXX")
    return render_template('member_num.html', tour_title=tour_title)

@app.route('/add_cost', methods=['GET', 'POST'])
def add_cost():
    tour_title = request.args.get('tour_title')
    timezone_tw = pytz.timezone('ROC')
    time_now = str(datetime.now(timezone_tw).date()) + "T" + str(datetime.now(timezone_tw).strftime("%H:%M"))
    print(time_now)
    tour_base = db.session.execute(db.select(TourName).where(TourName.tour_title == tour_title)).scalar()
    member_num = tour_base.member_num
    members = eval(tour_base.all_member)
    all_member = [""]
    for i in range(len(members)):
        all_member.append((members[i]))
    print(all_member)

    new_cost = CostInput()
    new_cost.who_pay.choices = all_member

    # if request.method == "POST":
    if new_cost.validate_on_submit():
        print("TTTTTTTTTTTTTT")
        if request.form["add_cost_submit"] == "Add":
            cost_item = new_cost.item.data
            who_pay = new_cost.who_pay.data
            money = new_cost.money.data
            apportion = []
            for member in members:
                # uses .get() to perform the lookup in the form dictionary.
                # If the key is present in the dictionary the value will be returned.
                # If the key is not in the dictionary the value None is returned.
                if request.form.get(member):
                    apportion.append(member)
            

            if apportion == []:
                new_cost.item.data = cost_item
                new_cost.who_pay.data = who_pay
                new_cost.money.data = money
                er = 'At least choose one.'
                print(er)
                return render_template('add_cost.html', form_new_cost=new_cost, tour_title=tour_title,
                                       all_member=members, member_num=member_num, er=er, time_now=time_now)
            else:
                insert_time = request.form.get("insert_time")
                print(insert_time)
                who_apportion = str(apportion)
                new_cost = Cost(
                    tour_title = tour_title,
                    item = cost_item,
                    all_member = tour_base.all_member,
                    who_pay = who_pay,
                    money = money,
                    who_apportion = who_apportion,
                    insert_time = insert_time,
                    update_time = insert_time
                )
                db.session.add(new_cost)
                db.session.commit()
                return redirect(url_for('home', tour_title=tour_title))

    else:

        return render_template('add_cost.html', form_new_cost=new_cost, tour_title=tour_title, all_member=members,
                               member_num=member_num, time_now=time_now)

@app.route("/home", methods=['GET', 'POST'])
def home():
    tour_title = request.args.get('tour_title')
    if tour_title:
        tour_base = db.session.execute(db.select(Cost).order_by(Cost.insert_time)).scalars().all()
        tour_base.reverse()
        data_base = []
        for data in tour_base:
            if data.tour_title == tour_title:
                data_base.append((data.id, data.item, data.money, data.insert_time))
        print(data_base)
        if request.method == "POST":
            print('111111111111111')
            if request.form.get('modify_item'):
                print('2222222222222222')
                item_id = request.form.get('modify_item')
                return redirect(url_for('modify_or_delete', item_id=item_id))
            else:
                print("QWQQWQWQWQQWQ")
        else:
            # return render_template('cost_list.html', tour_title=tour_title, data_base=data_base)

            return render_template('index.html', tour_title=tour_title, data_base=data_base)
    else:
        return redirect(url_for('check_tour_name'))

@app.route('/summary')
def summary():
    tour_title = request.args.get('tour_title')
    if tour_title:
        if db.session.execute(db.select(Cost).where(Cost.tour_title == tour_title)).scalar():
            all_member = eval(db.session.execute(db.select(Cost).where(Cost.tour_title ==
                                                                       tour_title)).scalar().all_member)
            results = Calculator(tour_title).summary()
            final_result = []
            for member1 in all_member:
                for member2 in all_member:
                    if member2 in results[member1].keys():
                        if member1 == member2:
                            final_result.append(f"Your total cost is $ {results[member1][member2]}")
                        else:
                            final_result.append(f"{member1} give {member2} $ {results[member1][member2]}")
            return render_template('summary.html', tour_title=tour_title, results=final_result)
        else:
            return render_template('summary.html', tour_title=tour_title, results=["For now, no cost in record."])
    else:
        return redirect(url_for('check_tour_name'))


@app.route('/cost_list', methods=["GET", "POST"])
def cost_list():
    tour_title = request.args.get('tour_title')
    tour_base = db.session.execute(db.select(Cost).order_by(Cost.insert_time)).scalars()
    data_base = []
    for data in tour_base:
        if data.tour_title == tour_title:
            data_base.append((data.id, data.item, data.money, data.update_time))
    print(data_base)
    if request.method == "POST":
        if request.form.get('cost_list_modify') == 'Modify':
            item_id = request.form['modify_item']
            return redirect(url_for('modify_item', item_id=item_id))
        else:
            print("QWQQWQWQWQQWQ")
    else:
        return render_template('cost_list.html', tour_title=tour_title, data_base=data_base)

@app.route('/modify_delete', methods=['GET', 'POST'])
def modify_or_delete():
    item_id = request.args.get('item_id')
    print(item_id)
    tour_base = db.session.execute(db.select(Cost).where(Cost.id == item_id)).scalar()
    insert_time = tour_base.insert_time
    members = eval(tour_base.all_member)
    modify_cost = CostInput()
    print('777777777777777777777777')
    if request.method == "POST":
        print("TTTTTTTTTTTTTT")
        if request.form.get("cost_item_modify") == "Modify":
            return redirect(url_for('modify_item', item_id=item_id))

        elif request.form.get("cost_item_delete") == "Delete":
            return redirect(url_for('delete_item', item_id=item_id))
        return redirect(url_for('cost_list', tour_title=tour_base.tour_title))

    else:
        all_member = [""]
        for member in members:
            all_member.append(member)
        modify_cost.who_pay.choices = all_member
        modify_cost.who_pay.data = tour_base.who_pay
        modify_cost.item.data = tour_base.item
        modify_cost.money.data = tour_base.money
        return render_template('modify_or_delete.html', item_id=item_id, tour_title=tour_base.tour_title,
                               form_modify_cost=modify_cost, all_member=members,
                               member_num=len(eval(tour_base.all_member)), who_apportion=eval(tour_base.who_apportion),
                               insert_time=insert_time)


@app.route('/modify_item', methods=['GET', 'POST'])
def modify_item():
    item_id = request.args.get('item_id')
    print(item_id)
    tour_base = db.session.execute(db.select(Cost).where(Cost.id == item_id)).scalar()
    tour_title = tour_base.tour_title

    members = eval(tour_base.all_member)
    member_num = len(members)
    all_member = [""]
    for i in range(len(members)):
        all_member.append((members[i]))
    print(all_member)

    modify_cost = CostInput()
    modify_cost.who_pay.choices = all_member

    cost_item = modify_cost.item.data
    who_pay = modify_cost.who_pay.data
    money = modify_cost.money.data

    apportion = []
    for member in eval(tour_base.all_member):
        # uses .get() to perform the lookup in the form dictionary.
        # If the key is present in the dictionary the value will be returned.
        # If the key is not in the dictionary the value None is returned.
        if request.form.get(member):
            apportion.append(member)

    # if request.method == "POST":
    if modify_cost.validate_on_submit() and apportion != []:
        print("66666666666666")
        if request.form.get("cost_item_modify") == "Update":
            who_apportion = str(apportion)
            tour_base.item = modify_cost.item.data
            tour_base.who_pay = modify_cost.who_pay.data
            tour_base.money = modify_cost.money.data
            tour_base.who_apportion = who_apportion
            tour_base.insert_time = request.form.get("insert_time")
            tour_base.update_time = str(datetime.now().date()) + "T" + str(datetime.now().strftime("%H:%M"))
            db.session.commit()
            return redirect(url_for('home', tour_title=tour_title))

    elif modify_cost.validate_on_submit() and apportion == []:
        insert_time = tour_base.insert_time
        modify_cost.item.data = cost_item
        modify_cost.who_pay.data = who_pay
        modify_cost.money.data = money
        er = 'At least choose one.'
        print(er)
        return render_template('modify_item.html',item_id=item_id, tour_title=tour_title, form_modify_cost=modify_cost,
                                       all_member=members, member_num=member_num, er=er, insert_time=insert_time)

    else:
        all_member = [""]
        for member in members:
            all_member.append(member)
        modify_cost.who_pay.choices = all_member
        modify_cost.who_pay.data = tour_base.who_pay
        modify_cost.item.data = tour_base.item
        modify_cost.money.data = tour_base.money
        insert_time = tour_base.insert_time
        return render_template('modify_item.html', item_id=item_id, tour_title=tour_title, form_modify_cost=modify_cost,
                               all_member=members, member_num=len(eval(tour_base.all_member)),
                               who_apportion=eval(tour_base.who_apportion), insert_time=insert_time)




@app.route('/delete')
def delete_item():
    item_id = request.args.get('item_id')
    tour_base = db.session.execute(db.select(Cost).where(Cost.id == item_id)).scalar()
    tour_title = tour_base.tour_title
    print('555555555555555555')
    db.session.delete(tour_base)
    db.session.commit()
    return redirect(url_for('home', tour_title=tour_title))


if __name__ == '__main__':
    app.run(debug=True)