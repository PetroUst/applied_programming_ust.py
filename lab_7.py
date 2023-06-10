import bcrypt as bcrypt
from sqlalchemy import *
from flask import *
from flask_marshmallow import Marshmallow
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from flask_swagger_ui import *
from main import *
from flask_httpauth import HTTPBasicAuth
from sqlalchemy import and_
from flask_cors import CORS
from copy import copy
import time
app = Flask(__name__)
CORS(app, origins='http://localhost:4200')
#SQLalchemy
# engine = create_engine("mysql+pymysql://root:1234@127.0.0.1:3306/pp", echo=True,pool_size=200,max_overflow=400)
engine = create_engine("mysql+pymysql://root:1234@127.0.0.1:3306/pp")
Session = sessionmaker(bind=engine)
s = Session()

#Marshmallow
ma = Marshmallow(app)

#SwaggerUrL
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGER_BLUEPRINT = get_swaggerui_blueprint(SWAGGER_URL, API_URL,
    config={'app_name': 'Event Tickets API'})
app.register_blueprint(SWAGGER_BLUEPRINT, url_prefix=SWAGGER_URL)

auth = HTTPBasicAuth()

# @auth.verify_password
# def verify_password(username, password):
#     try:
#         user = s.query(User).filter(User.Username == username).one()
#         s.rollback()
#         if not user:
#             return make_response(404)
#         print(user)
#         if bcrypt.checkpw(password.encode("utf-8"), user.Password.encode("utf-8")):
#             print("nice")
#             return username
#     except:
#         return None

@auth.verify_password
def verify_password(username, password):
    try:
        ses = Session()
        # time.sleep(1)
        user = ses.query(User).filter(User.Username == username).one()
        if not user:
            return None

        if bcrypt.checkpw(password.encode("utf-8"), user.Password.encode("utf-8")):
            ses.close()
            return username
    except:
        return None

@auth.get_user_roles
def get_user_roles(username):
    user = s.query(User).filter(User.Username == username).first()
    return user.Role


@app.errorhandler(401)
def handle_401_error(_error):
    return make_response(jsonify({'error': 'Unauthorised'}), 401)

@app.errorhandler(403)
def handle_403_error(_error):
    return make_response(jsonify({'error': 'Forbidden'}), 403)

