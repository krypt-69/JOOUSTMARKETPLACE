# app/mpesa.py
import requests
import base64
from datetime import datetime
import json
from flask import current_app

class MpesaGateway:
    def __init__(self):
        # Don't load config here - it's too early
        pass
    
    def get_access_token(self):
        """Get Megapay API access (API key based, not OAuth)"""
        try:
            # For Megapay, we don't need OAuth token, but we'll keep this function
            # for compatibility and return a placeholder
            api_key = current_app.config.get('MEGAPAY_API_KEY')
            
            print(f"DEBUG: Megapay API Key: {api_key}")
            
            if not api_key:
                print("DEBUG: Missing Megapay API Key")
                return None
            
            # Megapay uses API key directly, not OAuth
            # We'll return a placeholder token for compatibility
            return f"Bearer {api_key}"
            
        except Exception as e:
            print(f"DEBUG: Megapay Auth Error: {str(e)}")
            return None
    
    def stk_push(self, phone_number, amount, account_reference, description):
        """Initiate STK push for payment using Megapay"""
        try:
            # Get config for Megapay
            api_key = current_app.config.get('MEGAPAY_API_KEY')
            business_shortcode = current_app.config.get('MEGAPAY_BUSINESS_CODE')
            base_url = current_app.config.get('MEGAPAY_BASE_URL', 'https://api.sandbox.megapay.com')
            
            print(f"DEBUG: Megapay Business Code: {business_shortcode}")
            
            if not api_key or not business_shortcode:
                return None, "Megapay configuration missing"
            
            # Clean phone number (remove leading + if present)
            if phone_number.startswith('+'):
                phone_number = phone_number[1:]
            
            # Megapay STK push payload
            payload = {
                "businessCode": business_shortcode,
                "phoneNumber": phone_number,
                "amount": float(amount),  # Megapay expects float
                "accountReference": account_reference,
                "description": description,
                "callbackUrl": current_app.config.get('MPESA_CALLBACK_URL', 'https://hedgy-marvella-nonsubsiding.ngrok-free.dev/payment-callback')
            }
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Megapay STK endpoint
            url = f"{base_url}/v1/stk/push"
            print(f"DEBUG: Megapay STK Push URL: {url}")
            print(f"DEBUG: Megapay STK Payload: {json.dumps(payload, indent=2)}")
            print(f"DEBUG: Headers: {headers}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"DEBUG: Megapay STK Response Status: {response.status_code}")
            print(f"DEBUG: Megapay STK Response Text: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            # Check Megapay response structure
            if result.get('success') == True or result.get('status') == 'success':
                return result, "STK push initiated successfully"
            elif 'requestId' in result or 'CheckoutRequestID' in result:
                return result, "STK push initiated successfully"
            else:
                error_message = result.get('message', result.get('error', 'Unknown error'))
                return result, f"STK push failed: {error_message}"
            
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Megapay STK Request Error: {str(e)}")
            return None, f"Network error: {str(e)}"
        except Exception as e:
            print(f"DEBUG: Megapay STK General Error: {str(e)}")
            return None, str(e)
    
    def stk_push1(self, phone_number, amount, account_reference, description):
        """Initiate STK push for payment with different callback"""
        try:
            # Get config for Megapay
            api_key = current_app.config.get('MEGAPAY_API_KEY')
            business_shortcode = current_app.config.get('MEGAPAY_BUSINESS_CODE')
            base_url = current_app.config.get('MEGAPAY_BASE_URL', 'https://api.sandbox.megapay.com')
            
            print(f"DEBUG: Megapay Business Code: {business_shortcode}")
            
            if not api_key or not business_shortcode:
                return None, "Megapay configuration missing"
            
            # Clean phone number (remove leading + if present)
            if phone_number.startswith('+'):
                phone_number = phone_number[1:]
            
            # Megapay STK push payload with different callback
            payload = {
                "businessCode": business_shortcode,
                "phoneNumber": phone_number,
                "amount": float(amount),
                "accountReference": account_reference,
                "description": description,
                "callbackUrl": current_app.config.get('MPESA_CALLBACK_URL_UNLOCK', 'https://hedgy-marvella-nonsubsiding.ngrok-free.dev/unlock/callback')
            }
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Megapay STK endpoint
            url = f"{base_url}/v1/stk/push"
            print(f"DEBUG: Megapay STK Push URL: {url}")
            print(f"DEBUG: Megapay STK Payload: {json.dumps(payload, indent=2)}")
            print(f"DEBUG: Headers: {headers}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"DEBUG: Megapay STK Response Status: {response.status_code}")
            print(f"DEBUG: Megapay STK Response Text: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            # Check Megapay response structure
            if result.get('success') == True or result.get('status') == 'success':
                return result, "STK push initiated successfully"
            elif 'requestId' in result or 'CheckoutRequestID' in result:
                return result, "STK push initiated successfully"
            else:
                error_message = result.get('message', result.get('error', 'Unknown error'))
                return result, f"STK push failed: {error_message}"
            
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Megapay STK Request Error: {str(e)}")
            return None, f"Network error: {str(e)}"
        except Exception as e:
            print(f"DEBUG: Megapay STK General Error: {str(e)}")
            return None, str(e)
    
    def check_transaction_status(self, checkout_request_id):
        """Check transaction status using Megapay"""
        try:
            api_key = current_app.config.get('MEGAPAY_API_KEY')
            base_url = current_app.config.get('MEGAPAY_BASE_URL', 'https://api.sandbox.megapay.com')
            
            if not api_key:
                return None
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Megapay status check endpoint (might vary - adjust based on actual API)
            # Option 1: If Megapay provides specific status endpoint
            url = f"{base_url}/v1/transaction/status/{checkout_request_id}"
            
            # Option 2: If using query endpoint
            # payload = {"checkoutRequestId": checkout_request_id}
            # url = f"{base_url}/v1/stk/query"
            # response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"DEBUG: Megapay Status Check Response: {result}")
            
            return result
            
        except Exception as e:
            print(f"DEBUG: Megapay Status Check Error: {str(e)}")
            return None