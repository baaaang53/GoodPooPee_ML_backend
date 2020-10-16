from app.models.pet import Pet
from app.models.user import User
from app.models.ppcam_serial_nums import PpcamSerialNums
from flask import request
from flask_restful import Resource
from app.models.ppcam import Ppcam, PpcamSchema
from app.utils.decorators import confirm_account
from app import db
import datetime

# make instances of schemas
ppcam_schema = PpcamSchema()
ppcams_schema = PpcamSchema(many=True)

class PpcamRegisterApi(Resource):
    def post(self):
        '''
        When first time to register ppcam profile to server
        Post ppcam profile to table
        :url: {{baseUrl}}/ppcam/register
        :path: None
        :body: serial_num: str, ip_address: str, user_email: str
        '''
        from sqlalchemy.exc import IntegrityError

        # check serial nums is valid
        exist_serial_record = PpcamSerialNums.query.filter_by(serial_num = request.json['serial_num']).first()
        if(exist_serial_record is None):
            return {
                "msg" : "Serial number is invalid. check again."
            }, 404
        # check user email is valid
        exist_user_record = User.query.filter_by(email = request.json['user_email']).first()
        if(exist_user_record is None):
            return {
                "msg" : "User email is invalid. check again."
            }, 404
        # create new ppcam profile
        new_ppcam = Ppcam(
            serial_num = request.json['serial_num'],
            ip_address = request.json['ip_address'],
            user_id = exist_user_record.id,
        )
        db.session.add(new_ppcam)
        # update serial nums table
        exist_serial_record.sold = 1
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return {
                "msg" : "Fail to add new ppcam(IntegrityError)."
            }, 409
        return ppcam_schema.dump(new_ppcam), 200

class PpcamLoginApi(Resource):
    '''
    To issue device auth token
    '''
    def post(self):
        # check that ppcam profile exist
        login_device = Ppcam.query.filter_by(serial_num = request.json['serial_num']).first()
        if login_device is None:
            return {
                "msg" : "Serial number is invalid"
            }, 404
        # check that ppcam registered(sold == 1)
        if login_device.sold != 1:
            device_auth_token = login_device.encode_auth_token(login_device.id)
            user_id = login_device.user_id
            users_pet = Pet.query.filter_by(user_id = user_id).first()
            users_pet_id = 'null'
            if(users_pet is not None):
                users_pet_id = users_pet.id
            return {
                'device_access_token' : device_auth_token.decode('UTF-8'),
                'ppcam_id' : login_device.id,
                'user_id' : user_id,
                'pet_id' : users_pet_id
            }, 200
        else:
            return {
                "msg" : "This device is not registered"
            }, 403

class PpcamApi(Resource):
    @confirm_account
    def get(self, ppcam_id):
        selected_ppcam = Ppcam.query.filter_by(id = ppcam_id).first()
        if(selected_ppcam is None):
            return {
                "msg" : "Ppcam not found"
            }, 404
        return ppcam_schema.dump(selected_ppcam), 200

    @confirm_account
    def put(self, ppcam_id):
        from sqlalchemy.exc import IntegrityError
        updated_ppcam = Ppcam.query.filter_by(id = ppcam_id).first()
        if(updated_ppcam is None):
            return {
                "msg" : "Ppcam not found"
            }, 404
        try:
            updated_ppcam.serial_num = request.json['serial_num']
            updated_ppcam.ip_address = request.json['ip_address']
            updated_ppcam.last_modified_date = datetime.datetime.utcnow()
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return {
                "msg" : 'IntegrityError on updating ppcam'
            }, 409
        return ppcam_schema.dump(updated_ppcam), 200

    @confirm_account
    def delete(self, ppcam_id):
        from sqlalchemy.exc import IntegrityError
        deleted_ppcam = Ppcam.query.filter_by(id = ppcam_id).first()
        if(deleted_ppcam is None):
            return {
                "msg" : "Ppcam not found"
            }, 404
        try:
            db.session.delete(deleted_ppcam)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return {
                "msg" : "IntegrityError on that ppcam, maybe pad of ppcam still exists."
            }, 409
        return {
            "msg" : "Successfully deleted that ppcam"
        }, 200
