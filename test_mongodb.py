#!/usr/bin/env python3
"""
MongoDB Connection Diagnostic Tool
Run this script to test your MongoDB connection before deploying
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError
import sys

def test_mongodb_connection(mongo_uri):
    """Test MongoDB connection with detailed error reporting"""
    
    print("=" * 70)
    print("🔍 MongoDB Connection Diagnostic Tool")
    print("=" * 70)
    print()
    
    # Step 1: Validate URI format
    print("📋 Step 1: Validating Connection String Format")
    print("-" * 70)
    
    if not mongo_uri:
        print("❌ MONGO_URI is empty or not set!")
        print("\n💡 Solution:")
        print("   1. Set the MONGO_URI environment variable")
        print("   2. Or edit this script and paste your URI directly")
        return False
    
    # Check for common mistakes
    if "<password>" in mongo_uri:
        print("❌ You forgot to replace <password> with your actual password!")
        print("\n💡 Solution:")
        print("   Replace <password> in your connection string with the real password")
        return False
    
    if not mongo_uri.startswith(("mongodb://", "mongodb+srv://")):
        print("❌ Invalid URI format! Must start with mongodb:// or mongodb+srv://")
        return False
    
    # Mask password for display
    display_uri = mongo_uri
    if "@" in mongo_uri:
        parts = mongo_uri.split("@")
        if "://" in parts[0]:
            credentials = parts[0].split("://")[1]
            if ":" in credentials:
                username = credentials.split(":")[0]
                display_uri = mongo_uri.replace(credentials, f"{username}:****")
    
    print(f"✅ URI format looks valid")
    print(f"📍 Connection string: {display_uri}")
    print()
    
    # Step 2: Test basic connection
    print("📋 Step 2: Testing Connection")
    print("-" * 70)
    
    try:
        print("⏳ Attempting to connect (timeout: 10 seconds)...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        
        # Force connection attempt
        client.admin.command('ping')
        
        print("✅ Connection successful!")
        print()
        
        # Step 3: Test database access
        print("📋 Step 3: Testing Database Access")
        print("-" * 70)
        
        db = client['university_db']
        print(f"✅ Can access database: university_db")
        
        # Step 4: Test collection access
        print()
        print("📋 Step 4: Testing Collection Access")
        print("-" * 70)
        
        students_col = db['students']
        print(f"✅ Can access collection: students")
        
        # Step 5: Test write permissions
        print()
        print("📋 Step 5: Testing Write Permissions")
        print("-" * 70)
        
        test_doc = {
            'usn': 'TEST_USN_123',
            'name': 'Test Student',
            'test': True
        }
        
        result = students_col.insert_one(test_doc)
        print(f"✅ Can write to database (inserted ID: {result.inserted_id})")
        
        # Clean up test document
        students_col.delete_one({'usn': 'TEST_USN_123'})
        print(f"✅ Can delete from database")
        
        # Step 6: Check existing data
        print()
        print("📋 Step 6: Checking Existing Data")
        print("-" * 70)
        
        count = students_col.count_documents({})
        print(f"📊 Current student records: {count}")
        
        if count > 0:
            sample = students_col.find_one({}, {'_id': 0, 'usn': 1, 'name': 1})
            print(f"📝 Sample record: {sample}")
        
        print()
        print("=" * 70)
        print("✅ ALL TESTS PASSED! Your MongoDB connection is working perfectly!")
        print("=" * 70)
        print()
        print("🚀 You're ready to deploy to Render!")
        print()
        
        client.close()
        return True
        
    except ServerSelectionTimeoutError as e:
        print("❌ CONNECTION TIMEOUT!")
        print()
        print("⚠️  Possible causes:")
        print("   1. Network Access not configured in MongoDB Atlas")
        print("   2. Incorrect cluster address")
        print("   3. Firewall blocking the connection")
        print()
        print("💡 Solutions:")
        print("   1. Go to MongoDB Atlas → Security → Network Access")
        print("   2. Click 'Add IP Address'")
        print("   3. Click 'Allow Access from Anywhere' (0.0.0.0/0)")
        print("   4. Wait 1-2 minutes for changes to take effect")
        print()
        print(f"🔍 Error details: {str(e)}")
        return False
        
    except ConfigurationError as e:
        print("❌ CONFIGURATION ERROR!")
        print()
        print("⚠️  Your connection string has a configuration problem")
        print()
        print("💡 Common issues:")
        print("   1. Special characters in password need URL encoding")
        print("   2. Invalid cluster name")
        print("   3. Wrong authentication database")
        print()
        print("🔧 If your password has special characters (@, #, $, etc):")
        print("   Use this tool to encode it: https://www.urlencoder.org/")
        print()
        print(f"🔍 Error details: {str(e)}")
        return False
        
    except ConnectionFailure as e:
        print("❌ AUTHENTICATION FAILED!")
        print()
        print("⚠️  Username or password is incorrect")
        print()
        print("💡 Solutions:")
        print("   1. Go to MongoDB Atlas → Security → Database Access")
        print("   2. Verify the username exists")
        print("   3. Click 'Edit' → 'Edit Password' to reset password")
        print("   4. Make sure user has 'readWrite' permissions")
        print()
        print(f"🔍 Error details: {str(e)}")
        return False
        
    except Exception as e:
        print("❌ UNEXPECTED ERROR!")
        print()
        print(f"🔍 Error type: {type(e).__name__}")
        print(f"🔍 Error details: {str(e)}")
        print()
        print("💡 Try:")
        print("   1. Check if your MongoDB Atlas cluster is running")
        print("   2. Verify your connection string is correct")
        print("   3. Check MongoDB Atlas status page")
        return False

def main():
    print("\n")
    
    # Try to get MONGO_URI from environment variable
    mongo_uri = os.environ.get('MONGO_URI')
    
    # If not in environment, prompt user
    if not mongo_uri:
        print("⚠️  MONGO_URI environment variable not found")
        print()
        print("Please paste your MongoDB connection string here:")
        print("(or press Ctrl+C to exit and set MONGO_URI environment variable)")
        print()
        try:
            mongo_uri = input("MongoDB URI: ").strip()
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            sys.exit(0)
    
    if not mongo_uri:
        print("❌ No MongoDB URI provided. Exiting.")
        sys.exit(1)
    
    # Run the diagnostic
    success = test_mongodb_connection(mongo_uri)
    
    print()
    if success:
        sys.exit(0)
    else:
        print("=" * 70)
        print("❌ MONGODB CONNECTION FAILED")
        print("=" * 70)
        print()
        print("📚 For more help, see:")
        print("   - DEPLOYMENT_GUIDE.md (Step 1: MongoDB Atlas setup)")
        print("   - TROUBLESHOOTING.md (MongoDB connection section)")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()