@app.errorhandler(404)
def handle_404_error(_error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(405)
def handle_401_error(_error):
    return make_response(jsonify({'error': 'Already exists'}), 401)



class TicketSchema(ma.Schema):
    class Meta:
        fields = ('TicketId', 'EventId', 'Price', 'Line', 'Place', 'IsBooked', 'IsPaid')

Ticket_schema = TicketSchema(many=False)
Tickets_schema = TicketSchema(many=True)

class UserSchema(ma.Schema):
    class Meta:
        fields = ('Username', 'Name', 'Surname', 'Email')
User_schema = TicketSchema(many=False)
Users_schema = TicketSchema(many=True)

# Max-tickets -- MaxTickets
class EventSchema(ma.Schema):
    class Meta:
        fields = ('EventId', 'EventName', 'Time', 'City', 'Location', 'Price', 'MaxTickets')

Event_schema = EventSchema(many=False)
Events_schema = EventSchema(many=True)


# 11get ticket by id
@app.route("/Ticket/<int:TicketId>", methods=["GET"])
def getTicketById(TicketId):
    ticket = s.query(Ticket).filter(Ticket.TicketId == TicketId).one()
    return Ticket_schema.jsonify(ticket)



# 11get all tickets on event
@app.route("/Ticket/get-by-event-id/<int:EventId>", methods=["GET"])
def getTicketsByEventId(EventId):
    tickets = s.query(Ticket).filter(Ticket.EventId == EventId).all()
    return Tickets_schema.jsonify(tickets)



# 11add ticket
@app.route("/Ticket", methods=["POST"])
@auth.login_required(role=['SuperUser'])
def addTicket():
    try:
        EventId = request.json['EventId']
        Price = request.json['Price']
        Line = request.json['Line']
        Place = request.json['Place']
        IsBooked = 0
        IsPaid = 0
        event = s.query(Event).filter(Event.EventId == EventId).one()
        count = s.query(Ticket).filter(Ticket.EventId == EventId).count()
        if count+1>event.MaxTickets:
            return Response(status=420, responce="You can't add tickets more")
        print("count = ", count,event.MaxTickets)
        Username = event.Username
        current = auth.username()
        if current != Username:
            return Response(status=403, response='Access denied')

        new_ticket = Ticket(EventId=EventId,  IsBooked=IsBooked,
                            IsPaid=IsPaid, Price=Price, Line=Line,
                            Place=Place)

        s.add(new_ticket)
        s.commit()
        return Ticket_schema.jsonify(new_ticket)

    except Exception as e:
        return jsonify({"Error": "Invalid Request, please try again."})


# 11delete tickets by event id
@app.route("/Ticket/<int:EventId>", methods=["DELETE"])
@auth.login_required(role=['SuperUser'])
def deleteTicketsByEventId(EventId):
    event = s.query(Event).filter(Event.EventId == EventId).one()
    Username = event.Username
    current = auth.username()
    if current != Username:
        return Response(status=403, response='Access denied')
    tickets = s.query(Ticket).filter(Ticket.EventId == EventId).all()

    for ticket in tickets:
        s.delete(ticket)

    s.commit()
    return jsonify({"Success": "Tickets deleted."})


# 11event add
@app.route("/Event", methods=["POST"])
@auth.login_required(role=['SuperUser'])
def addEvent():
    try:
        EventName = request.json['EventName']
        Time = request.json['Time']
        City = request.json['City']
        Location = request.json['Location']
        MaxTickets = request.json['MaxTickets']
        Price = request.json['Price']
        input_time_format = '%Y-%m-%dT%H:%M'
        output_time_format = '%d-%m-%Y %H:%M'
        parsed_datetime = datetime.strptime(Time, input_time_format)
        formatted_datetime = parsed_datetime.strftime(output_time_format)
        new_event = Event(EventName=EventName,
                        Time=formatted_datetime, City=City,
                        Location=Location, MaxTickets=MaxTickets, Username=auth.username(), Price=Price)

        s.add(new_event)
        s.commit()
        return Event_schema.jsonify(new_event)

    except Exception as e:
        return jsonify({"Error": "Invalid Request, please try again."})


@app.route("/User/login", methods=["POST"])
def login():
    username = request.json['Username']
    password = request.json['Password']
    try:
        user = s.query(User).filter(User.Username == username).one()
        if bcrypt.checkpw(password.encode("utf-8"), user.Password.encode("utf-8")):
            return jsonify({"Success": "You are logged in."})
        return jsonify({"Error": "Invalid username or password."})
    except Exception as e:
        return jsonify({"Error": "Invalid username or password."})

# 11delete event by id

@app.route("/User/get-user", methods=["GET"])
@auth.login_required()
def getUser():
    username = auth.username()
    user = s.query(User).filter(User.Username == username).one()
    # s.rollback()
    if user:
        userCopy = copy(user)
        userCopy.Password = ""
        return User_schema.jsonify(user)
    return Response(status=404, response='User not found, log in please')

@app.route("/Event/<int:EventId>", methods=["DELETE"])
@auth.login_required(role=['SuperUser'])
def deleteEventById(EventId):
    event = s.query(Event).filter(Event.EventId == EventId).one()
    Username = event.Username
    current = auth.username()
    if current != Username:
        return Response(status=403, response='Access denied')
    s.delete(event)
    s.commit()
    return jsonify({"Success": "Event deleted."})


# 11update event
@app.route("/Event/<int:EventId>", methods=["PUT"])
@auth.login_required(role=['SuperUser'])
def updateEventById(EventId):
    event = s.query(Event).filter(Event.EventId == EventId).one()
    Username = event.Username
    current = auth.username()
    if current != Username:
        return Response(status=405, response='Access denied')
    try:

        EventName = request.json['EventName']
        Time = request.json['Time']
        City = request.json['City']
        Location = request.json['Location']
        MaxTickets = request.json['MaxTickets']


        event.EventName = EventName
        event.Time = Time
        event.City = City
        event.Location = Location
        event.MaxTickets = MaxTickets

        s.commit()
    except Exception as e:
        return jsonify({"Error": "Invalid request, please try again."})

    return Event_schema.jsonify(event)


# USERS


class UserSchema(ma.Schema):
    class Meta:
        fields = ('Username', 'Name', 'Surname', 'Email', 'Password','Role')


User_schema = UserSchema(many=False)
Users_schema = UserSchema(many=True)


# 11get all user`s tickets
@app.route("/Ticket/get-by-userid/<string:Username>", methods=["GET"])
# role=['User']
@auth.login_required(role=['User'])
def getUsersTickets(Username):
    current = auth.username()
    if current != Username:
        print(current)
        print('\n\n\n')
        return Response(status=403, response='Access denied')
    tickets = s.query(Ticket).filter(Ticket.Username == Username).all()

    return Tickets_schema.jsonify(tickets)


# 11add user
@app.route("/User", methods=["POST"])
def addUser():
    try:
        Username = request.json['Username']
        # exUser = s.query(User).filter(User.Username == Username).one()
        Name = request.json['Name']
        Surname = request.json['Surname']
        Email = request.json['Email']
        Password = request.json['Password']
        Password = bcrypt.hashpw(Password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        new_user = User(Username=Username, Name=Name, Surname=Surname,
                        Email=Email, Password=Password,Role="User")
        s.add(new_user)
        s.commit()
        return User_schema.jsonify(new_user)


    except Exception as ex:
        s.rollback()
        return Response(status=405, response='User with such username or email already exists')


    except Exception as e:
        s.rollback()
        return Response(status=500, response='An error occurred during the transaction')


# @app.route("/SuperUser", methods=["POST"])
# def addSuperUser():
#     try:
#         Username = request.json['Username']
#         Name = request.json['Name']
#         Surname = request.json['Surname']
#         Email = request.json['Email']
#         Password = request.json['Password']
#         Password = bcrypt.hashpw(Password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
#         new_user = User(Username=Username, Name=Name, Surname=Surname,
#                         Email=Email, Password=Password,Role="SuperUser")
#
#         s.add(new_user)
#         # s.rollback()
#         s.commit()
#         return User_schema.jsonify(new_user)
#
#     except Exception as e:
#         return Response(status=405, response='User with such username or email already exists')

@app.route("/Event/get-by-userid", methods=["GET"])
@auth.login_required(role=['SuperUser'])
def getUsersEvents():
    current = auth.username()
    sesM = sessionmaker(bind=engine)
    ses = sesM()
    events = ses.query(Event).filter(Event.Username == current).all()
    ses.close()
    return Events_schema.jsonify(events)


@app.route("/SuperUser", methods=["POST"])
def addSuperUser():
    try:
        Username = request.json['Username']
        Name = request.json['Name']
        Surname = request.json['Surname']
        Email = request.json['Email']
        Password = request.json['Password']
        Password = bcrypt.hashpw(Password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        new_user = User(Username=Username, Name=Name, Surname=Surname,
                        Email=Email, Password=Password, Role="SuperUser")

        s.add(new_user)
        s.commit()
        return User_schema.jsonify(new_user)

    except Exception as ex:
        s.rollback()
        return Response(status=405, response='User with such username or email already exists')

    except Exception as e:
        s.rollback()
        return Response(status=500, response='An error occurred during the transaction')



# 11book Ticket
@app.route("/User/booking/<int:TicketId>", methods=["PUT"])
@auth.login_required(role=['User'])
def BookTicketById(TicketId):

    try:
        current = auth.username()
        ticket = s.query(Ticket).filter(Ticket.TicketId == TicketId).one()
        if ticket.Username is not None:
            return Response(status=403, response='The ticket is already booked')
        else:
            ticket.Username = current
            ticket.IsBooked = 1
            s.commit()
    except Exception as e:
        return jsonify({"Error": "Choose another ticket."})
    return Ticket_schema.jsonify(ticket)


# 11buy ticket
@app.route("/User/buying/<int:TicketId>", methods=["PUT"])
@auth.login_required(role=['User'])
def BuyTicketById(TicketId):

    try:
        current = auth.username()
        ticket = s.query(Ticket).filter(Ticket.TicketId == TicketId).one()
        if (ticket.Username != current and ticket.Username is not None) or ticket.IsPaid == 1:
            return Response(status=403, response='The ticket is already booked or bought by another person')
        else:
            ticket.Username = current
            ticket.IsPaid = 1
            s.commit()
    except Exception as e:
        return jsonify({"Error": "Choose another ticket."})
    return Ticket_schema.jsonify(ticket)

@app.route("/User/cancel/<int:TicketId>", methods=["PUT"])
@auth.login_required(role=['User'])
def CancelBookingByTicketById(TicketId):

    try:
        current = auth.username()
        ticket = s.query(Ticket).filter(Ticket.TicketId == TicketId).one()
        if ticket.IsPaid == 1:
            return Response(status=201, response='Already purchased')
        if ticket.Username == current:
            ticket.Username = None
            ticket.IsBooked = 0
            s.commit()
        else:
            return Response(status=403, response='Access denied')
    except Exception as e:
        return jsonify({"Error": "Choose another ticket."})
    return Ticket_schema.jsonify(ticket)


@app.route("/Event/get-all-events", methods=["GET"])
def getEvents():
    events = s.query(Event).all()
    return Events_schema.jsonify(events)

if __name__ == "__main__" : app.run()