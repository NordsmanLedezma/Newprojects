import requests
import sys
import json
from datetime import datetime

class LoanCalculatorAPITester:
    def __init__(self, base_url="https://loan-calc-py.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        result = {
            "test_name": name,
            "status": status,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        print(f"{status} - {name}")
        if details:
            print(f"   Details: {details}")

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/")
            success = response.status_code == 200
            details = f"Status: {response.status_code}, Response: {response.json() if success else response.text}"
            self.log_test("API Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("API Root Endpoint", False, f"Error: {str(e)}")
            return False

    def test_currencies_endpoint(self):
        """Test currencies endpoint"""
        try:
            response = requests.get(f"{self.api_url}/currencies")
            success = response.status_code == 200
            if success:
                data = response.json()
                expected_currencies = ["EUR", "USD", "CHF", "JPY"]
                has_currencies = "currencies" in data and all(curr in data["currencies"] for curr in expected_currencies)
                has_rates = "exchange_rates" in data
                success = has_currencies and has_rates
                details = f"Currencies: {data.get('currencies', [])}, Has rates: {has_rates}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Currencies Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Currencies Endpoint", False, f"Error: {str(e)}")
            return False

    def test_loan_calculation_basic(self):
        """Test basic loan calculation"""
        try:
            payload = {
                "loan_amount": 100000,
                "interest_rate": 3.5,
                "term_years": 25,
                "currency": "EUR",
                "rate_type": "fixed",
                "grace_period_months": 0,
                "upfront_commission_bps": 0,
                "insurance_fee_bps": 0,
                "floating_rate_margin": 0
            }
            
            response = requests.post(f"{self.api_url}/calculate-loan", json=payload)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["id", "loan_input", "loan_summary", "amortization_schedule", "created_at"]
                has_required_fields = all(field in data for field in required_fields)
                
                # Check loan summary fields
                summary_fields = ["monthly_payment", "total_payments", "total_interest", "total_cost"]
                has_summary_fields = all(field in data.get("loan_summary", {}) for field in summary_fields)
                
                # Check amortization schedule
                has_schedule = len(data.get("amortization_schedule", [])) > 0
                
                success = has_required_fields and has_summary_fields and has_schedule
                details = f"Fields OK: {has_required_fields}, Summary OK: {has_summary_fields}, Schedule entries: {len(data.get('amortization_schedule', []))}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Basic Loan Calculation", success, details)
            return success, data if success else None
        except Exception as e:
            self.log_test("Basic Loan Calculation", False, f"Error: {str(e)}")
            return False, None

    def test_loan_calculation_with_advanced_options(self):
        """Test loan calculation with advanced options"""
        try:
            payload = {
                "loan_amount": 250000,
                "interest_rate": 4.25,
                "term_years": 30,
                "currency": "USD",
                "rate_type": "floating",
                "grace_period_months": 12,
                "upfront_commission_bps": 50,  # 0.5%
                "insurance_fee_bps": 25,       # 0.25%
                "floating_rate_margin": 0.5
            }
            
            response = requests.post(f"{self.api_url}/calculate-loan", json=payload)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                # Check that grace period is reflected in schedule
                schedule = data.get("amortization_schedule", [])
                grace_payments = [p for p in schedule[:12] if p.get("principal_payment", 0) == 0]
                has_grace_period = len(grace_payments) == 12
                
                # Check commission and insurance fees
                summary = data.get("loan_summary", {})
                has_commission = summary.get("upfront_commission", 0) > 0
                has_insurance = summary.get("total_insurance_fees", 0) > 0
                
                success = has_grace_period and has_commission and has_insurance
                details = f"Grace period payments: {len(grace_payments)}/12, Commission: {has_commission}, Insurance: {has_insurance}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Advanced Loan Calculation", success, details)
            return success, data if success else None
        except Exception as e:
            self.log_test("Advanced Loan Calculation", False, f"Error: {str(e)}")
            return False, None

    def test_multi_currency_support(self):
        """Test calculations in different currencies"""
        currencies = ["EUR", "USD", "CHF", "JPY"]
        all_success = True
        
        for currency in currencies:
            try:
                payload = {
                    "loan_amount": 100000,
                    "interest_rate": 3.0,
                    "term_years": 20,
                    "currency": currency,
                    "rate_type": "fixed",
                    "grace_period_months": 0,
                    "upfront_commission_bps": 0,
                    "insurance_fee_bps": 0
                }
                
                response = requests.post(f"{self.api_url}/calculate-loan", json=payload)
                success = response.status_code == 200
                
                if success:
                    data = response.json()
                    correct_currency = data.get("loan_input", {}).get("currency") == currency
                    success = correct_currency
                    details = f"Currency: {currency}, Correct: {correct_currency}"
                else:
                    details = f"Status: {response.status_code}"
                
                self.log_test(f"Currency Support - {currency}", success, details)
                if not success:
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"Currency Support - {currency}", False, f"Error: {str(e)}")
                all_success = False
        
        return all_success

    def test_loan_history(self):
        """Test loan history endpoint"""
        try:
            response = requests.get(f"{self.api_url}/loan-history")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                is_list = isinstance(data, list)
                details = f"Response is list: {is_list}, Count: {len(data) if is_list else 'N/A'}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Loan History Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Loan History Endpoint", False, f"Error: {str(e)}")
            return False

    def test_excel_export(self, loan_id):
        """Test Excel export functionality"""
        if not loan_id:
            self.log_test("Excel Export", False, "No loan ID available for testing")
            return False
            
        try:
            response = requests.post(f"{self.api_url}/export-excel/{loan_id}")
            success = response.status_code == 200
            
            if success:
                content_type = response.headers.get('content-type', '')
                is_excel = 'spreadsheet' in content_type or 'excel' in content_type
                has_content = len(response.content) > 0
                success = is_excel and has_content
                details = f"Content-Type: {content_type}, Size: {len(response.content)} bytes"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Excel Export", success, details)
            return success
        except Exception as e:
            self.log_test("Excel Export", False, f"Error: {str(e)}")
            return False

    def test_input_validation(self):
        """Test input validation"""
        test_cases = [
            {
                "name": "Negative loan amount",
                "payload": {"loan_amount": -1000, "interest_rate": 3.5, "term_years": 25},
                "should_fail": True
            },
            {
                "name": "Invalid interest rate",
                "payload": {"loan_amount": 100000, "interest_rate": 100, "term_years": 25},
                "should_fail": True
            },
            {
                "name": "Invalid term years",
                "payload": {"loan_amount": 100000, "interest_rate": 3.5, "term_years": 50},
                "should_fail": True
            },
            {
                "name": "Missing required fields",
                "payload": {"loan_amount": 100000},
                "should_fail": True
            }
        ]
        
        all_success = True
        for test_case in test_cases:
            try:
                response = requests.post(f"{self.api_url}/calculate-loan", json=test_case["payload"])
                
                if test_case["should_fail"]:
                    success = response.status_code != 200
                    details = f"Expected failure, got status: {response.status_code}"
                else:
                    success = response.status_code == 200
                    details = f"Expected success, got status: {response.status_code}"
                
                self.log_test(f"Validation - {test_case['name']}", success, details)
                if not success:
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"Validation - {test_case['name']}", False, f"Error: {str(e)}")
                all_success = False
        
        return all_success

    def run_all_tests(self):
        """Run all backend API tests"""
        print(f"🚀 Starting Loan Calculator API Tests")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test basic connectivity
        if not self.test_api_root():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Test endpoints
        self.test_currencies_endpoint()
        
        # Test loan calculations
        basic_success, basic_data = self.test_loan_calculation_basic()
        loan_id = basic_data.get("id") if basic_data else None
        
        self.test_loan_calculation_with_advanced_options()
        self.test_multi_currency_support()
        
        # Test history and export
        self.test_loan_history()
        if loan_id:
            self.test_excel_export(loan_id)
        
        # Test validation
        self.test_input_validation()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = LoanCalculatorAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
            "test_results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())