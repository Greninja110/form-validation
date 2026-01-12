import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# ===============================
# CONFIGURATION
# ===============================
WEBSITE_URL = "http://localhost:8080"

# ===============================
# FIELD CONFIGURATION
# Enable/Disable fields to test by commenting out
# ===============================
FIELDS_TO_TEST = {
    'name': True,           # Set to False or comment out to skip testing
    'age': True,
    'email': True,
    'password': True,
    'confirm_password': True,
    'dob': True,
    'gender': True,
    'address': True,
    'country': True,
    'phone': True,
    'otp': True
}

# ===============================
# FIELD ID MAPPING
# Update these IDs to match your form's HTML
# ===============================
FIELD_IDS = {
    'name': 'name',
    'age': 'age',
    'email': 'email',
    'password': 'password',
    'confirm_password': 'password_confirmation',  
    'dob': 'dob',
    'gender': {'male': 'male', 'female': 'female', 'other': 'other'},
    'address': 'address',
    'country': 'country',
    'phone': 'phone',
    'otp': ['otp1', 'otp2', 'otp3', 'otp4', 'otp5', 'otp6']  
}

# ===============================
# TEST DATA DEFINITIONS
# ===============================

# Name Tests
NAME = "abhijeet"
NAME_ALPHANUMERIC = "abhijeet123"
NAME_SPECIALCHARS = "abhijeet!@#"
NAME_EMPTY = ""
NAME_WITH_SPACE = "Abhijeet Sahoo"

NAME_TESTS = [
    (NAME, "Valid Name", True),
    (NAME_WITH_SPACE, "Name with Space", True),
    (NAME_ALPHANUMERIC, "Alphanumeric Name", False),
    (NAME_SPECIALCHARS, "Name with Special Characters", False),
    (NAME_EMPTY, "Empty Name", False)
]

# Age Tests
AGE_UNDERAGE = "15"
AGE_ADULT = "25"
AGE_INVALID = "150"
AGE_INVALID_NEGATIVE = "-5"
AGE_ZERO = "0"
AGE_ALPHABETIC = "twenty"
AGE_EMPTY = ""

AGE_TESTS = [
    (AGE_ADULT, "Valid Adult Age", True),
    (AGE_UNDERAGE, "Underage", False),
    (AGE_INVALID, "Invalid High Age", False),
    (AGE_INVALID_NEGATIVE, "Negative Age", False),
    (AGE_ZERO, "Zero Age", False),
    (AGE_ALPHABETIC, "Alphabetic Age", False),
    (AGE_EMPTY, "Empty Age", False)
]

# Email Tests
VALID_EMAIL = "abhijeetsahoo2452004@gmail.com"
INVALID_EMAIL = "invalidemail.com"
INVALID_EMAIL_2 = "test@"
INVALID_EMAIL_3 = "@gmail.com"

EMAIL_TESTS = [
    (VALID_EMAIL, "Valid Email", True),
    (INVALID_EMAIL, "Invalid Email (no @)", False),
    (INVALID_EMAIL_2, "Invalid Email (incomplete)", False),
    (INVALID_EMAIL_3, "Invalid Email (no username)", False),
    ("", "Empty Email", False)
]

# Password Tests
WEAK_PASSWORD = "12345678"
STRONG_PASSWORD = "Str0ngP@ssw0rd!23"
SMALL_PASSWORD = "123"
BIG_PASSWORD = "1234546789012345678901234567890"

PASSWORD_TESTS = [
    (STRONG_PASSWORD, "Strong Password", True),
    (WEAK_PASSWORD, "Weak Password", False),
    (SMALL_PASSWORD, "Short Password", False),
    (BIG_PASSWORD, "Very Long Password", False),
    ("", "Empty Password", False)
]

# Confirm Password Tests
CONFIRM_PASSWORD_TESTS = [
    (STRONG_PASSWORD, "Matching Password", True),
    ("DifferentPass123!", "Non-matching Password", False),
    ("", "Empty Confirm Password", False),
    (STRONG_PASSWORD[:-1], "Almost Matching Password", False),
]

# DOB Tests
DOB_VALID = "2000-05-15"
DOB_INVALID_FORMAT = "15-05-2000"
DOB_UNDERAGE = "2012-01-01"
DOB_ADULT = "2000-01-01"
DOB_OVERAGE = "1875-01-01"
DOB_FUTURE = "2027-01-01"
DOB_EMPTY = ""

