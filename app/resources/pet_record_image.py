from flask import request, Response
from flask_restful import Resource
from app.models.pet_record import PetRecord, PetRecordSchema, RecordQuerySchema
from app.utils.s3 import get_object
from app.utils.decorators import confirm_account

# make instances of schemas
pet_record_schema = PetRecordSchema()
record_query_schema = RecordQuerySchema()

class PetRecordImageApi(Resource):
    @confirm_account
    def get(self, pet_id):
        # validate query string by ma
        errors = record_query_schema.validate(request.args)
        if errors:
            return {
                "status" : "fail",
                "msg" : "error in put method - query schema validation"
            }, 400
        # get timestamp in query string
        last_timestamp = request.args.get("timestamp")
        # querying record
        selected_record = PetRecord.query.filter_by(timestamp = last_timestamp, pet_id = pet_id).first()
        # get image_uuid by timestamp of record
        image_uuid = selected_record.image_uuid
        file_data = get_object(image_uuid)
        if file_data:
            return Response(
                file_data,
                mimetype='image/png'
            )
        else:
            return {
                "status" : "Fail",
                "msg" : "Fail to get object from S3 bucket."
            }, 500