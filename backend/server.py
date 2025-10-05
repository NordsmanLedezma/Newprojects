from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import jwt
import hashlib
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO
from fastapi.responses import StreamingResponse
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Sistema de Registro de Bonos de Panamá")
api_router = APIRouter(prefix="/api")

# Pydantic Models
class UserBase(BaseModel):
    username: str
    email: str
    brokerage_name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdminCreate(BaseModel):
    username: str
    password: str
    email: str

class Admin(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SecurityBase(BaseModel):
    isin_code: Optional[str] = None
    latinex_code: Optional[str] = None
    security_description: str
    coupon: str
    issue_date: str
    maturity_date: str
    
    @validator('isin_code', 'latinex_code')
    def at_least_one_code(cls, v, values):
        if not v and not values.get('isin_code') and not values.get('latinex_code'):
            raise ValueError('Al menos un código ISIN o Latinex es requerido')
        return v

class SecurityCreate(SecurityBase):
    pass

class Security(SecurityBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HoldingBase(BaseModel):
    filing_date: str
    isin_or_latinex_code: str
    holder_name: str
    holder_id: str
    legal_representative: Optional[str] = None
    amount_held: float
    address: str
    phone: str
    email: str

class HoldingCreate(HoldingBase):
    pass

class Holding(HoldingBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    security_info: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: str
    user_info: Dict[str, Any]

# Helper functions
def verify_password(plain_password, hashed_password):
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict):
    to_encode = data.copy()
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

# Authentication endpoints
@api_router.post("/auth/login", response_model=Token)
async def login(login_data: LoginRequest):
    # Check admin first
    admin = await db.admins.find_one({"username": login_data.username})
    if admin and verify_password(login_data.password, admin["hashed_password"]):
        token_data = {"sub": admin["username"], "user_type": "admin", "user_id": admin["id"]}
        token = create_access_token(token_data)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_type": "admin",
            "user_info": {"username": admin["username"], "email": admin["email"]}
        }
    
    # Check user
    user = await db.users.find_one({"username": login_data.username})
    if user and verify_password(login_data.password, user["hashed_password"]):
        if not user.get("is_active", True):
            raise HTTPException(status_code=400, detail="Usuario inactivo")
        token_data = {"sub": user["username"], "user_type": "user", "user_id": user["id"]}
        token = create_access_token(token_data)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_type": "user",
            "user_info": {
                "username": user["username"], 
                "email": user["email"],
                "brokerage_name": user["brokerage_name"]
            }
        }
    
    raise HTTPException(status_code=400, detail="Credenciales incorrectas")