DOB_TESTS = [
    (DOB_VALID, "Valid DOB", True),
    (DOB_ADULT, "Adult DOB", True),
    (DOB_INVALID_FORMAT, "Invalid Format DOB", False),
    (DOB_UNDERAGE, "Underage DOB", False),
    (DOB_OVERAGE, "Very Old DOB", False),
    (DOB_FUTURE, "Future DOB", False),
    (DOB_EMPTY, "Empty DOB", False)
]

# Address Tests
ADDRESS_VALID = "123 Main Street, Bangalore"
ADDRESS_EMPTY = ""

ADDRESS_TESTS = [
    (ADDRESS_VALID, "Valid Address", True),
    (ADDRESS_EMPTY, "Empty Address", False)
]

# Phone Tests
PHONE_VALID = "9876543210"
PHONE_INVALID = "12345abcde"
PHONE_SHORT = "12345"
PHONE_LONG = "12345678901234567890"
PHONE_SPECIAL = "98765-43210"
PHONE_EMPTY = ""

PHONE_TESTS = [
    (PHONE_VALID, "Valid Phone", True),
    (PHONE_INVALID, "Alphanumeric Phone", False),
    (PHONE_SHORT, "Short Phone", False),
    (PHONE_LONG, "Long Phone", False),
    (PHONE_SPECIAL, "Phone with Special Chars", False),
    (PHONE_EMPTY, "Empty Phone", False)
]

# OTP Tests
OTP_VALID = "123456"
OTP_SHORT = "123"
OTP_LONG = "1234567"
OTP_ALPHABETIC = "abcdef"
OTP_ALPHANUMERIC = "a1b2c3"
OTP_SPECIAL = "!@#$%^"
OTP_EMPTY = ""

OTP_TESTS = [
    (OTP_VALID, "Valid 6-digit OTP", True),
    (OTP_SHORT, "Short OTP", False),
    (OTP_LONG, "Long OTP", False),
    (OTP_ALPHABETIC, "Alphabetic OTP", False),
    (OTP_ALPHANUMERIC, "Alphanumeric OTP", False),
    (OTP_SPECIAL, "Special Characters OTP", False),
    (OTP_EMPTY, "Empty OTP", False)
]

# Gender options (no test array needed, just default value)
GENDER_DEFAULT = "male"

# Country options (no test array needed, just default value)
COUNTRY_DEFAULT = "India"

