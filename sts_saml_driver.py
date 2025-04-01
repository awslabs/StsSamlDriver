
from bottle import post, request, run, response, redirect
import boto3
import argparse
import requests
from botocore.config import Config
import urllib
import sys
import json
import datetime
from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler
from bottle import ServerAdapter
import os
import configparser
import webbrowser

args = None

class SingleShotServerAdapter(ServerAdapter):
    def run(self, handler):  # Method to start the server
        # Custom handler to shutdown server after first request
        class CustomHandler(WSGIRequestHandler):
            def log_message(self, format, *args):
                # Suppress log messages
                pass

            def handle(self):
                super().handle()
                self.server.shutdown_request(self.request)  # Shut down after handling

        #only open a browser if the user has specified and IDP, and there is a console session
        if args.issuer != "https://console.aws.amazon.com":
            webbrowser.open(args.issuer)
         # Create a server that will handle only a single request
        self.server = make_server(self.host, self.port, handler, WSGIServer, handler_class=CustomHandler,)
        self.server.handle_request()  # Handle a single request


@post('/saml')
def receive_saml():
    try:
        saml_response = request.forms.get('SAMLResponse')
        if not saml_response:
            response.status = 400
            return """
                <html>
                <head><title>&#x274C; Error getting AWS credentials</title></head>
                    <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                        <h2 style="color: #d13212;">Error&#x274C;</h2>
                        <p>No SAMLResponse found in the POST data</p>
                    </body>
                </html>
            """
        
        if not saml_response.strip():
            response.status = 400
            return """
                <html>
                <head><title>&#x274C; Error getting AWS credentials</title></head>
                    <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                        <h2 style="color: #d13212;">Error &#x274C;</h2>
                        <p>Empty SAMLResponse provided</p>
                    </body>
                </html>
            """

        credentials = assume_role_with_saml(
            saml_response.replace(" ", "+"), 
            args.role_arn, 
            args.saml_provider_arn, 
            args.region,
            args.profile_to_update,
            args.path
        )

        if args.console:
            response.status = 302  
            response.set_header('Location', getConsoleUrl(credentials, args.region,args.issuer))
            return f"""
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                        <h2>Redirecting to AWS Console...</h2>
                        <p>If you are not redirected automatically, <a href="%s">{getConsoleUrl(credentials, args.region, args.issuer)}</a></p>
                    </body>
                </html>
            """ 
        
        if not args.profile_to_update:
            response.status = 200
            response.content_type = 'text/html'
            return f"""
                <html>
                    <head><title>&#x2705;Succesful request for AWS credentials </title></head>
                    <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                        <h2 style="color: #16191f;">SAML Login Succesfull &#x2705;</h2>
                        <p style="color: #444;">Your temporary AWS security credentials have been acquired.</p>
                        <p style="color: #444;">The AssumeRoleWithSAML call was succesful and your environment variables, or application has been issued credentials.</p>
                    </body>
                </html>
            """        
        
        if args.profile_to_update:
            response.status = 200
            response.content_type = 'text/html'
            return f"""
                <html>
                    <head><title>&#x2705;Succesful request for AWS credentials </title></head>
                    <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                        <h2 style="color: #16191f;">SAML Login Succesful &#x2705;</h2>
                        <p style="color: #444;">Your credentials have been successfully updated in the profile <strong>{args.profile_to_update}</strong></p>
                        <p style="color: #444;">You can add the argument <strong>--profile {args.profile_to_update}</strong> to AWS CLI commands to use these credentials</p>
                        <p style="color: #444;">To learn how to use this profile with the AWS SDK, please read the documentation for the AWS SDK you're using.</p>
                    </body>
                </html>
                """
        


    except boto3.exceptions.botocore.exceptions.ClientError as e:
        response.status = 400
        return f"""
                <html>
                <head><title>&#x274C; Error getting AWS credentials</title></head>
                    <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                        <h2 style="color: #d13212;">Error&#x274C;</h2>
                        <p>Error returned from AWS: <strong>{e}</b></p>
                    </body>
                </html>
            """
    except Exception as e:
        response.status = 500
        f"""
                <html>
                <head><title>&#x274C; Error getting AWS credentials</title></head>
                    <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                        <h2 style="color: #d13212;">Error&#x274C;</h2>
                        <p>Error returned from AWS: <strong>{e}</b></p>
                    </body>
                </html>
            """
    