# Admin endpoints
@api_router.post("/admin/create-admin", response_model=Admin)
async def create_admin(admin_data: AdminCreate, token_payload: dict = Depends(verify_token)):
    if token_payload.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Check if admin exists
    existing = await db.admins.find_one({"username": admin_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="El administrador ya existe")
    
    hashed_password = get_password_hash(admin_data.password)
    admin_dict = admin_data.dict()
    del admin_dict["password"]
    admin_obj = Admin(**admin_dict)
    admin_dict = admin_obj.dict()
    admin_dict["hashed_password"] = hashed_password
    admin_dict = prepare_for_mongo(admin_dict)
    
    await db.admins.insert_one(admin_dict)
    return admin_obj

@api_router.get("/admin/admins", response_model=List[Admin])
async def get_admins(token_payload: dict = Depends(verify_token)):
    if token_payload.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    admins = await db.admins.find().to_list(1000)
    return [Admin(**admin) for admin in admins]

@api_router.post("/admin/users", response_model=User)
async def create_user(user_data: UserCreate, token_payload: dict = Depends(verify_token)):
    if token_payload.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Check if user exists
    existing = await db.users.find_one({"username": user_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    del user_dict["password"]
    user_obj = User(**user_dict)
    user_dict = user_obj.dict()
    user_dict["hashed_password"] = hashed_password
    user_dict = prepare_for_mongo(user_dict)
    
    await db.users.insert_one(user_dict)
    return user_obj

@api_router.get("/admin/users", response_model=List[User])
async def get_users(token_payload: dict = Depends(verify_token)):
    if token_payload.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.put("/admin/users/{user_id}/toggle")
async def toggle_user_status(user_id: str, token_payload: dict = Depends(verify_token)):
    if token_payload.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    new_status = not user.get("is_active", True)
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": new_status}})
    return {"message": f"Usuario {'activado' if new_status else 'desactivado'}"}

# Securities (ISIN/Latinex) endpoints
@api_router.post("/admin/securities", response_model=Security)
async def create_security(security_data: SecurityCreate, token_payload: dict = Depends(verify_token)):
    if token_payload.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Check for duplicates
    query = {}
    if security_data.isin_code:
        query["isin_code"] = security_data.isin_code
    if security_data.latinex_code:
        if query:
            query = {"$or": [query, {"latinex_code": security_data.latinex_code}]}
        else:
            query["latinex_code"] = security_data.latinex_code
    
    existing = await db.securities.find_one(query)
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un valor con ese código")
    
    security_obj = Security(**security_data.dict())
    security_dict = prepare_for_mongo(security_obj.dict())
    await db.securities.insert_one(security_dict)
    return security_obj

@api_router.get("/admin/securities", response_model=List[Security])
async def get_securities(token_payload: dict = Depends(verify_token)):
    if token_payload.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    securities = await db.securities.find().to_list(1000)
    return [Security(**security) for security in securities]

@api_router.get("/securities/search/{code}")
async def search_security(code: str, token_payload: dict = Depends(verify_token)):
    """Search security by ISIN or Latinex code"""
    query = {"$or": [{"isin_code": code}, {"latinex_code": code}]}
    security = await db.securities.find_one(query)
    if not security:
        raise HTTPException(status_code=404, detail="Valor no encontrado")
    return Security(**security)

# Holdings endpoints
@api_router.post("/holdings", response_model=Holding)
async def create_holding(holding_data: HoldingCreate, token_payload: dict = Depends(verify_token)):
    if token_payload.get("user_type") != "user":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Get security info
    query = {"$or": [
        {"isin_code": holding_data.isin_or_latinex_code}, 
        {"latinex_code": holding_data.isin_or_latinex_code}
    ]}
    security = await db.securities.find_one(query)
    
    holding_dict = holding_data.dict()
    holding_dict["user_id"] = token_payload["user_id"]
    if security:
        holding_dict["security_info"] = {
            "isin_code": security.get("isin_code"),
            "latinex_code": security.get("latinex_code"),
            "security_description": security["security_description"],
            "coupon": security["coupon"],
            "maturity_date": security["maturity_date"]
        }
    
    holding_obj = Holding(**holding_dict)
    holding_dict = prepare_for_mongo(holding_obj.dict())
    await db.holdings.insert_one(holding_dict)
    
    # Update master holdings
    await update_master_holdings()
    
    return holding_obj

@api_router.get("/holdings", response_model=List[Holding])
async def get_user_holdings(token_payload: dict = Depends(verify_token)):
    if token_payload.get("user_type") != "user":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    holdings = await db.holdings.find({"user_id": token_payload["user_id"]}).to_list(1000)
    return [Holding(**holding) for holding in holdings]

@api_router.get("/admin/holdings", response_model=List[Holding])
async def get_all_holdings(token_payload: dict = Depends(verify_token)):
    if token_payload.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    holdings = await db.holdings.find().to_list(1000)
    return [Holding(**holding) for holding in holdings]

async def update_master_holdings():
    """Update master holdings collection with consolidated data"""
    # Clear existing master holdings
    await db.master_holdings.delete_many({})
    
    # Aggregate holdings by filing_date, security, and holder
    pipeline = [
        {
            "$group": {
                "_id": {
                    "filing_date": "$filing_date",
                    "isin_or_latinex_code": "$isin_or_latinex_code",
                    "holder_name": "$holder_name",
                    "holder_id": "$holder_id"
                },
                "total_amount": {"$sum": "$amount_held"},
                "holdings": {"$push": "$$ROOT"}
            }
        },
        {
            "$sort": {
                "_id.filing_date": 1,
                "_id.isin_or_latinex_code": 1,
                "_id.holder_name": 1
            }
        }
    ]
    
    aggregated = await db.holdings.aggregate(pipeline).to_list(1000)
    
    master_holdings = []
    for item in aggregated:
        master_holding = {
            "id": str(uuid.uuid4()),
            "filing_date": item["_id"]["filing_date"],
            "isin_or_latinex_code": item["_id"]["isin_or_latinex_code"],
            "holder_name": item["_id"]["holder_name"],
            "holder_id": item["_id"]["holder_id"],
            "total_amount": item["total_amount"],
            "holdings_count": len(item["holdings"]),
            "source_holdings": item["holdings"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        master_holdings.append(master_holding)
    
    if master_holdings:
        await db.master_holdings.insert_many(master_holdings)

@api_router.get("/admin/export/excel")
async def export_to_excel(token_payload: dict = Depends(verify_token)):
    if token_payload.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Create workbook
    wb = openpyxl.Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Style definitions
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    center_alignment = Alignment(horizontal="center", vertical="center")
    
    # Sheet 1: Securities (ISIN Master)
    ws1 = wb.create_sheet("Valores_ISIN")
    securities_headers = ["Código ISIN", "Código Latinex", "Descripción del Valor", 
                         "Cupón", "Fecha de Emisión", "Fecha de Vencimiento"]
    ws1.append(securities_headers)
    
    for cell in ws1[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
    
    securities = await db.securities.find().to_list(1000)
    for security in securities:
        ws1.append([
            security.get("isin_code", ""),
            security.get("latinex_code", ""),
            security["security_description"],
            security["coupon"],
            security["issue_date"],
            security["maturity_date"]
        ])
    
    # Sheet 2: Individual Holdings
    ws2 = wb.create_sheet("Tenencias_Individuales")
    holdings_headers = ["Fecha de Presentación", "Código ISIN/Latinex", "Nombre del Tenedor", 
                       "ID del Tenedor", "Representante Legal", "Cantidad Tenida", 
                       "Dirección", "Teléfono", "Email", "Casa de Corretaje"]
    ws2.append(holdings_headers)
    
    for cell in ws2[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
    
    # Get holdings with user info
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "id",
                "as": "user_info"
            }
        },
        {
            "$sort": {
                "filing_date": 1,
                "isin_or_latinex_code": 1,
                "holder_name": 1
            }
        }
    ]
    
    holdings_with_users = await db.holdings.aggregate(pipeline).to_list(1000)
    for holding in holdings_with_users:
        user_info = holding.get("user_info", [{}])[0]
        ws2.append([
            holding["filing_date"],
            holding["isin_or_latinex_code"],
            holding["holder_name"],
            holding["holder_id"],
            holding.get("legal_representative", ""),
            holding["amount_held"],
            holding["address"],
            holding["phone"],
            holding["email"],
            user_info.get("brokerage_name", "")
        ])
    
    # Sheet 3: Master Consolidated Holdings
    ws3 = wb.create_sheet("Tenencias_Consolidadas")
    master_headers = ["Fecha de Presentación", "Código ISIN/Latinex", "Descripción del Valor",
                     "Nombre del Tenedor", "ID del Tenedor", "Cantidad Total", 
                     "Número de Registros"]
    ws3.append(master_headers)
    
    for cell in ws3[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
    
    master_holdings = await db.master_holdings.find().sort([
        ("filing_date", 1), ("isin_or_latinex_code", 1), ("holder_name", 1)
    ]).to_list(1000)
    
    for master in master_holdings:
        # Get security description
        security_info = None
        if master.get("source_holdings"):
            security_info = master["source_holdings"][0].get("security_info", {})
        
        ws3.append([
            master["filing_date"],
            master["isin_or_latinex_code"],
            security_info.get("security_description", "") if security_info else "",
            master["holder_name"],
            master["holder_id"],
            master["total_amount"],
            master["holdings_count"]
        ])
    
    # Auto-adjust column widths
    for ws in [ws1, ws2, ws3]:
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tenencias_bonos_panama_{timestamp}.xlsx"
    
    return StreamingResponse(
        BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Create default admin on startup
@app.on_event("startup")
async def create_default_admin():
    admin_exists = await db.admins.find_one({"username": "admin"})
    if not admin_exists:
        admin_data = {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "email": "admin@sistema.com",
            "hashed_password": get_password_hash("admin123"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.admins.insert_one(admin_data)
        print("Admin por defecto creado: usuario 'admin', contraseña 'admin123'")

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
