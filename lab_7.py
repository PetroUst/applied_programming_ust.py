from sqlalchemy import *
from flask import *
from flask_marshmallow import Marshmallow
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from flask_swagger_ui import *
from main import *
from flask_bcrypt import Bcrypt
from flask_httpauth import HTTPBasicAuth
from sqlalchemy import and_
app = Flask(__name__)

#SQLalchemy
engine = create_engine("mysql+pymysql://root:12345678@127.0.0.1:3306/pp", echo=True)
session = sessionmaker(bind=engine)
s = session()

#Marshmallow
ma = Marshmallow(app)

#SwaggerUrL
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGER_BLUEPRINT = get_swaggerui_blueprint(SWAGGER_URL, API_URL,
    config={'app_name': 'Event Tickets API'})
app.register_blueprint(SWAGGER_BLUEPRINT, url_prefix=SWAGGER_URL)

auth = HTTPBasicAuth()

bcrypt = Bcrypt()
@auth.verify_password
def verify_password(username, password):
    try:
        user = s.query(User).filter(User.Username == username).one()
        if user and bcrypt.check_password_hash(user.Password, password):
            return username
    except:
        return Response(status=500)

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

# @app.errorhandler(404)
# def handle_404_error(_error):
#     return make_response(jsonify({'error': 'Not found'}), 404)



class TicketSchema(ma.Schema):
    class Meta:
        fields = ('TicketId', 'EventId', 'Price', 'Line', 'Place', 'IsBooked', 'IsPaid')


Ticket_schema = TicketSchema(many=False)
Tickets_schema = TicketSchema(many=True)


class EventSchema(ma.Schema):
    class Meta:
        fields = ('EventId', 'EventName', 'Time', 'City', 'Location', 'Max-tickets')


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

        new_event = Event(EventName=EventName,
                        Time=datetime.strptime(Time, "%Y-%m-%d %H:%M"), City=City,
                        Location=Location, MaxTickets=MaxTickets, Username=auth.username())

        s.add(new_event)
        s.commit()
        return Event_schema.jsonify(new_event)

    except Exception as e:
        return jsonify({"Error": "Invalid Request, please try again."})


# 11delete event by id
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
@auth.login_required(role=['User'])
def getUsersTickets(Username):
    current = auth.username()
    if current != Username:
        return Response(status=403, response='Access denied')
    tickets = s.query(Ticket).filter(Ticket.Username == Username).all()

    return Tickets_schema.jsonify(tickets)


# 11add user
@app.route("/User", methods=["POST"])
def addUser():
    try:
        Username = request.json['Username']
        Name = request.json['Name']
        Surname = request.json['Surname']
        Email = request.json['Email']
        Password = request.json['Password']
        Password = bcrypt.generate_password_hash(Password)

        new_user = User(Username=Username, Name=Name, Surname=Surname,
                        Email=Email, Password=Password,Role="User")

        s.add(new_user)
        s.commit()
        return User_schema.jsonify(new_user)

    except Exception as e:
        return jsonify({"Error": "Invalid Request, please try again."})


@app.route("/SuperUser", methods=["POST"])
def addSuperUser():
    try:
        Username = request.json['Username']
        Name = request.json['Name']
        Surname = request.json['Surname']
        Email = request.json['Email']
        Password = request.json['Password']
        # Password = bcrypt.hashpw(Password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        new_user = User(Username=Username, Name=Name, Surname=Surname,
                        Email=Email, Password=Password,Role="SuperUser")

        s.add(new_user)
        s.commit()
        return User_schema.jsonify(new_user)

    except Exception as e:
        return jsonify({"Error": "Invalid Request, please try again."})




# 11book Ticket
@app.route("/User/booking", methods=["PUT"])
@auth.login_required(role=['User'])
def BookTicketById():

    try:

        TicketId = request.json['TicketId']
        Username = request.json['Username']
        IsBooked = request.json['IsBooked']
        current = auth.username()
        if current != Username:
            return Response(status=403, response='Access denied')
        ticket = s.query(Ticket).filter(Ticket.TicketId == TicketId).one()

        if ticket.IsPaid:
            return handle_403_error(1)

        if ticket.IsBooked:
            if ticket.Username != Username:
                return handle_403_error(1)

            if IsBooked == 0:
                ticket.Username = None

            ticket.IsBooked = IsBooked


        s.commit()
    except Exception as e:
        return jsonify({"Error": "Invalid request, please try again."})
    return Ticket_schema.jsonify(ticket)


# 11buy ticket
@app.route("/User/buying", methods=["PUT"])
@auth.login_required(role=['User'])
def BuyTicketById():

    try:
        TicketId = request.json['TicketId']
        Username = request.json['Username']
        current = auth.username()
        if current != Username:
            return Response(status=403, response='Access denied')
        ticket = s.query(Ticket).filter(Ticket.TicketId == TicketId).one()

        # if ticket.IsPaid:
        #     return handle_403_error(1)
        #
        # if ticket.IsBooked:
        #     if ticket.Username != Username:
        #         return handle_403_error(1)

        ticket.IsPaid = 1
        ticket.Username = Username

        s.commit()
    except Exception as e:
        return jsonify({"Error": "Invalid request, please try again."})
    return Ticket_schema.jsonify(ticket)

if __name__ == "__main__" : app.run()