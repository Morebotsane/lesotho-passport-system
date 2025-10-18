# test_auth.py
from app.core.security import get_password_hash, verify_password, create_access_token, verify_token

def test_password_hashing():
    print("🔒 Testing password hashing...")
    password = "TestPassword123!"
    hashed = get_password_hash(password)
    
    print(f"   Original: {password}")
    print(f"   Hashed: {hashed[:50]}...")
    
    # Test verification
    is_valid = verify_password(password, hashed)
    print(f"   ✅ Verification: {is_valid}")
    
    # Test wrong password
    wrong_valid = verify_password("WrongPassword123!", hashed)
    print(f"   ❌ Wrong password: {wrong_valid}")

def test_jwt_tokens():
    print("\n🎫 Testing JWT tokens...")
    user_id = "12345"
    
    # Create token
    token = create_access_token(user_id)
    print(f"   Token created: {token[:50]}...")
    
    # Verify token
    decoded_user_id = verify_token(token)
    print(f"   ✅ Decoded user ID: {decoded_user_id}")
    
    # Test invalid token
    invalid = verify_token("invalid.token.here")
    print(f"   ❌ Invalid token result: {invalid}")

if __name__ == "__main__":
    test_password_hashing()
    test_jwt_tokens()