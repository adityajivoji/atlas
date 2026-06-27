from fastapi import APIRouter, Request
import helpers
from services import UserService
import utils

user_route = APIRouter()


@user_route.get("/get/{id:str}")
async def get_user_with_user_id(id: str):
    try:
        user_helper = await UserService.get_user_with_user_id(id)
        return utils.MiscUtils.api_response(
            message="User fetched successfully",
            data=user_helper.to_dict()
        )
    except Exception as e:
        return utils.MiscUtils.error_response(e)
    

@user_route.post("/add")
async def create_user(request: Request):
    try:
        request_body = await utils.MiscUtils.get_request_body_from_request(request)
        name = request_body.get("user")
        user_name = request_body.get("user_name")
        password = request_body.get("password")
        email = request_body.get("email")
        meta = request_body.get("meta", {})
        
        assert name and user_name and password and email, "Invalid Request Body"
        user_helper = await UserService.create_user(
            name=name,
            user_name=user_name,
            password=password,
            email=email,
            meta=meta
        )
        return utils.MiscUtils.api_response(
            message="User created successfully",
            data=user_helper.to_dict()
        )
    except Exception as e:
        return utils.MiscUtils.error_response(e)
    
    
@user_route.post("/update/{id:str}")
async def update_user(request: Request, id:str):
    try:
        request_body = await utils.MiscUtils.get_request_body_from_request(request)
        name = request_body.get("user")
        user_name = request_body.get("user_name")
        password = request_body.get("password")
        email = request_body.get("email")
        meta = request_body.get("meta", {})
        
        user_helper = await UserService.update_user(
            id=id,
            name=name,
            user_name=user_name,
            password=password,
            email=email,
            meta=meta
        )
        return utils.MiscUtils.api_response(
            message="User created successfully",
            data=user_helper.to_dict()
        )
    except Exception as e:
        return utils.MiscUtils.error_response(e)
    
@user_route.delete("/delete/{id:str}")
async def delete(request: Request, id: str):
    try:
        user_helper = await UserService.delete(
            id=id
        )
        return utils.MiscUtils.api_response(
            message="User created successfully",
            data=user_helper.to_dict()
        )
    except Exception as e:
        return utils.MiscUtils.error_response(e)
    

@user_route.get("/all")
async def get_all(request: Request):
    try:
        request_body = await utils.MiscUtils.get_request_body_from_request(request)
        user_helpers = await UserService.get_all_by_filter(
            filter=request_body
        )
        return utils.MiscUtils.api_response(
            message="User created successfully",
            data=[user_helper.to_dict() for user_helper in user_helpers]
        )
    except Exception as e:
        return utils.MiscUtils.error_response(e)
    
    
@user_route.get("/one")
async def get_one_by_filter(request: Request):
    try:
        request_body = await utils.MiscUtils.get_request_body_from_request(request)
        user_helper = await UserService.get_one_by_filter(
            filter=request_body
        )
        return utils.MiscUtils.api_response(
            message="User created successfully",
            data=user_helper.to_dict() if user_helper else None
        )
    except Exception as e:
        return utils.MiscUtils.error_response(e)
    
    

