from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone
import math
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import tempfile
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Currency exchange rates (mock data - in real app would fetch from API)
EXCHANGE_RATES = {
    "EUR": 1.0,  # Base currency
    "USD": 1.0950,
    "CHF": 0.9850,
    "JPY": 163.25
}

# Define Models
class ReferenceRateSchedule(BaseModel):
    payment_number: int = Field(..., ge=1, description="Payment number (starting from 1)")
    reference_rate: float = Field(..., ge=0, le=50, description="Reference rate as percentage for this payment period")

class LoanInput(BaseModel):
    loan_amount: float = Field(..., gt=0, description="Loan amount")
    interest_rate: float = Field(..., ge=0, le=50, description="Annual interest rate as percentage (for fixed rate) or initial reference rate (for floating rate)")
    term_years: int = Field(..., gt=0, le=30, description="Loan term in years")
    currency: Literal["EUR", "USD", "CHF", "JPY"] = Field(default="EUR")
    rate_type: Literal["fixed", "floating"] = Field(default="fixed")
    grace_period_months: int = Field(default=0, ge=0, le=60, description="Grace period in months")
    upfront_commission_bps: float = Field(default=0, ge=0, le=1000, description="Upfront commission in basis points")
    insurance_fee_bps: float = Field(default=0, ge=0, le=1000, description="Insurance fee in basis points")
    # Floating rate specific fields
    spread_bps: Optional[float] = Field(default=0, ge=0, le=1000, description="Spread in basis points added to reference rate (for floating rate)")
    reference_rate_schedule: Optional[List[ReferenceRateSchedule]] = Field(default=[], description="Reference rate schedule for floating rate loans")

class AmortizationPayment(BaseModel):
    payment_number: int
    payment_date: str
    beginning_balance: float
    payment_amount: float
    principal_payment: float
    interest_payment: float
    insurance_fee: float
    ending_balance: float
    cumulative_interest: float
    cumulative_principal: float

class LoanSummary(BaseModel):
    monthly_payment: float
    total_payments: float
    total_interest: float
    total_insurance_fees: float
    upfront_commission: float
    total_cost: float
    effective_rate: float
    loan_to_value: float

class LoanResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    loan_input: LoanInput
    loan_summary: LoanSummary
    amortization_schedule: List[AmortizationPayment]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

def calculate_monthly_payment(principal: float, annual_rate: float, num_payments: int) -> float:
    """Calculate monthly payment using PMT formula"""
    if annual_rate == 0:
        return principal / num_payments
    
    monthly_rate = annual_rate / 100 / 12
    payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
    return payment

def get_effective_interest_rate(loan_input: LoanInput, payment_number: int) -> float:
    """Get the effective interest rate for a specific payment"""
    if loan_input.rate_type == "fixed":
        return loan_input.interest_rate
    
    # For floating rate, find the applicable reference rate
    if loan_input.reference_rate_schedule:
        # Find the most recent rate applicable to this payment
        applicable_rate = loan_input.interest_rate  # Default to initial rate
        for rate_schedule in loan_input.reference_rate_schedule:
            if rate_schedule.payment_number <= payment_number:
                applicable_rate = rate_schedule.reference_rate
            else:
                break
        
        # Add spread (convert basis points to percentage)
        spread_percentage = (loan_input.spread_bps or 0) / 100
        return applicable_rate + spread_percentage
    else:
        # No schedule provided, use initial rate + spread
        spread_percentage = (loan_input.spread_bps or 0) / 100
        return loan_input.interest_rate + spread_percentage