def assume_role_with_saml(saml_assertion, role_arn, principal_arn, region,profile,path):
    botoconfig = Config()
    try:
        sts_client = boto3.client('sts', region_name=region, config=botoconfig)
        response = sts_client.assume_role_with_saml(
            RoleArn=role_arn,
            PrincipalArn=principal_arn,
            SAMLAssertion=saml_assertion,
            DurationSeconds=args.duration_seconds
        )
        
        response['Credentials']['Expiration'] = response['Credentials']['Expiration'].isoformat()
        response['Credentials']['Version'] = 1
        if not profile:
            print(json.dumps(response['Credentials']))
        else:
            config = configparser.ConfigParser()
            config_path = os.path.expanduser(path)
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            config.read(config_path)

            # Handle the profile name correctly
            profile_section = f"profile {profile}" if profile != "default" else "default"

            if not config.has_section(profile_section):
                config.add_section(profile_section)

            config[profile_section].update({
                'region': region,
                'aws_access_key_id': response['Credentials']['AccessKeyId'],
                'aws_secret_access_key': response['Credentials']['SecretAccessKey'],
                'aws_session_token': response['Credentials']['SessionToken']
            })

            with open(config_path, 'w') as configfile:
                config.write(configfile)
            print(f"Succesfully updated profile {profile} in {path}")

        return response['Credentials']
    except boto3.exceptions.botocore.exceptions.ClientError as e:
        error_message = f"AWS API Error: {e.response['Error']['Message']}"
        print(error_message, file=sys.stderr)
        raise
    except boto3.exceptions.botocore.exceptions.ParamValidationError as e:
        error_message = f"Parameter validation error: {str(e)}"
        print(error_message, file=sys.stderr)
        raise
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(error_message, file=sys.stderr)
        raise
    
def getConsoleUrl(credentials, region,issuer):
    try:
        request_credentials = {
            'sessionKey': credentials['SecretAccessKey'],
            'sessionId': credentials['AccessKeyId'],
            'sessionToken': credentials['SessionToken']
        }


        request_parameters = f"?Action=getSigninToken&SessionDuration={args.duration_seconds}"
        request_parameters += "&Session=" + urllib.parse.quote_plus(json.dumps(request_credentials))
        request_url = f"https://{region}.signin.aws.amazon.com/federation" + request_parameters
        
        r = requests.get(request_url,timeout=5)
        r.raise_for_status()  # Raise an exception for bad status codes
        
        signin_token = r.json()
        if 'SigninToken' not in signin_token:
            raise ValueError("SigninToken not found in AWS Federation Service response")

        request_parameters = "?Action=login"
        request_parameters += f"&Issuer={issuer}"
        request_parameters += "&Destination=" + urllib.parse.quote_plus(f"https://{region}.console.aws.amazon.com/")
        request_parameters += "&SigninToken=" + signin_token["SigninToken"]
        return f"https://{region}.signin.aws.amazon.com/federation" + request_parameters

    except requests.exceptions.RequestException as e:
        error_message = f"Failed to contact AWS Federation Service: {str(e)}"
        print(error_message, file=sys.stderr)
        raise
    except json.JSONDecodeError as e:
        error_message = "Invalid JSON response from AWS Federation Service"
        print(error_message, file=sys.stderr)
        raise
    except Exception as e:
        error_message = f"Error generating console URL: {str(e)}"
        print(error_message, file=sys.stderr)
        raise



def main():
    global args
    parser = argparse.ArgumentParser(description='Assume AWS Role with SAML Assertion.')
    parser.add_argument('--role-arn', type=str, required=True, help='AWS Role ARN to assume')
    parser.add_argument('--saml-provider-arn', type=str, required=True, help='AWS SAML Provider ARN')
    parser.add_argument('--region', type=str, default='us-east-1', help='AWS Region (default: us-east-1)')
    parser.add_argument('--duration-seconds', type=int, default=3600,
                      help='seconds to assume role for (3600 default)')
    parser.add_argument('--console', action='store_true', help='Open a console session as well if set')
    parser.add_argument('--profile-to-update', type=str, default=False, help='the name of the AWS profile to update when')
    parser.add_argument('--path', type=str, default="~/.aws/credentials", help='path to aws credentials file you want updated. used with profile')
    parser.add_argument('--issuer', type=str, default='https://console.aws.amazon.com', help='The URL of your IDP. Your browser will be opened to this.')
    
    
    args = parser.parse_args()

    # Validate ARNs
    if not args.role_arn.startswith('arn:aws:iam::'):
        parser.error("Invalid role ARN format")
    if not args.saml_provider_arn.startswith('arn:aws:iam::'):
        parser.error("Invalid principal ARN format")
    if not args.issuer.startswith('https://'):
        parser.error("Issuer must start with https://")

    try:
        if args.profile_to_update:
            print("Waiting for SAML assertion....")
        server_adapter = SingleShotServerAdapter(host='localhost', port=8090, quiet=True)
        run(server=server_adapter, quiet=True)
    except Exception as e:
        print(f"Server error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()