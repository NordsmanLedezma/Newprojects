import requests
import json

# Login as admin
def get_admin_token():
    login_url = "https://bondregistry.preview.emergentagent.com/api/auth/login"
    login_data = {"username": "admin", "password": "admin123"}
    
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception("Failed to login")

# Get securities data
def get_securities(token):
    securities_url = "https://bondregistry.preview.emergentagent.com/api/admin/securities"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(securities_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to get securities")

def main():
    try:
        print("🔐 Logging in as admin...")
        token = get_admin_token()
        print("✅ Admin login successful")
        
        print("📊 Fetching securities data...")
        securities = get_securities(token)
        
        print(f"\n✅ SECURITIES TABLE SUCCESSFULLY LOADED!")
        print(f"📈 Total securities in database: {len(securities)}")
        
        # Group by type
        local_bonds = [s for s in securities if s["isin_code"] and s["isin_code"].startswith("PAL")]
        international_bonds = [s for s in securities if s["isin_code"] and s["isin_code"].startswith("US")]
        
        print(f"\n📋 BREAKDOWN:")
        print(f"   🇵🇦 Local Panama bonds (PAL codes): {len(local_bonds)}")
        print(f"   🌍 International bonds (US codes): {len(international_bonds)}")
        
        print(f"\n📝 SAMPLE SECURITIES (first 5):")
        for i, security in enumerate(securities[:5], 1):
            isin = security.get("isin_code", "")
            latinex = security.get("latinex_code", "")
            description = security.get("security_description", "")[:50] + "..." if len(security.get("security_description", "")) > 50 else security.get("security_description", "")
            coupon = security.get("coupon", "")
            print(f"   {i}. {isin} | {latinex} | {description} | {coupon}")
        
        print(f"\n🎯 TABLE LOADING STATUS: ✅ SUCCESSFUL")
        print(f"💡 To access the table:")
        print(f"   1. Login as admin (admin/admin123)")
        print(f"   2. Go to 'Panel de Administración'")
        print(f"   3. Click on 'Valores ISIN' tab")
        print(f"   4. You should see all {len(securities)} securities listed")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()