# ===============================
# TEST CLASS
# ===============================
class FormValidationTester:
    def __init__(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 5)
        self.test_results = []
        self.vulnerabilities = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_fields = []
        
    def navigate_to_form(self):
        """Navigate to the form page"""
        self.driver.get(WEBSITE_URL)
        time.sleep(1)
    
    def field_exists(self, field_id):
        """Check if a field exists on the page"""
        try:
            self.driver.find_element(By.ID, field_id)
            return True
        except NoSuchElementException:
            return False
    
    def fill_field(self, field_name, value):
        """Fill a single field with error handling"""
        try:
            field_id = FIELD_IDS.get(field_name)
            
            if field_name == 'gender':
                if value in field_id:
                    gender_id = field_id[value]
                    if self.field_exists(gender_id):
                        self.driver.find_element(By.ID, gender_id).click()
                return True
            
            elif field_name == 'country':
                if self.field_exists(field_id):
                    country_dropdown = Select(self.driver.find_element(By.ID, field_id))
                    country_dropdown.select_by_visible_text(value)
                return True
            
            elif field_name == 'otp':
                if isinstance(field_id, list):
                    otp_digits = list(value[:6])
                    for i, digit in enumerate(otp_digits):
                        if self.field_exists(field_id[i]):
                            self.driver.find_element(By.ID, field_id[i]).clear()
                            self.driver.find_element(By.ID, field_id[i]).send_keys(digit)
                    
                    for i in range(len(otp_digits), len(field_id)):
                        if self.field_exists(field_id[i]):
                            self.driver.find_element(By.ID, field_id[i]).clear()
                else:
                    if self.field_exists(field_id):
                        self.driver.find_element(By.ID, field_id).clear()
                        if value:
                            self.driver.find_element(By.ID, field_id).send_keys(value)
                return True
            
            else:
                if self.field_exists(field_id):
                    self.driver.find_element(By.ID, field_id).clear()
                    if value:
                        self.driver.find_element(By.ID, field_id).send_keys(value)
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Error filling field {field_name}: {str(e)}")
            return False
    
    def fill_form(self, **kwargs):
        """Fill the entire form with given data"""
        try:
            for field_name, value in kwargs.items():
                if FIELDS_TO_TEST.get(field_name, False):
                    self.fill_field(field_name, value)
            return True
        except Exception as e:
            print(f"Error filling form: {str(e)}")
            return False
    
    def submit_form(self):
        """Submit the form and check result"""
        try:
            submit_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Register') or contains(text(),'Submit')]"))
            )
            
            current_url = self.driver.current_url
            submit_btn.click()
            time.sleep(1.5)
            
            # Check if redirected or URL changed
            new_url = self.driver.current_url
            if new_url != current_url:
                return True, "Form submitted successfully"
            else:
                # Check for any validation messages or if form is still visible
                try:
                    # Check if form still exists (validation failed)
                    self.driver.find_element(By.TAG_NAME, "form")
                    return False, "Form submission blocked by validation"
                except NoSuchElementException:
                    # Form no longer exists, probably submitted
                    return True, "Form submitted successfully"
                    
        except TimeoutException:
            return False, "Submit button not clickable"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_default_values(self):
        """Get default valid values for all enabled fields"""
        defaults = {}
        
        if FIELDS_TO_TEST.get('name', False):
            defaults['name'] = NAME
        if FIELDS_TO_TEST.get('age', False):
            defaults['age'] = AGE_ADULT
        if FIELDS_TO_TEST.get('email', False):
            defaults['email'] = VALID_EMAIL
        if FIELDS_TO_TEST.get('password', False):
            defaults['password'] = STRONG_PASSWORD
        if FIELDS_TO_TEST.get('confirm_password', False):
            defaults['confirm_password'] = STRONG_PASSWORD
        if FIELDS_TO_TEST.get('dob', False):
            defaults['dob'] = DOB_VALID
        if FIELDS_TO_TEST.get('gender', False):
            defaults['gender'] = GENDER_DEFAULT
        if FIELDS_TO_TEST.get('address', False):
            defaults['address'] = ADDRESS_VALID
        if FIELDS_TO_TEST.get('country', False):
            defaults['country'] = COUNTRY_DEFAULT
        if FIELDS_TO_TEST.get('phone', False):
            defaults['phone'] = PHONE_VALID
        if FIELDS_TO_TEST.get('otp', False):
            defaults['otp'] = OTP_VALID
            
        return defaults
    
    def test_field(self, field_name, test_data_array, default_values):
        """Test a specific field with various inputs"""
        if not FIELDS_TO_TEST.get(field_name, False):
            print(f"\n⊘ Skipping {field_name.upper()} field (disabled in configuration)")
            self.skipped_fields.append(field_name)
            return
        
        print(f"\n{'='*60}")
        print(f"Testing {field_name.upper()} Field")
        print(f"{'='*60}")
        
        for test_value, test_description, should_pass in test_data_array:
            self.total_tests += 1
            self.navigate_to_form()
            
            # Update the field being tested
            test_values = default_values.copy()
            test_values[field_name] = test_value
            
            # Special handling for confirm_password
            if field_name == 'confirm_password':
                # Ensure password field has the value we're comparing against
                test_values['password'] = STRONG_PASSWORD
            
            # Fill form
            self.fill_form(**test_values)
            
            # Submit and check
            success, message = self.submit_form()
            
            # Determine test result
            if should_pass and success:
                result = "PASS ✓"
                self.passed_tests += 1
                status = "Expected: VALID | Actual: ACCEPTED"
            elif not should_pass and not success:
                result = "PASS ✓"
                self.passed_tests += 1
                status = "Expected: INVALID | Actual: REJECTED"
            elif should_pass and not success:
                result = "FAIL ✗"
                self.failed_tests += 1
                status = "Expected: VALID | Actual: REJECTED (False Negative)"
            else:
                result = "FAIL ✗"
                self.failed_tests += 1
                status = "Expected: INVALID | Actual: ACCEPTED (Vulnerability!)"
                self.vulnerabilities.append({
                    'field': field_name,
                    'input': test_value,
                    'description': test_description
                })
            
            # Log result
            test_result = {
                'field': field_name,
                'test': test_description,
                'input': test_value if test_value else "[EMPTY]",
                'expected': "VALID" if should_pass else "INVALID",
                'actual': "ACCEPTED" if success else "REJECTED",
                'result': result,
                'status': status
            }
            self.test_results.append(test_result)
            
            print(f"{result} | {field_name}: {test_description}")
            print(f"     Input: {test_value if test_value else '[EMPTY]'}")
            print(f"     {status}")
    
    def run_all_tests(self):
        """Run all field validation tests"""
        default_values = self.get_default_values()
        
        print("\n" + "="*60)
        print("ACTIVE FIELDS FOR TESTING")
        print("="*60)
        for field, enabled in FIELDS_TO_TEST.items():
            status = "✓ ENABLED" if enabled else "✗ DISABLED"
            print(f"{field.upper()}: {status}")
        
        # Test each field based on configuration
        if FIELDS_TO_TEST.get('name', False):
            self.test_field('name', NAME_TESTS, default_values)
        
        if FIELDS_TO_TEST.get('age', False):
            self.test_field('age', AGE_TESTS, default_values)
        
        if FIELDS_TO_TEST.get('email', False):
            self.test_field('email', EMAIL_TESTS, default_values)
        
        if FIELDS_TO_TEST.get('password', False):
            self.test_field('password', PASSWORD_TESTS, default_values)
        
        if FIELDS_TO_TEST.get('confirm_password', False):
            self.test_field('confirm_password', CONFIRM_PASSWORD_TESTS, default_values)
        
        if FIELDS_TO_TEST.get('dob', False):
            self.test_field('dob', DOB_TESTS, default_values)
        
        if FIELDS_TO_TEST.get('address', False):
            self.test_field('address', ADDRESS_TESTS, default_values)
        
        if FIELDS_TO_TEST.get('phone', False):
            self.test_field('phone', PHONE_TESTS, default_values)
        
        if FIELDS_TO_TEST.get('otp', False):
            self.test_field('otp', OTP_TESTS, default_values)
    
    def generate_report(self):
        """Generate detailed test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"form_validation_report_{timestamp}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            # Header
            f.write("="*80 + "\n")
            f.write("FORM VALIDATION TEST REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Website URL: {WEBSITE_URL}\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {self.total_tests}\n")
            f.write(f"Passed: {self.passed_tests} ({(self.passed_tests/self.total_tests*100):.2f}%)\n")
            f.write(f"Failed: {self.failed_tests} ({(self.failed_tests/self.total_tests*100):.2f}%)\n")
            
            # Fields tested
            f.write("\nFields Tested:\n")
            for field, enabled in FIELDS_TO_TEST.items():
                if enabled:
                    f.write(f"  ✓ {field.upper()}\n")
            
            if self.skipped_fields:
                f.write("\nFields Skipped:\n")
                for field in self.skipped_fields:
                    f.write(f"  ✗ {field.upper()}\n")
            
            f.write("="*80 + "\n\n")
            
            # Executive Summary
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-"*80 + "\n")
            if len(self.vulnerabilities) == 0:
                f.write("✓ No critical vulnerabilities found. All validations working correctly.\n")
            else:
                f.write(f"✗ CRITICAL: {len(self.vulnerabilities)} vulnerabilities found!\n")
                f.write("  The form accepts invalid data for the following fields:\n")
                for vuln in self.vulnerabilities:
                    f.write(f"  - {vuln['field'].upper()}: {vuln['description']}\n")
            f.write("\n")
            
            # Detailed Test Results
            f.write("DETAILED TEST RESULTS\n")
            f.write("-"*80 + "\n\n")
            
            current_field = None
            for result in self.test_results:
                if current_field != result['field']:
                    current_field = result['field']
                    f.write(f"\n{current_field.upper()} FIELD TESTS\n")
                    f.write("-"*80 + "\n")
                
                f.write(f"\n{result['result']} | Test: {result['test']}\n")
                f.write(f"   Input: {result['input']}\n")
                f.write(f"   Expected: {result['expected']} | Actual: {result['actual']}\n")
                f.write(f"   Status: {result['status']}\n")
            
            # Vulnerabilities Section
            f.write("\n" + "="*80 + "\n")
            f.write("SECURITY VULNERABILITIES\n")
            f.write("="*80 + "\n")
            if len(self.vulnerabilities) > 0:
                for i, vuln in enumerate(self.vulnerabilities, 1):
                    f.write(f"\nVulnerability #{i}:\n")
                    f.write(f"  Field: {vuln['field'].upper()}\n")
                    f.write(f"  Issue: {vuln['description']}\n")
                    f.write(f"  Invalid Input Accepted: {vuln['input']}\n")
            else:
                f.write("\n✓ No vulnerabilities detected.\n")
            
            # Recommendations
            f.write("\n" + "="*80 + "\n")
            f.write("RECOMMENDATIONS\n")
            f.write("="*80 + "\n")
            
            recommendations = []
            
            for vuln in self.vulnerabilities:
                if vuln['field'] == 'name':
                    if 'Alphanumeric' in vuln['description']:
                        recommendations.append("- NAME: Add validation to reject numeric characters")
                    if 'Special Characters' in vuln['description']:
                        recommendations.append("- NAME: Add validation to reject special characters")
                    if 'Empty' in vuln['description']:
                        recommendations.append("- NAME: Make field required (cannot be empty)")
                
                elif vuln['field'] == 'age':
                    if 'Underage' in vuln['description']:
                        recommendations.append("- AGE: Implement minimum age requirement (18+)")
                    if 'Invalid' in vuln['description'] or 'Negative' in vuln['description']:
                        recommendations.append("- AGE: Add range validation (18-120)")
                    if 'Alphabetic' in vuln['description']:
                        recommendations.append("- AGE: Restrict input to numeric values only")
                
                elif vuln['field'] == 'email':
                    recommendations.append("- EMAIL: Implement proper email format validation (RFC 5322)")
                
                elif vuln['field'] == 'password':
                    if 'Short' in vuln['description']:
                        recommendations.append("- PASSWORD: Enforce minimum length (8+ characters)")
                    if 'Weak' in vuln['description']:
                        recommendations.append("- PASSWORD: Require strong password (uppercase, lowercase, numbers, special chars)")
                
                elif vuln['field'] == 'confirm_password':
                    recommendations.append("- CONFIRM PASSWORD: Ensure password fields match before submission")
                
                elif vuln['field'] == 'phone':
                    if 'Alphanumeric' in vuln['description']:
                        recommendations.append("- PHONE: Restrict to numeric values only")
                    if 'Short' in vuln['description'] or 'Long' in vuln['description']:
                        recommendations.append("- PHONE: Enforce exact length (10 digits)")
                
                elif vuln['field'] == 'dob':
                    if 'Future' in vuln['description']:
                        recommendations.append("- DOB: Validate date is not in the future")
                    if 'Underage' in vuln['description']:
                        recommendations.append("- DOB: Ensure user is at least 18 years old")
                    if 'Format' in vuln['description']:
                        recommendations.append("- DOB: Use proper date picker (YYYY-MM-DD)")
                
                elif vuln['field'] == 'otp':
                    if 'Short' in vuln['description'] or 'Long' in vuln['description']:
                        recommendations.append("- OTP: Enforce exactly 6 digits")
                    if 'Alphabetic' in vuln['description'] or 'Alphanumeric' in vuln['description']:
                        recommendations.append("- OTP: Accept only numeric values")
            
            if recommendations:
                for rec in set(recommendations):
                    f.write(f"{rec}\n")
            else:
                f.write("✓ Form validation is working correctly. No improvements needed.\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("END OF REPORT\n")
            f.write("="*80 + "\n")
        
        print(f"\n\n{'='*60}")
        print(f"Report generated: {report_filename}")
        print(f"{'='*60}")
        
        return report_filename
    
    def close(self):
        """Close the browser"""
        self.driver.quit()

# ===============================
# MAIN EXECUTION
# ===============================
if __name__ == "__main__":
    print("="*60)
    print("FORM VALIDATION TESTING AUTOMATION")
    print("="*60)
    print(f"Target URL: {WEBSITE_URL}")
    print("Starting tests...\n")
    
    tester = FormValidationTester()
    
    try:
        tester.run_all_tests()
        report_file = tester.generate_report()
        
        print(f"\nTest Summary:")
        print(f"Total Tests: {tester.total_tests}")
        print(f"Passed: {tester.passed_tests}")
        print(f"Failed: {tester.failed_tests}")
        print(f"Vulnerabilities: {len(tester.vulnerabilities)}")
        print(f"\nDetailed report saved to: {report_file}")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        time.sleep(2)
        tester.close()
        print("\nTesting completed.")