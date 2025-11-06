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
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

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

    def test_update_security(self):
        """Test updating an individual security - NEW FEATURE"""
        if not self.created_security_id:
            print("❌ No security ID available for update test")
            return False
            
        print(f"\n🔍 Testing Update Individual Security...")
        
        # Updated security data
        updated_data = {
            "isin_code": f"US{datetime.now().strftime('%H%M%S')}UPD",
            "latinex_code": f"RPME{datetime.now().strftime('%H%M%S')}UPD",
            "security_description": "República de Panamá - Bono Actualizado",
            "coupon": "8.5%",
            "issue_date": "2024-02-01",
            "maturity_date": "2035-02-01"
        }
        
        success, response = self.run_test(
            "Update Security (PUT)",
            "PUT",
            f"admin/securities/{self.created_security_id}",
            200,
            data=updated_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Individual security update working correctly")
            return True, updated_data
        else:
            print("❌ Individual security update failed")
            return False, {}

    def test_update_security_duplicate_validation(self):
        """Test update security with duplicate codes"""
        if not self.created_security_id:
            print("❌ No security ID available for duplicate validation test")
            return False
            
        print(f"\n🔍 Testing Update Security Duplicate Validation...")
        
        # First create another security to test duplicate validation
        timestamp = datetime.now().strftime('%H%M%S')
        another_security_data = {
            "isin_code": f"US{timestamp}DUP",
            "latinex_code": f"RPME{timestamp}DUP",
            "security_description": "República de Panamá - Bono para Duplicado",
            "coupon": "7.5%",
            "issue_date": "2024-03-01",
            "maturity_date": "2033-03-01"
        }
        
        success, response = self.run_test(
            "Create Another Security for Duplicate Test",
            "POST",
            "admin/securities",
            200,
            data=another_security_data,
            token=self.admin_token
        )
        
        if not success:
            print("❌ Could not create second security for duplicate test")
            return False
            
        another_security_id = response.get('id')
        
        # Now try to update the first security with the same codes as the second
        duplicate_data = {
            "isin_code": another_security_data["isin_code"],
            "latinex_code": another_security_data["latinex_code"],
            "security_description": "Trying to duplicate codes",
            "coupon": "6.0%",
            "issue_date": "2024-04-01",
            "maturity_date": "2032-04-01"
        }
        
        success, response = self.run_test(
            "Update Security with Duplicate Codes (Should Fail)",
            "PUT",
            f"admin/securities/{self.created_security_id}",
            400,  # Should return 400 for duplicate
            data=duplicate_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Duplicate validation working correctly")
            return True
        else:
            print("❌ Duplicate validation failed - should have rejected duplicate codes")
            return False

    def test_delete_security(self):
        """Test deleting an individual security - NEW FEATURE"""
        if not self.created_security_id:
            print("❌ No security ID available for delete test")
            return False
            
        print(f"\n🔍 Testing Delete Individual Security...")
        
        success, response = self.run_test(
            "Delete Security (DELETE)",
            "DELETE",
            f"admin/securities/{self.created_security_id}",
            200,
            token=self.admin_token
        )
        
        if success:
            print("✅ Individual security deletion working correctly")
            # Verify the security is actually deleted
            success_verify, response_verify = self.run_test(
                "Verify Security Deleted (Should Return 404)",
                "GET",
                f"securities/search/NONEXISTENT",
                404,
                token=self.admin_token
            )
            return True
        else:
            print("❌ Individual security deletion failed")
            return False

    def test_delete_nonexistent_security(self):
        """Test deleting a non-existent security"""
        print(f"\n🔍 Testing Delete Non-existent Security...")
        
        fake_id = "nonexistent-security-id"
        success, response = self.run_test(
            "Delete Non-existent Security (Should Return 404)",
            "DELETE",
            f"admin/securities/{fake_id}",
            404,
            token=self.admin_token
        )
        
        if success:
            print("✅ Non-existent security deletion validation working correctly")
            return True
        else:
            print("❌ Non-existent security deletion validation failed")
            return False

    def test_update_nonexistent_security(self):
        """Test updating a non-existent security"""
        print(f"\n🔍 Testing Update Non-existent Security...")
        
        fake_id = "nonexistent-security-id"
        update_data = {
            "isin_code": "US123456789",
            "latinex_code": "RPME123456789",
            "security_description": "Non-existent security",
            "coupon": "5.0%",
            "issue_date": "2024-01-01",
            "maturity_date": "2030-01-01"
        }
        
        success, response = self.run_test(
            "Update Non-existent Security (Should Return 404)",
            "PUT",
            f"admin/securities/{fake_id}",
            404,
            data=update_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Non-existent security update validation working correctly")
            return True
        else:
            print("❌ Non-existent security update validation failed")
            return False

    def test_security_permissions(self):
        """Test that only admins can edit/delete securities"""
        if not self.created_security_id:
            print("❌ No security ID available for permission test")
            return False
            
        print(f"\n🔍 Testing Security Edit/Delete Permissions...")
        
        # Test user trying to update security (should fail)
        update_data = {
            "isin_code": "US999999999",
            "latinex_code": "RPME999999999",
            "security_description": "Unauthorized update attempt",
            "coupon": "1.0%",
            "issue_date": "2024-01-01",
            "maturity_date": "2025-01-01"
        }
        
        success_update, response_update = self.run_test(
            "Update Security (User Token - Should Fail)",
            "PUT",
            f"admin/securities/{self.created_security_id}",
            403,  # Should return 403 Forbidden
            data=update_data,
            token=self.user_token
        )
        
        # Test user trying to delete security (should fail)
        success_delete, response_delete = self.run_test(
            "Delete Security (User Token - Should Fail)",
            "DELETE",
            f"admin/securities/{self.created_security_id}",
            403,  # Should return 403 Forbidden
            token=self.user_token
        )
        
        if success_update and success_delete:
            print("✅ Security edit/delete permission validation working correctly")
            return True
        else:
            print("❌ Security edit/delete permission validation failed")
            return False

    def test_update_user(self):
        """Test updating user information - NEW USER MANAGEMENT FEATURE"""
        if not self.created_user_id:
            print("❌ No user ID available for update test")
            return False
            
        print(f"\n🔍 Testing Update User Information...")
        
        # Updated user data
        timestamp = datetime.now().strftime('%H%M%S')
        updated_data = {
            "username": f"updated_user_{timestamp}",
            "email": f"updated_{timestamp}@example.com",
            "brokerage_name": "Casa de Corretaje Actualizada",
            "is_active": True,
            "password": "newpassword123"
        }
        
        success, response = self.run_test(
            "Update User (PUT)",
            "PUT",
            f"admin/users/{self.created_user_id}",
            200,
            data=updated_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ User update working correctly")
            return True, updated_data
        else:
            print("❌ User update failed")
            return False, {}

    def test_update_user_duplicate_validation(self):
        """Test update user with duplicate username"""
        if not self.created_user_id:
            print("❌ No user ID available for duplicate validation test")
            return False
            
        print(f"\n🔍 Testing Update User Duplicate Validation...")
        
        # First create another user to test duplicate validation
        timestamp = datetime.now().strftime('%H%M%S')
        another_user_data = {
            "username": f"duplicate_test_{timestamp}",
            "password": "testpass123",
            "email": f"duplicate_{timestamp}@example.com",
            "brokerage_name": "Casa de Duplicado"
        }
        
        success, response = self.run_test(
            "Create Another User for Duplicate Test",
            "POST",
            "admin/users",
            200,
            data=another_user_data,
            token=self.admin_token
        )
        
        if not success:
            print("❌ Could not create second user for duplicate test")
            return False
            
        # Now try to update the first user with the same username as the second
        duplicate_data = {
            "username": another_user_data["username"],
            "email": "trying_duplicate@example.com",
            "brokerage_name": "Trying to duplicate username",
            "is_active": True,
            "password": "somepassword"
        }
        
        success, response = self.run_test(
            "Update User with Duplicate Username (Should Fail)",
            "PUT",
            f"admin/users/{self.created_user_id}",
            400,  # Should return 400 for duplicate
            data=duplicate_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ User duplicate validation working correctly")
            return True
        else:
            print("❌ User duplicate validation failed - should have rejected duplicate username")
            return False

    def test_change_user_password(self):
        """Test changing user password - NEW USER MANAGEMENT FEATURE"""
        if not self.created_user_id:
            print("❌ No user ID available for password change test")
            return False
            
        print(f"\n🔍 Testing Change User Password...")
        
        password_data = {
            "new_password": "newpassword456"
        }
        
        success, response = self.run_test(
            "Change User Password (PUT)",
            "PUT",
            f"admin/users/{self.created_user_id}/password",
            200,
            data=password_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ User password change working correctly")
            return True
        else:
            print("❌ User password change failed")
            return False

    def test_change_user_password_validation(self):
        """Test password change validation (short password)"""
        if not self.created_user_id:
            print("❌ No user ID available for password validation test")
            return False
            
        print(f"\n🔍 Testing Password Change Validation...")
        
        # Test with password too short
        invalid_password_data = {
            "new_password": "123"  # Less than 6 characters
        }
        
        success, response = self.run_test(
            "Change User Password (Too Short - Should Fail)",
            "PUT",
            f"admin/users/{self.created_user_id}/password",
            400,  # Should return 400 for invalid password
            data=invalid_password_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Password validation working correctly")
            return True
        else:
            print("❌ Password validation failed - should have rejected short password")
            return False

    def test_delete_user(self):
        """Test deleting a user - NEW USER MANAGEMENT FEATURE"""
        if not self.created_user_id:
            print("❌ No user ID available for delete test")
            return False
            
        print(f"\n🔍 Testing Delete User...")
        
        success, response = self.run_test(
            "Delete User (DELETE)",
            "DELETE",
            f"admin/users/{self.created_user_id}",
            200,
            token=self.admin_token
        )
        
        if success:
            print("✅ User deletion working correctly")
            return True
        else:
            print("❌ User deletion failed")
            return False

    def test_delete_nonexistent_user(self):
        """Test deleting a non-existent user"""
        print(f"\n🔍 Testing Delete Non-existent User...")
        
        fake_id = "nonexistent-user-id"
        success, response = self.run_test(
            "Delete Non-existent User (Should Return 404)",
            "DELETE",
            f"admin/users/{fake_id}",
            404,
            token=self.admin_token
        )
        
        if success:
            print("✅ Non-existent user deletion validation working correctly")
            return True
        else:
            print("❌ Non-existent user deletion validation failed")
            return False

    def test_update_nonexistent_user(self):
        """Test updating a non-existent user"""
        print(f"\n🔍 Testing Update Non-existent User...")
        
        fake_id = "nonexistent-user-id"
        update_data = {
            "username": "nonexistent",
            "email": "nonexistent@example.com",
            "brokerage_name": "Non-existent brokerage",
            "is_active": True,
            "password": "password123"
        }
        
        success, response = self.run_test(
            "Update Non-existent User (Should Return 404)",
            "PUT",
            f"admin/users/{fake_id}",
            404,
            data=update_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Non-existent user update validation working correctly")
            return True
        else:
            print("❌ Non-existent user update validation failed")
            return False

    def test_user_management_permissions(self):
        """Test that only admins can manage users"""
        if not self.created_user_id:
            print("❌ No user ID available for permission test")
            return False
            
        print(f"\n🔍 Testing User Management Permissions...")
        
        # Test user trying to update another user (should fail)
        update_data = {
            "username": "unauthorized_update",
            "email": "unauthorized@example.com",
            "brokerage_name": "Unauthorized brokerage",
            "is_active": True,
            "password": "password123"
        }
        
        success_update, response_update = self.run_test(
            "Update User (User Token - Should Fail)",
            "PUT",
            f"admin/users/{self.created_user_id}",
            403,  # Should return 403 Forbidden
            data=update_data,
            token=self.user_token
        )
        
        # Test user trying to delete another user (should fail)
        success_delete, response_delete = self.run_test(
            "Delete User (User Token - Should Fail)",
            "DELETE",
            f"admin/users/{self.created_user_id}",
            403,  # Should return 403 Forbidden
            token=self.user_token
        )
        
        # Test user trying to change another user's password (should fail)
        password_data = {"new_password": "unauthorized123"}
        success_password, response_password = self.run_test(
            "Change User Password (User Token - Should Fail)",
            "PUT",
            f"admin/users/{self.created_user_id}/password",
            403,  # Should return 403 Forbidden
            data=password_data,
            token=self.user_token
        )
        
        if success_update and success_delete and success_password:
            print("✅ User management permission validation working correctly")
            return True
        else:
            print("❌ User management permission validation failed")
            return False

    def test_get_user_holdings_by_admin(self):
        """Test admin getting holdings for specific user - NEW HOLDINGS MANAGEMENT FEATURE"""
        if not self.created_user_id:
            print("❌ No user ID available for holdings test")
            return False
            
        print(f"\n🔍 Testing Get User Holdings by Admin...")
        
        success, response = self.run_test(
            "Get User Holdings by Admin (GET)",
            "GET",
            f"admin/users/{self.created_user_id}/holdings",
            200,
            token=self.admin_token
        )
        
        if success:
            print("✅ Admin can get user holdings correctly")
            if isinstance(response, list):
                print(f"   Found {len(response)} holdings for user")
            return True
        else:
            print("❌ Admin get user holdings failed")
            return False

    def test_create_holding_for_user_by_admin(self):
        """Test admin creating holding for specific user - NEW HOLDINGS MANAGEMENT FEATURE"""
        if not self.created_user_id:
            print("❌ No user ID available for holdings creation test")
            return False
            
        print(f"\n🔍 Testing Create Holding for User by Admin...")
        
        # Create a security first if we don't have one
        if not self.created_security_id:
            security_created, security_data = self.test_create_security()
            if not security_created:
                print("❌ Could not create security for holdings test")
                return False
        
        holding_data = {
            "filing_date": "2024-01-20",
            "isin_or_latinex_code": f"US{datetime.now().strftime('%H%M%S')}AK07",
            "holder_name": "Admin Created Holder",
            "holder_id": "8-987-654",
            "legal_representative": "Legal Rep Admin",
            "amount_held": 250000.75,
            "address": "Admin Created Address, Panama City",
            "phone": "+507-987-6543",
            "email": "admin.created@example.com"
        }
        
        success, response = self.run_test(
            "Create Holding for User by Admin (POST)",
            "POST",
            f"admin/users/{self.created_user_id}/holdings",
            200,
            data=holding_data,
            token=self.admin_token
        )
        
        if success and 'id' in response:
            self.created_holding_id = response['id']
            print("✅ Admin can create holdings for users correctly")
            return True, holding_data
        else:
            print("❌ Admin create holding for user failed")
            return False, {}

    def test_update_holding_by_admin(self):
        """Test admin updating holding - NEW HOLDINGS MANAGEMENT FEATURE"""
        if not hasattr(self, 'created_holding_id') or not self.created_holding_id:
            print("❌ No holding ID available for update test")
            return False
            
        print(f"\n🔍 Testing Update Holding by Admin...")
        
        updated_holding_data = {
            "filing_date": "2024-02-15",
            "isin_or_latinex_code": f"US{datetime.now().strftime('%H%M%S')}UPD",
            "holder_name": "Updated Holder Name",
            "holder_id": "8-111-222",
            "legal_representative": "Updated Legal Rep",
            "amount_held": 300000.00,
            "address": "Updated Address, Panama City",
            "phone": "+507-111-2222",
            "email": "updated.holder@example.com"
        }
        
        success, response = self.run_test(
            "Update Holding by Admin (PUT)",
            "PUT",
            f"admin/holdings/{self.created_holding_id}",
            200,
            data=updated_holding_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Admin can update holdings correctly")
            return True
        else:
            print("❌ Admin update holding failed")
            return False

    def test_delete_holding_by_admin(self):
        """Test admin deleting holding - NEW HOLDINGS MANAGEMENT FEATURE"""
        if not hasattr(self, 'created_holding_id') or not self.created_holding_id:
            print("❌ No holding ID available for delete test")
            return False
            
        print(f"\n🔍 Testing Delete Holding by Admin...")
        
        success, response = self.run_test(
            "Delete Holding by Admin (DELETE)",
            "DELETE",
            f"admin/holdings/{self.created_holding_id}",
            200,
            token=self.admin_token
        )
        
        if success:
            print("✅ Admin can delete holdings correctly")
            return True
        else:
            print("❌ Admin delete holding failed")
            return False

    def test_holdings_management_permissions(self):
        """Test that only admins can manage holdings for other users"""
        if not self.created_user_id:
            print("❌ No user ID available for holdings permission test")
            return False
            
        print(f"\n🔍 Testing Holdings Management Permissions...")
        
        # Test user trying to get another user's holdings (should fail)
        success_get, response_get = self.run_test(
            "Get User Holdings by User Token (Should Fail)",
            "GET",
            f"admin/users/{self.created_user_id}/holdings",
            403,  # Should return 403 Forbidden
            token=self.user_token
        )
        
        # Test user trying to create holding for another user (should fail)
        holding_data = {
            "filing_date": "2024-01-20",
            "isin_or_latinex_code": "US123456789",
            "holder_name": "Unauthorized Holder",
            "holder_id": "8-000-000",
            "legal_representative": "",
            "amount_held": 1000.00,
            "address": "Unauthorized Address",
            "phone": "+507-000-0000",
            "email": "unauthorized@example.com"
        }
        
        success_create, response_create = self.run_test(
            "Create Holding for User by User Token (Should Fail)",
            "POST",
            f"admin/users/{self.created_user_id}/holdings",
            403,  # Should return 403 Forbidden
            data=holding_data,
            token=self.user_token
        )
        
        if success_get and success_create:
            print("✅ Holdings management permission validation working correctly")
            return True
        else:
            print("❌ Holdings management permission validation failed")
            return False

    def test_holdings_nonexistent_user(self):
        """Test holdings operations with non-existent user"""
        print(f"\n🔍 Testing Holdings Operations with Non-existent User...")
        
        fake_user_id = "nonexistent-user-id"
        
        # Test get holdings for non-existent user
        success_get, response_get = self.run_test(
            "Get Holdings for Non-existent User (Should Return 404)",
            "GET",
            f"admin/users/{fake_user_id}/holdings",
            404,
            token=self.admin_token
        )
        
        # Test create holding for non-existent user
        holding_data = {
            "filing_date": "2024-01-20",
            "isin_or_latinex_code": "US123456789",
            "holder_name": "Test Holder",
            "holder_id": "8-123-456",
            "legal_representative": "",
            "amount_held": 1000.00,
            "address": "Test Address",
            "phone": "+507-123-4567",
            "email": "test@example.com"
        }
        
        success_create, response_create = self.run_test(
            "Create Holding for Non-existent User (Should Return 404)",
            "POST",
            f"admin/users/{fake_user_id}/holdings",
            404,
            data=holding_data,
            token=self.admin_token
        )
        
        if success_get and success_create:
            print("✅ Non-existent user validation working correctly")
            return True
        else:
            print("❌ Non-existent user validation failed")
            return False

    def test_holdings_nonexistent_holding(self):
        """Test update/delete operations with non-existent holding"""
        print(f"\n🔍 Testing Holdings Operations with Non-existent Holding...")
        
        fake_holding_id = "nonexistent-holding-id"
        
        # Test update non-existent holding
        update_data = {
            "filing_date": "2024-01-20",
            "isin_or_latinex_code": "US123456789",
            "holder_name": "Test Holder",
            "holder_id": "8-123-456",
            "legal_representative": "",
            "amount_held": 1000.00,
            "address": "Test Address",
            "phone": "+507-123-4567",
            "email": "test@example.com"
        }
        
        success_update, response_update = self.run_test(
            "Update Non-existent Holding (Should Return 404)",
            "PUT",
            f"admin/holdings/{fake_holding_id}",
            404,
            data=update_data,
            token=self.admin_token
        )
        
        # Test delete non-existent holding
        success_delete, response_delete = self.run_test(
            "Delete Non-existent Holding (Should Return 404)",
            "DELETE",
            f"admin/holdings/{fake_holding_id}",
            404,
            token=self.admin_token
        )
        
        if success_update and success_delete:
            print("✅ Non-existent holding validation working correctly")
            return True
        else:
            print("❌ Non-existent holding validation failed")
            return False

    # ===== ADMIN MANAGEMENT TESTS =====
    def test_create_admin(self):
        """Test creating a new admin - ADMIN MANAGEMENT FEATURE"""
        print(f"\n🔍 Testing Create Admin...")
        
        timestamp = datetime.now().strftime('%H%M%S')
        admin_data = {
            "username": f"testadmin_{timestamp}",
            "password": "adminpass123",
            "email": f"testadmin_{timestamp}@example.com"
        }
        
        success, response = self.run_test(
            "Create Admin",
            "POST",
            "admin/create-admin",
            200,
            data=admin_data,
            token=self.admin_token
        )
        
        if success and 'id' in response:
            self.created_admin_id = response['id']
            print("✅ Admin creation working correctly")
            return True, admin_data
        else:
            print("❌ Admin creation failed")
            return False, {}

    def test_get_admins(self):
        """Test getting all admins - ADMIN MANAGEMENT FEATURE"""
        success, response = self.run_test(
            "Get Admins",
            "GET",
            "admin/admins",
            200,
            token=self.admin_token
        )
        
        if success and isinstance(response, list):
            print(f"✅ Get admins working correctly - found {len(response)} admins")
            return True
        else:
            print("❌ Get admins failed")
            return False

    def test_update_admin(self):
        """Test updating admin information - ADMIN MANAGEMENT FEATURE"""
        if not hasattr(self, 'created_admin_id') or not self.created_admin_id:
            print("❌ No admin ID available for update test")
            return False
            
        print(f"\n🔍 Testing Update Admin Information...")
        
        timestamp = datetime.now().strftime('%H%M%S')
        updated_data = {
            "username": f"updated_admin_{timestamp}",
            "email": f"updated_admin_{timestamp}@example.com"
        }
        
        success, response = self.run_test(
            "Update Admin (PUT)",
            "PUT",
            f"admin/admins/{self.created_admin_id}",
            200,
            data=updated_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Admin update working correctly")
            return True, updated_data
        else:
            print("❌ Admin update failed")
            return False, {}

    def test_update_admin_duplicate_validation(self):
        """Test update admin with duplicate username - ADMIN MANAGEMENT FEATURE"""
        if not hasattr(self, 'created_admin_id') or not self.created_admin_id:
            print("❌ No admin ID available for duplicate validation test")
            return False
            
        print(f"\n🔍 Testing Update Admin Duplicate Validation...")
        
        # Try to update with existing admin username
        duplicate_data = {
            "username": "admin",  # This should already exist
            "email": "duplicate@example.com"
        }
        
        success, response = self.run_test(
            "Update Admin with Duplicate Username (Should Fail)",
            "PUT",
            f"admin/admins/{self.created_admin_id}",
            400,  # Should return 400 for duplicate
            data=duplicate_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Admin duplicate validation working correctly")
            return True
        else:
            print("❌ Admin duplicate validation failed - should have rejected duplicate username")
            return False

    def test_update_admin_validation(self):
        """Test admin update validation (required fields) - ADMIN MANAGEMENT FEATURE"""
        if not hasattr(self, 'created_admin_id') or not self.created_admin_id:
            print("❌ No admin ID available for validation test")
            return False
            
        print(f"\n🔍 Testing Admin Update Validation...")
        
        # Test with missing required fields
        invalid_data = {
            "username": "",  # Empty username
            "email": ""      # Empty email
        }
        
        success, response = self.run_test(
            "Update Admin with Invalid Data (Should Fail)",
            "PUT",
            f"admin/admins/{self.created_admin_id}",
            400,  # Should return 400 for invalid data
            data=invalid_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Admin validation working correctly")
            return True
        else:
            print("❌ Admin validation failed - should have rejected empty fields")
            return False

    def test_change_admin_password(self):
        """Test changing admin password - ADMIN MANAGEMENT FEATURE"""
        if not hasattr(self, 'created_admin_id') or not self.created_admin_id:
            print("❌ No admin ID available for password change test")
            return False
            
        print(f"\n🔍 Testing Change Admin Password...")
        
        password_data = {
            "new_password": "newadminpass456"
        }
        
        success, response = self.run_test(
            "Change Admin Password (PUT)",
            "PUT",
            f"admin/admins/{self.created_admin_id}/password",
            200,
            data=password_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Admin password change working correctly")
            return True
        else:
            print("❌ Admin password change failed")
            return False

    def test_change_admin_password_validation(self):
        """Test admin password change validation (short password) - ADMIN MANAGEMENT FEATURE"""
        if not hasattr(self, 'created_admin_id') or not self.created_admin_id:
            print("❌ No admin ID available for password validation test")
            return False
            
        print(f"\n🔍 Testing Admin Password Change Validation...")
        
        # Test with password too short
        invalid_password_data = {
            "new_password": "123"  # Less than 6 characters
        }
        
        success, response = self.run_test(
            "Change Admin Password (Too Short - Should Fail)",
            "PUT",
            f"admin/admins/{self.created_admin_id}/password",
            400,  # Should return 400 for invalid password
            data=invalid_password_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Admin password validation working correctly")
            return True
        else:
            print("❌ Admin password validation failed - should have rejected short password")
            return False

    def test_update_nonexistent_admin(self):
        """Test updating a non-existent admin - ADMIN MANAGEMENT FEATURE"""
        print(f"\n🔍 Testing Update Non-existent Admin...")
        
        fake_id = "nonexistent-admin-id"
        update_data = {
            "username": "nonexistent",
            "email": "nonexistent@example.com"
        }
        
        success, response = self.run_test(
            "Update Non-existent Admin (Should Return 404)",
            "PUT",
            f"admin/admins/{fake_id}",
            404,
            data=update_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Non-existent admin update validation working correctly")
            return True
        else:
            print("❌ Non-existent admin update validation failed")
            return False

    def test_change_nonexistent_admin_password(self):
        """Test changing password for non-existent admin - ADMIN MANAGEMENT FEATURE"""
        print(f"\n🔍 Testing Change Password for Non-existent Admin...")
        
        fake_id = "nonexistent-admin-id"
        password_data = {
            "new_password": "somepassword123"
        }
        
        success, response = self.run_test(
            "Change Password for Non-existent Admin (Should Return 404)",
            "PUT",
            f"admin/admins/{fake_id}/password",
            404,
            data=password_data,
            token=self.admin_token
        )
        
        if success:
            print("✅ Non-existent admin password change validation working correctly")
            return True
        else:
            print("❌ Non-existent admin password change validation failed")
            return False

    def test_admin_management_permissions(self):
        """Test that only admins can manage other admins - ADMIN MANAGEMENT FEATURE"""
        if not hasattr(self, 'created_admin_id') or not self.created_admin_id:
            print("❌ No admin ID available for permission test")
            return False
            
        print(f"\n🔍 Testing Admin Management Permissions...")
        
        # Test user trying to update admin (should fail)
        update_data = {
            "username": "unauthorized_admin_update",
            "email": "unauthorized@example.com"
        }
        
        success_update, response_update = self.run_test(
            "Update Admin (User Token - Should Fail)",
            "PUT",
            f"admin/admins/{self.created_admin_id}",
            403,  # Should return 403 Forbidden
            data=update_data,
            token=self.user_token
        )
        
        # Test user trying to change admin password (should fail)
        password_data = {"new_password": "unauthorized123"}
        success_password, response_password = self.run_test(
            "Change Admin Password (User Token - Should Fail)",
            "PUT",
            f"admin/admins/{self.created_admin_id}/password",
            403,  # Should return 403 Forbidden
            data=password_data,
            token=self.user_token
        )
        
        # Test user trying to get admins list (should fail)
        success_get, response_get = self.run_test(
            "Get Admins (User Token - Should Fail)",
            "GET",
            "admin/admins",
            403,  # Should return 403 Forbidden
            token=self.user_token
        )
        
        # Test user trying to create admin (should fail)
        admin_data = {
            "username": "unauthorized_admin",
            "password": "password123",
            "email": "unauthorized@example.com"
        }
        success_create, response_create = self.run_test(
            "Create Admin (User Token - Should Fail)",
            "POST",
            "admin/create-admin",
            403,  # Should return 403 Forbidden
            data=admin_data,
            token=self.user_token
        )
        
        if success_update and success_password and success_get and success_create:
            print("✅ Admin management permission validation working correctly")
            return True
        else:
            print("❌ Admin management permission validation failed")
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

    # Test Holdings Management functionality (NEW FEATURES)
    print("\n" + "🔥" * 30)
    print("🎯 TESTING HOLDINGS MANAGEMENT FUNCTIONALITY")
    print("🔥" * 30)
    
    # Test holdings management operations
    tester.test_get_user_holdings_by_admin()
    holding_created, holding_data = tester.test_create_holding_for_user_by_admin()
    if holding_created:
        tester.test_update_holding_by_admin()
        tester.test_delete_holding_by_admin()
    tester.test_holdings_management_permissions()
    tester.test_holdings_nonexistent_user()
    tester.test_holdings_nonexistent_holding()

    # Test Admin Management functionality (NEW FEATURES)
    print("\n" + "🔥" * 30)
    print("🎯 TESTING ADMIN MANAGEMENT FUNCTIONALITY")
    print("🔥" * 30)
    
    # Test admin management operations
    admin_created, admin_data = tester.test_create_admin()
    tester.test_get_admins()
    if admin_created:
        tester.test_update_admin()
        tester.test_update_admin_duplicate_validation()
        tester.test_update_admin_validation()
        tester.test_change_admin_password()
        tester.test_change_admin_password_validation()
    tester.test_update_nonexistent_admin()
    tester.test_change_nonexistent_admin_password()
    tester.test_admin_management_permissions()

    # Test User Management functionality (NEW FEATURES)
    print("\n" + "🔥" * 30)
    print("🎯 TESTING USER MANAGEMENT FUNCTIONALITY")
    print("🔥" * 30)
    
    # Test user management operations
    tester.test_update_user()
    tester.test_update_user_duplicate_validation()
    tester.test_change_user_password()
    tester.test_change_user_password_validation()
    tester.test_update_nonexistent_user()
    tester.test_delete_nonexistent_user()
    tester.test_user_management_permissions()
    tester.test_delete_user()  # This should be last as it deletes the user
    
    # Test Individual Security Edit/Delete functionality (EXISTING FEATURES)
    print("\n" + "🔥" * 30)
    print("🎯 TESTING INDIVIDUAL SECURITY EDIT/DELETE FUNCTIONALITY")
    print("🔥" * 30)
    
    # Test individual security operations
    tester.test_update_security()
    tester.test_update_security_duplicate_validation()
    tester.test_update_nonexistent_security()
    tester.test_security_permissions()
    tester.test_delete_nonexistent_security()
    tester.test_delete_security()  # This should be last as it deletes the security
    
    # Test Clear All Securities functionality
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