def generate_amortization_schedule(loan_input: LoanInput) -> tuple[LoanSummary, List[AmortizationPayment]]:
    """Generate complete amortization schedule with floating rate support"""
    principal = loan_input.loan_amount
    initial_rate = loan_input.interest_rate
    term_months = loan_input.term_years * 12
    grace_period = loan_input.grace_period_months
    
    # Calculate upfront commission
    upfront_commission = principal * loan_input.upfront_commission_bps / 10000
    
    # Adjust principal for upfront commission (reduce available funds)
    net_principal = principal - upfront_commission
    
    # For floating rate loans, we'll calculate payment based on initial rate
    # and recalculate as rates change
    if loan_input.rate_type == "floating":
        effective_initial_rate = get_effective_interest_rate(loan_input, 1)
    else:
        effective_initial_rate = initial_rate
    
    # Calculate initial monthly payment (after grace period)
    payment_months = term_months - grace_period
    if loan_input.rate_type == "fixed":
        monthly_payment = calculate_monthly_payment(net_principal, effective_initial_rate, payment_months)
    else:
        # For floating rate, we'll recalculate payment amount based on remaining balance and current rate
        monthly_payment = calculate_monthly_payment(net_principal, effective_initial_rate, payment_months)
    
    # Insurance fee per payment
    monthly_insurance_fee = principal * loan_input.insurance_fee_bps / 10000 / 12
    
    schedule = []
    remaining_balance = net_principal
    cumulative_interest = 0
    cumulative_principal = 0
    cumulative_insurance = 0
    
    for payment_num in range(1, term_months + 1):
        # During grace period, only interest and insurance are paid
        if payment_num <= grace_period:
            interest_payment = remaining_balance * (annual_rate / 100 / 12)
            principal_payment = 0
            total_payment = interest_payment + monthly_insurance_fee
        else:
            # Regular amortization payments
            interest_payment = remaining_balance * (annual_rate / 100 / 12)
            principal_payment = monthly_payment - interest_payment
            total_payment = monthly_payment + monthly_insurance_fee
            
            # Ensure we don't pay more principal than remaining
            if principal_payment > remaining_balance:
                principal_payment = remaining_balance
                total_payment = principal_payment + interest_payment + monthly_insurance_fee
        
        # Update balances
        remaining_balance -= principal_payment
        cumulative_interest += interest_payment
        cumulative_principal += principal_payment
        cumulative_insurance += monthly_insurance_fee
        
        # Calculate payment date (assuming monthly payments)
        payment_date = datetime.now(timezone.utc).replace(day=1)
        payment_date = payment_date.replace(month=((payment_date.month + payment_num - 1) % 12) + 1)
        if payment_num > 12:
            payment_date = payment_date.replace(year=payment_date.year + (payment_num - 1) // 12)
        
        payment = AmortizationPayment(
            payment_number=payment_num,
            payment_date=payment_date.strftime("%Y-%m-%d"),
            beginning_balance=remaining_balance + principal_payment,
            payment_amount=total_payment,
            principal_payment=principal_payment,
            interest_payment=interest_payment,
            insurance_fee=monthly_insurance_fee,
            ending_balance=remaining_balance,
            cumulative_interest=cumulative_interest,
            cumulative_principal=cumulative_principal
        )
        schedule.append(payment)
        
        # Break if loan is fully paid
        if remaining_balance <= 0.01:
            break
    
    # Calculate summary
    total_payments = sum(p.payment_amount for p in schedule)
    total_interest = cumulative_interest
    total_insurance_fees = cumulative_insurance
    total_cost = total_payments + upfront_commission
    effective_rate = (total_cost / principal - 1) * 100 / loan_input.term_years
    
    summary = LoanSummary(
        monthly_payment=monthly_payment + monthly_insurance_fee,
        total_payments=total_payments,
        total_interest=total_interest,
        total_insurance_fees=total_insurance_fees,
        upfront_commission=upfront_commission,
        total_cost=total_cost,
        effective_rate=effective_rate,
        loan_to_value=100.0  # Assuming full loan amount
    )
    
    return summary, schedule

def create_excel_report(loan_result: LoanResult) -> str:
    """Create Excel report and return file path"""
    wb = Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Create Summary sheet
    summary_sheet = wb.create_sheet("Loan Summary")
    
    # Header style
    header_font = Font(bold=True, size=12)
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    # Summary data
    loan_input = loan_result.loan_input
    summary = loan_result.loan_summary
    
    summary_data = [
        ["Loan Details", ""],
        ["Loan Amount", f"{loan_input.loan_amount:,.2f} {loan_input.currency}"],
        ["Interest Rate", f"{loan_input.interest_rate:.2f}%"],
        ["Term", f"{loan_input.term_years} years"],
        ["Rate Type", loan_input.rate_type.title()],
        ["Grace Period", f"{loan_input.grace_period_months} months"],
        ["Upfront Commission", f"{loan_input.upfront_commission_bps} bps"],
        ["Insurance Fee", f"{loan_input.insurance_fee_bps} bps annually"],
        ["", ""],
        ["Payment Summary", ""],
        ["Monthly Payment", f"{summary.monthly_payment:,.2f} {loan_input.currency}"],
        ["Total Payments", f"{summary.total_payments:,.2f} {loan_input.currency}"],
        ["Total Interest", f"{summary.total_interest:,.2f} {loan_input.currency}"],
        ["Total Insurance Fees", f"{summary.total_insurance_fees:,.2f} {loan_input.currency}"],
        ["Upfront Commission", f"{summary.upfront_commission:,.2f} {loan_input.currency}"],
        ["Total Cost of Loan", f"{summary.total_cost:,.2f} {loan_input.currency}"],
        ["Effective Annual Rate", f"{summary.effective_rate:.2f}%"]
    ]
    
    for row_idx, (label, value) in enumerate(summary_data, 1):
        summary_sheet.cell(row=row_idx, column=1, value=label)
        summary_sheet.cell(row=row_idx, column=2, value=value)
        if label in ["Loan Details", "Payment Summary"]:
            summary_sheet.cell(row=row_idx, column=1).font = header_font
    
    # Adjust column widths
    summary_sheet.column_dimensions['A'].width = 25
    summary_sheet.column_dimensions['B'].width = 20
    
    # Create Amortization Schedule sheet
    schedule_sheet = wb.create_sheet("Amortization Schedule")
    
    headers = [
        "Payment #", "Payment Date", "Beginning Balance", "Payment Amount",
        "Principal", "Interest", "Insurance Fee", "Ending Balance",
        "Cumulative Interest", "Cumulative Principal"
    ]
    
    # Add headers
    for col_idx, header in enumerate(headers, 1):
        cell = schedule_sheet.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    
    # Add schedule data
    for row_idx, payment in enumerate(loan_result.amortization_schedule, 2):
        schedule_sheet.cell(row=row_idx, column=1, value=payment.payment_number)
        schedule_sheet.cell(row=row_idx, column=2, value=payment.payment_date)
        schedule_sheet.cell(row=row_idx, column=3, value=f"{payment.beginning_balance:.2f}")
        schedule_sheet.cell(row=row_idx, column=4, value=f"{payment.payment_amount:.2f}")
        schedule_sheet.cell(row=row_idx, column=5, value=f"{payment.principal_payment:.2f}")
        schedule_sheet.cell(row=row_idx, column=6, value=f"{payment.interest_payment:.2f}")
        schedule_sheet.cell(row=row_idx, column=7, value=f"{payment.insurance_fee:.2f}")
        schedule_sheet.cell(row=row_idx, column=8, value=f"{payment.ending_balance:.2f}")
        schedule_sheet.cell(row=row_idx, column=9, value=f"{payment.cumulative_interest:.2f}")
        schedule_sheet.cell(row=row_idx, column=10, value=f"{payment.cumulative_principal:.2f}")
    
    # Adjust column widths for schedule
    for col in range(1, 11):
        schedule_sheet.column_dimensions[get_column_letter(col)].width = 15
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    wb.save(temp_file.name)
    temp_file.close()
    
    return temp_file.name

# API Routes
@api_router.post("/calculate-loan", response_model=LoanResult)
async def calculate_loan(loan_input: LoanInput):
    """Calculate loan amortization schedule"""
    try:
        summary, schedule = generate_amortization_schedule(loan_input)
        
        result = LoanResult(
            loan_input=loan_input,
            loan_summary=summary,
            amortization_schedule=schedule
        )
        
        # Save to database
        result_dict = result.dict()
        result_dict['created_at'] = result_dict['created_at'].isoformat()
        await db.loan_calculations.insert_one(result_dict)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/loan-history", response_model=List[LoanResult])
async def get_loan_history():
    """Get loan calculation history"""
    try:
        calculations = await db.loan_calculations.find().sort("created_at", -1).limit(50).to_list(50)
        results = []
        for calc in calculations:
            calc['created_at'] = datetime.fromisoformat(calc['created_at'])
            results.append(LoanResult(**calc))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/export-excel/{loan_id}")
async def export_excel(loan_id: str):
    """Export loan calculation to Excel"""
    try:
        # Get loan calculation from database
        calc = await db.loan_calculations.find_one({"id": loan_id})
        if not calc:
            raise HTTPException(status_code=404, detail="Loan calculation not found")
        
        calc['created_at'] = datetime.fromisoformat(calc['created_at'])
        loan_result = LoanResult(**calc)
        
        # Create Excel file
        excel_path = create_excel_report(loan_result)
        
        # Return file
        return FileResponse(
            path=excel_path,
            filename=f"loan_calculation_{loan_id[:8]}.xlsx",
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/currencies")
async def get_currencies():
    """Get supported currencies with exchange rates"""
    return {
        "currencies": list(EXCHANGE_RATES.keys()),
        "exchange_rates": EXCHANGE_RATES
    }

@api_router.get("/")
async def root():
    return {"message": "Loan Calculator API"}

# Include the router in the main app
app.include_router(api_router)

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
