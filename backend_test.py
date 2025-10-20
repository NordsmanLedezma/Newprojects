import requests
import sys
import json
from datetime import datetime
from io import BytesIO
import openpyxl

class BondsAPITester:
    def __init__(self, base_url="https://bondregistry.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.user_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_user_id = None
        self.created_security_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, files=files, headers=headers, timeout=10)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 200:
                        print(f"   Response: {response_data}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed - Connection error")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
            return True
        return False

    def test_create_user(self):
        """Test creating a new user"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "username": f"testuser_{timestamp}",
            "password": "testpass123",
            "email": f"test_{timestamp}@example.com",
            "brokerage_name": "Casa de Prueba"
        }
        
        success, response = self.run_test(
            "Create User",
            "POST",
            "admin/users",
            200,
            data=user_data,
            token=self.admin_token
        )
        if success and 'id' in response:
            self.created_user_id = response['id']
            return True, user_data
        return False, {}

    def test_user_login(self, user_data):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"username": user_data["username"], "password": user_data["password"]}
        )
        if success and 'access_token' in response:
            self.user_token = response['access_token']
            print(f"   User token obtained: {self.user_token[:20]}...")
            return True
        return False

    def test_get_users(self):
        """Test getting all users"""
        success, response = self.run_test(
            "Get Users",
            "GET",
            "admin/users",
            200,
            token=self.admin_token
        )
        return success

    def test_create_security(self):
        """Test creating a new security"""
        timestamp = datetime.now().strftime('%H%M%S')
        security_data = {
            "isin_code": f"US{timestamp}AK07",
            "latinex_code": f"RPME{timestamp}429A",
            "security_description": "República de Panamá - Bono de Prueba",
            "coupon": "9.375%",
            "issue_date": "2024-01-01",
            "maturity_date": "2034-01-01"
        }
        
        success, response = self.run_test(
            "Create Security",
            "POST",
            "admin/securities",
            200,
            data=security_data,
            token=self.admin_token
        )
        if success and 'id' in response:
            self.created_security_id = response['id']
            return True, security_data
        return False, {}

    def test_get_securities(self):
        """Test getting all securities"""
        success, response = self.run_test(
            "Get Securities",
            "GET",
            "admin/securities",
            200,
            token=self.admin_token
        )
        return success

    def test_search_security(self, security_data):
        """Test searching for a security"""
        success, response = self.run_test(
            "Search Security by ISIN",
            "GET",
            f"securities/search/{security_data['isin_code']}",
            200,
            token=self.user_token
        )
        return success

    def test_create_holding(self, security_data):
        """Test creating a holding"""
        holding_data = {
            "filing_date": "2024-01-15",
            "isin_or_latinex_code": security_data["isin_code"],
            "holder_name": "Juan Pérez",
            "holder_id": "8-123-456",
            "legal_representative": "María González",
            "amount_held": 100000.50,
            "address": "Calle 50, Ciudad de Panamá",
            "phone": "+507-123-4567",
            "email": "juan.perez@example.com"
        }
        
        success, response = self.run_test(
            "Create Holding",
            "POST",
            "holdings",
            200,
            data=holding_data,
            token=self.user_token
        )
        return success

    def test_get_user_holdings(self):
        """Test getting user holdings"""
        success, response = self.run_test(
            "Get User Holdings",
            "GET",
            "holdings",
            200,
            token=self.user_token
        )
        return success

    def test_get_all_holdings(self):
        """Test getting all holdings (admin)"""
        success, response = self.run_test(
            "Get All Holdings",
            "GET",
            "admin/holdings",
            200,
            token=self.admin_token
        )
        return success

    def test_toggle_user_status(self):
        """Test toggling user status"""
        if not self.created_user_id:
            print("❌ No user ID available for toggle test")
            return False
            
        success, response = self.run_test(
            "Toggle User Status",
            "PUT",
            f"admin/users/{self.created_user_id}/toggle",
            200,
            token=self.admin_token
        )
        return success

    def test_export_excel(self):
        """Test Excel export"""
        success, response = self.run_test(
            "Export to Excel",
            "GET",
            "admin/export/excel",
            200,
            token=self.admin_token
        )
        return success

    def create_test_excel_file(self):
        """Create a test Excel file for import testing"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Valores_ISIN"
        
        # Headers
        headers = ["Código ISIN", "Código Latinex", "Descripción del Valor", 
                  "Cupón", "Fecha de Emisión", "Fecha de Vencimiento"]
        ws.append(headers)
        
        # Test data
        timestamp = datetime.now().strftime('%H%M%S')
        test_data = [
            [f"US{timestamp}001", f"LTST{timestamp}001", "Test Bond Import 1", "4.5%", "2024-01-01", "2029-01-01"],
            [f"US{timestamp}002", f"LTST{timestamp}002", "Test Bond Import 2", "5.0%", "2024-02-01", "2030-02-01"],
            ["", f"LTST{timestamp}003", "Test Bond Import 3 (No ISIN)", "3.75%", "2024-03-01", "2028-03-01"]
        ]
        
        for row in test_data:
            ws.append(row)
        
        # Save to BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        return excel_buffer

    def test_excel_import(self):
        """Test Excel import functionality"""
        print(f"\n🔍 Testing Excel Import...")
        
        # Create test Excel file
        excel_file = self.create_test_excel_file()
        
        # Prepare file for upload
        files = {
            'file': ('test_valores.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Excel Import (Valid File)",
            "POST",
            "admin/import/excel",
            200,
            files=files,
            token=self.admin_token
        )
        
        if success and isinstance(response, dict):
            print(f"   Import result: {response.get('message', 'No message')}")
            print(f"   Imported count: {response.get('imported_count', 0)}")
            if response.get('errors'):
                print(f"   Errors: {len(response['errors'])}")
        
        return success

    def test_invalid_excel_import(self):
        """Test Excel import with invalid file"""
        print(f"\n🔍 Testing Invalid Excel Import...")
        
        # Create a text file instead of Excel
        fake_file = BytesIO(b"This is not an Excel file")
        files = {
            'file': ('fake.txt', fake_file, 'text/plain')
        }
        
        success, response = self.run_test(
            "Excel Import (Invalid File)",
            "POST",
            "admin/import/excel",
            400,  # Should return 400 for invalid file format
            files=files,
            token=self.admin_token
        )
        
        return success

    def test_clear_all_securities(self):
        """Test clearing all securities - MAIN FEATURE TO TEST"""
        print(f"\n🔍 Testing Clear All Securities...")
        
        # First, get current count of securities
        success, response = self.run_test(
            "Get Securities Count (Before Clear)",
            "GET",
            "admin/securities",
            200,
            token=self.admin_token
        )
        
        if success and isinstance(response, list):
            count_before = len(response)
            print(f"   Securities before clear: {count_before}")
        else:
            count_before = 0
            print("   Could not get securities count before clear")
        
        # Test the clear all endpoint
        success, response = self.run_test(
            "Clear All Securities",
            "DELETE",
            "admin/securities/clear-all",
            200,
            token=self.admin_token
        )
        
        if success and isinstance(response, dict):
            deleted_count = response.get('deleted_count', 0)
            total_before = response.get('total_before', 0)
            message = response.get('message', '')
            
            print(f"   Result: {message}")
            print(f"   Deleted count: {deleted_count}")
            print(f"   Total before: {total_before}")
            
            # Verify the list is now empty
            success_verify, response_verify = self.run_test(
                "Verify Securities Cleared",
                "GET",
                "admin/securities",
                200,
                token=self.admin_token
            )
            
            if success_verify and isinstance(response_verify, list):
                count_after = len(response_verify)
                print(f"   Securities after clear: {count_after}")
                
                if count_after == 0:
                    print("✅ Clear all functionality working correctly")
                    return True
                else:
                    print(f"❌ Clear all failed - still {count_after} securities remaining")
                    return False
            else:
                print("❌ Could not verify securities were cleared")
                return False
        else:
            print("❌ Clear all endpoint failed or returned unexpected response")
            return False

    def test_clear_all_permissions(self):
        """Test that only admins can clear all securities"""
        print(f"\n🔍 Testing Clear All Permissions (Non-Admin Access)...")
        
        # Try to clear all securities with user token (should fail)
        success, response = self.run_test(
            "Clear All Securities (User Token - Should Fail)",
            "DELETE",
            "admin/securities/clear-all",
            403,  # Should return 403 Forbidden
            token=self.user_token
        )
        
        if success:
            print("✅ Permission validation working - non-admin access denied")
            return True
        else:
            print("❌ Permission validation failed - non-admin was able to access")
            return False

    def test_clear_all_without_token(self):
        """Test clear all without authentication token"""
        print(f"\n🔍 Testing Clear All Without Token...")
        
        success, response = self.run_test(
            "Clear All Securities (No Token - Should Fail)",
            "DELETE",
            "admin/securities/clear-all",
            401,  # Should return 401 Unauthorized
            token=None
        )
        
        if success:
            print("✅ Authentication validation working - no token access denied")
            return True
        else:
            print("❌ Authentication validation failed - no token access allowed")
            return False

def main():
    print("🚀 Starting Panamanian Bonds API Testing...")
    print("=" * 60)
    
    tester = BondsAPITester()
    
    # Test admin login first
    if not tester.test_admin_login():
        print("\n❌ Admin login failed - stopping tests")
        return 1

    # Test user management
    user_created, user_data = tester.test_create_user()
    if not user_created:
        print("\n❌ User creation failed")
        return 1

    if not tester.test_user_login(user_data):
        print("\n❌ User login failed")
        return 1

    tester.test_get_users()

    # Test securities management
    security_created, security_data = tester.test_create_security()
    if not security_created:
        print("\n❌ Security creation failed")
        return 1

    tester.test_get_securities()
    tester.test_search_security(security_data)

    # Test holdings management
    tester.test_create_holding(security_data)
    tester.test_get_user_holdings()
    tester.test_get_all_holdings()

    # Test additional admin functions
    tester.test_toggle_user_status()
    tester.test_export_excel()
    
    # Test Excel import functionality
    tester.test_excel_import()
    tester.test_invalid_excel_import()

    # Test Clear All Securities functionality (MAIN FEATURE)
    print("\n" + "🔥" * 30)
    print("🎯 TESTING CLEAR ALL SECURITIES FUNCTIONALITY")
    print("🔥" * 30)
    
    # Test permission validations first
    tester.test_clear_all_permissions()
    tester.test_clear_all_without_token()
    
    # Test the actual clear all functionality
    tester.test_clear_all_securities()

    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS:")
    print(f"   Tests run: {tester.tests_run}")
    print(f"   Tests passed: {tester.tests_passed}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())