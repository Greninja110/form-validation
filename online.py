import asyncio
import re
import random
import string
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError
from urllib.parse import urlparse


# ===============================
# UNIQUE EMAIL GENERATOR 
# ===============================

def generate_unique_email():
    """
    Generates unique email like:
    test+hhmmssxyz@example.com
    """
    timestamp = datetime.now().strftime("%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=3))
    return f"test{timestamp}{random_suffix}@gmail.com"


#--------------------------------
# FORM SIGNATURE GENERATOR 
#--------------------------------

async def get_form_signature(page):
    """
    Creates a robust, interaction-based signature of the active form step.
    Enhanced to detect differences between email and OTP input forms.
    Works even when all steps exist in DOM but visibility changes.
    """
    return await page.evaluate("""
        () => {
            const isInteractable = (el) => {
                const s = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();

                return (
                    s.display !== 'none' &&
                    s.visibility !== 'hidden' &&
                    s.opacity !== '0' &&
                    !el.disabled &&
                    rect.width > 0 &&
                    rect.height > 0 &&
                    el.tabIndex !== -1 &&
                    !el.hasAttribute('aria-hidden')
                );
            };

            const inputs = Array.from(
                document.querySelectorAll('input, select, textarea')
            ).filter(el => 
                el.type !== 'hidden' && isInteractable(el)
            );

            const buttons = Array.from(
                document.querySelectorAll('button')
            ).filter(isInteractable);

            // Collect all visible text content (headings, labels, paragraphs)
            const visibleTexts = Array.from(
                document.querySelectorAll('h1, h2, h3, h4, h5, h6, label, p, span, div')
            )
            .filter(el => {
                const s = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return (
                    s.display !== 'none' &&
                    s.visibility !== 'hidden' &&
                    s.opacity !== '0' &&
                    rect.width > 0 &&
                    rect.height > 0 &&
                    el.innerText &&
                    el.innerText.trim().length > 0 &&
                    el.innerText.trim().length < 200 // Avoid capturing large blocks
                );
            })
            .map(el => el.innerText.trim().toLowerCase())
            .filter((text, index, self) => self.indexOf(text) === index); // Remove duplicates

            // Capture input field details with more precision
            const activeInputs = inputs.map(el => ({
                tag: el.tagName,
                type: el.type || '',
                name: el.name || '',
                id: el.id || '',
                placeholder: el.placeholder || '',
                maxlength: el.maxLength || null,
                pattern: el.pattern || '',
                inputmode: el.getAttribute('inputmode') || '',
                autocomplete: el.autocomplete || '',
                className: el.className || ''
            }));

            // Get button text with better formatting
            const buttonTexts = buttons.map(b => b.innerText.trim().toLowerCase());

            // Create a composite hash from all visible text
            const textHash = visibleTexts.join('|').substring(0, 500);

            return {
                active_input_count: activeInputs.length,
                active_inputs: activeInputs,
                active_button_texts: buttonTexts,
                visible_texts: visibleTexts.slice(0, 10), // First 10 unique texts
                text_hash: textHash,
                has_otp_indicators: visibleTexts.some(t => 
                    t.includes('otp') || 
                    t.includes('verify') || 
                    t.includes('code') ||
                    t.includes('6-digit') ||
                    t.includes('enter 6')
                ),
                has_email_indicators: visibleTexts.some(t => 
                    t.includes('email') || 
                    t.includes('welcome') ||
                    t.includes('detect if')
                ),
                form_container_ids: Array.from(
                    document.querySelectorAll('[id*="form"], [class*="form"], [id*="step"], [class*="step"]')
                )
                .filter(isInteractable)
                .map(el => el.id || el.className)
                .slice(0, 5)
            };
        }
    """)



#--------------------------------
# INLINE VALIDATION ERROR DETECTION 
#--------------------------------
async def detect_inline_validation_error(page):
    """
    Detects visible inline validation messages on the page
    """
    error_keywords = [
        "valid email",
        "invalid",
        "required",
        "please enter",
        "not valid",
        "error"
    ]

    texts = await page.evaluate("""
        () => {
            const elements = Array.from(
                document.querySelectorAll('p, span, div, small, label')
            ).filter(el => {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       el.innerText.trim().length > 0;
            });

            return elements.map(el => el.innerText.trim().toLowerCase());
        }
    """)

    for text in texts:
        for keyword in error_keywords:
            if keyword in text:
                return True, text

    return False, None


# ===============================
# CONFIGURATION 
# ===============================

CONFIG = {
    "url": "https://tiffinworld.com/auth/customer",
    # "submit_selector": "button[type=button]",
    "submit_selector": "button#continueBtn",
    "delay_between_tests": 2,
    "wait_after_submit": 5,

    # -------------------------------
    # SUCCESS DETECTION CONFIG
    # -------------------------------
    "success_detection": {
        "method_priority": [
            "url_change",
            "network_success",
            "success_message",
            "form_disappears"
        ],
        "success_url_keywords": [
            "success", "dashboard", "welcome", "thank", "verify", "home"
        ],
        "success_message_selectors": [
            ".alert-success",
            ".success",
            ".toast-success"
        ],
        "error_message_selectors": [
            ".alert-danger",
            ".error",
            ".invalid-feedback",
            ".toast-error"
        ]
    },

    # -------------------------------
    # FORM FIELDS (ENABLE / DISABLE)
    # -------------------------------
    "fields": {

        "full_name": {
            "selector": "input[name='name']",
            "type": "text",
            "enabled": False
        },

        "age": {
            "selector": "input[name='age']",
            "type": "numeric",
            "enabled": False
        },

        "email": {
            "selector": "input[name='email']:visible",
            "type": "email",
            "enabled": True
        },

        "password": {
            "selector": "input[name='password']",
            "type": "password",
            "enabled": False
        },

        "confirm_password": {
            "selector": "input[name='password_confirmation']",
            "type": "password_confirm",
            "enabled": False,
            "depends_on": "password"
        },

        "dob": {
            "selector": "input[name='dob']",
            "type": "date",
            "enabled": False
        },

        "gender": {
            "selector": "input[name='gender']",
            "type": "radio",
            "options": ["male", "female", "other"],
            "enabled": False
        },

        "address": {
            "selector": "input[name='address']",
            "type": "text",
            "enabled": False
        },

        "company_name": {
            "selector": "input[name='company_name']",
            "type": "text",
            "enabled": False
        },

        "country": {
            "selector": "select[name='country']",
            "type": "select",
            "value": "India",
            "enabled": False
        },

        "phone": {
            "selector": "input[name='phone']",
            "type": "numeric",
            "enabled": False
        },

        "otp": {
            "selector": "input[name='otp']",
            "type": "numeric",
            "enabled": False
        }
    }
}

# ===============================
# TEST DATA BY FIELD TYPE
# ===============================

TEST_DATA = {
    "alpha": [
        ("John Doe", True),
        ("John123", False),
        ("@John", False),
        ("", False)
    ],

    "numeric": [
        ("9876543210", True),
        ("12345", False),
        ("abcd123", False),
        ("@123", False)
    ],

    "email": [
        ("__UNIQUE_EMAIL__", True),  # special marker
        ("invalid@", False),
        ("@test.com", False),
        ("", False)
    ],

    "password": [
        ("Strong@123", True),
        ("password", False),
        ("12345", False),
        ("", False)
    ],

    "password_confirm": [
        ("Strong@123", True),
        ("Wrong@123", False)
    ],

    "date": [
        ("1999-01-01", True),
        ("2050-01-01", False),
        ("", False)
    ]
}

# ===============================
# LOGGING SETUP 
# ===============================
def create_log_file(url):
    domain = urlparse(url).netloc.replace("www.", "")
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"{domain}-{timestamp}.txt"
    return filename

LOG_FILE = create_log_file(CONFIG["url"])

def log(message):
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")


# ===============================
# FIELD FILLING LOGIC
# ===============================

async def fill_field(page, field, value):
    ftype = field["type"]

    if ftype == "radio":
        await page.locator(
            f"{field['selector']}[value='{value}']"
        ).check()

    elif ftype == "select":
        await page.select_option(
            field["selector"],
            label=field["value"]
        )

    else:
        await page.fill(field["selector"], value)

# ===============================
# SUCCESS DETECTION LOGIC
# ===============================

async def detect_success(page, old_url, old_form_signature=None):
    cfg = CONFIG["success_detection"]

    # 1️⃣ URL CHANGE
    if page.url != old_url:
        for kw in cfg["success_url_keywords"]:
            if kw in page.url.lower():
                return True, "URL Changed"

    # 2️⃣ SUCCESS MESSAGE
    for selector in cfg["success_message_selectors"]:
        try:
            if await page.locator(selector).is_visible():
                return True, "Success Message Found"
        except:
            pass

    # 3️⃣ INLINE VALIDATION ERROR (NEW)
    has_inline_error, error_text = await detect_inline_validation_error(page)
    if has_inline_error:
        return False, f"Inline Validation Error: {error_text}"

    # 4️⃣ ERROR MESSAGE SELECTORS
    for selector in cfg["error_message_selectors"]:
        try:
            if await page.locator(selector).is_visible():
                return False, "Error Message Found"
        except:
            pass

    # 5️⃣ FORM CHANGED
    if old_form_signature is not None:
        try:
            await page.wait_for_timeout(800)

            new_form_signature = await get_form_signature(page)
            if new_form_signature and new_form_signature != old_form_signature:
                return True, "Form Changed (Next Step)"
        except:
            pass

    # 6️⃣ SUBMIT BUTTON DISABLED
    try:
        submit_btn = page.locator(CONFIG["submit_selector"])
        if not await submit_btn.is_enabled():
            return True, "Submit Button Disabled"
    except:
        pass

    return None, "Inconclusive"


# ===============================
# MAIN TEST RUNNER
# ===============================

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 🔹 LOG HEADER (ADDED)
        log("=" * 60)
        log("FORM VALIDATION TEST STARTED")
        log(f"URL: {CONFIG['url']}")
        log(f"Timestamp: {datetime.now().isoformat()}")
        log("=" * 60)

        for field_name, field in CONFIG["fields"].items():
            if not field["enabled"]:
                continue

            log(f"\n🔹 Testing Field: {field_name}")

            for value, expected in TEST_DATA.get(field["type"], []):
                await page.goto(CONFIG["url"], timeout=60000)

                shared_values = {}

                for name, f in CONFIG["fields"].items():
                    if not f["enabled"]:
                        continue

                    if f["type"] == "email" and value == "__UNIQUE_EMAIL__":
                        fill_value = generate_unique_email()

                    elif "depends_on" in f:
                        fill_value = shared_values.get(f["depends_on"])

                    elif name == field_name:
                        fill_value = value

                    else:
                        fill_value = "Valid123"

                    shared_values[name] = fill_value
                    await fill_field(page, f, fill_value)

                # CAPTURE FORM SIGNATURE BEFORE CLICKING SUBMIT
                old_form_signature = await get_form_signature(page)
                old_url = page.url
                
                await page.click(CONFIG["submit_selector"])
                await page.wait_for_timeout(CONFIG["wait_after_submit"] * 1000)

                # PASS THE OLD SIGNATURE FOR COMPARISON
                result, reason = await detect_success(page, old_url, old_form_signature)
                status = "PASS" if result == expected else "FAIL"

                log(f"   [{status}] Input: {value} → {reason}")

                await asyncio.sleep(CONFIG["delay_between_tests"])

        await browser.close()


# ===============================
# START EXECUTION
# ===============================

asyncio.run(run())
