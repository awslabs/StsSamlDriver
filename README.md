# STS SAML Driver

A Python-based SAML authentication handler for AWS STS that allows you to get temporary credentials using SAML to the AWS CLI, or an application written using an AWS SDK without the need to screen scrape or emulate a browser.

Many tools exist today to get AWS credentials into an environment that can work with the AWS CLI or AWS SDK using SAML. However most of these scripts rely on parsing HTML or fully emulating a browser to do so which is difficult and may not be supported by various IDPs, especially on identity-as-a-service providers who may update the HTML on their login flows without notice.

This tool avoids interacting directly with a SAML IDP in any capacity by starting up a server on http://localhost:8090, which will receive a SAML assertion from your IDP on `/saml` from your browser.  After receiving the assertion, the code will attempt to call `AssumeRoleWithSAML` to assume the role, and deliver the temporary credentials to your application and optionally launch an AWS console session. The server only listens for a single SAML assertion and will stop running after one is received.

You can use this tool by updating the ACS server of your SAML IDP (or target, or whatever your IDP's name is for where the SAML assertion is sent to) for a given application targetted at assuming a role on AWS to http://localhost:8090/saml , or doing similar with a userscript service like tampermoney, or custom browser plugins to override a SAML destination.

## Features

- Support for AWS IAM role assumption using SAML assertions
- Optional AWS Management Console access
- Configurable session duration
- targets specific region
- no screen scraping or browser emulation

## Prerequisites

- Python 3.x
- AWS account with configured SAML provider
- Required Python packages:
  - boto3
  - bottle
  - requests
  - urllib3
- jq

## Installation from github

1. Clone the repository:
```bash
git clone https://github.com/awslabs/StsSamlDriver.git
```

2. install the tool
```bash
pip3 install .
```
or if you prefer, pipx
```bash
pipx install .
```


3. install jq (optional)
If you want to use the provided wrapper script to set CLI environment variables, you'll need jq.
This may vary based on your package manager.
Here's a few common ones to easy copy paste.
```bash
apt install jq
```
```bash
yum install jq
```
```bash
brew install jq
```

## Installation from pypi with pip

This package is also hosted on pypi can be directly installed from pypi using pip.

```bash
pip3 install sts_saml_driver
```

or 

```bash
pipx install sts_saml_driver
```

Then install jq (optional)

If you want to use the provided wrapper script to set CLI environment variables, you'll need jq.
This may vary based on your package manager.
Here's a few common ones to easy copy paste.
```bash
apt install jq
```
```bash
yum install jq
```
```bash
brew install jq
```


## High level Setup in AWS and IAM

1. [Follow the steps for creating a SAML IDP in IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_saml.html)
1. [Follow the steps for creating a SAML role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_saml.html) . You may need to modify the `saml:aud` condition key check to allow for "http://localhost:8090/saml" , or remove the condition check for `saml:aud` all together. This key is not necesarry to ensure that the SAML assertions used for accessing your AWS accounts are the ones you intend, as SAML federation for AWS requires other AWS specific metadata.
1. Configure the IdP you plan to use for this flow to send the SAML assertions to use `http://localhost:8090/saml` as an "ACS URL" or "target". The terminology may vary based on your IDP. 
1. Use this tool to sign into AWS. Detailed instructions are below in the "Usage" section for a variety of different usecases.

### Tips for configuring specific IDPs

* PingFederate allows you to have [multiple ACS urls associated with an application, and specify which ACS url is used](https://support.pingidentity.com/s/article/Using-multiple-ACS-URLs-as-PingFederate-IdP). You can use the ACSIdx parameter to specify where the SAML assertion is sent, and have urls for direct console access, or this tool.
* EntraID does not allow you to dynamically specify ACS urls with IdP initiated SAML. For EntraId, you can create an additional enterprise application for SAML authentication with http://localhost:8090/saml as the ACS url, add the metadata from this application to your AWS accounts, and configure it with the IAM roles you want. Your end-user wanting to get AWS credentials for the CLI or SDK will then use the EntraID application you've created for the for this tool.
* Okta does not allow you to dynamically specify ACS urls with an IdP initiated SAML. For Okta, you can create an additional application for SAML authentication with http://localhost:8090/saml as the ACS url, add the metadata from this application to your AWS accounts, and configure it with the IAM roles you want. Your end-user wanting to get AWS credentials for the CLI or SDK will then use the Okta application you've created for the for this tool.
* ADFS does not allow you to dynamically specify ACS urls with IdP initiated SAML. For ADFS, you can create an additional relying party trust for SAML authentication with http://localhost:8090/saml as the ACS url, add the metadata from this relying party trust to your AWS accounts, and configure it with the IAM roles you want. Your end-user wanting to get AWS credentials for the CLI or SDK will then use the ADFS application/IDP initiated SAML url you've created for the for this tool.
* Google Workspace does not allow you to dynamically specify ACS urls with an IdP initiated SAML. For Google Workspace, you can create an additional application for SAML authentication with http://localhost:8090/saml as the ACS url, add the metadata from this application to your AWS accounts, and configure it with the IAM roles you want. Your end-user wanting to get AWS credentials for the CLI or SDK will then use the Google Workspace application you've created for the for this tool.

### Single application approaches for IdPs that do not support dynamic SAML ACS urls

If you do not wish to duplicate applications within your IDPs if your IDP does not support dynamic ACS urls for IdP initiated SAML, there are still other approaches you can take. This will require some level of abstrace with either infrastructure, or by getting involved with the user's browser.

1. Build a userscript with browser plugins like Tampermonkey or Greasemonkey for your IdP that intercept the form post for SAML federation to AWS, and ask the user where they would like to send the assertion.
2. Build a browser plugin that behaves similarly - intercepts the form post for SAML federation to AWS, and asks the user where they would like it sent.
3. Build a person in the middle style application that receives the SAML assertion and set that as the ACS url for your application for SAML federation to AWS. Your person in the middle will receive the SAML assertion, and then ask the user where they would like it sent.

## Usage

This tool is executed by calling the `stssamldriver` script after it's been installed to your system by pip.

After you, or your application executes samldriver, it will then wait and take no further action until a saml assertion is sent to http://localhost:8090/saml, with which it will attempt to call `AssumeRoleWithSAML`.

### Parameters

Required Parameters:
* `--role-arn`: The AWS Role ARN to assume
* `--saml-provider-arn`: The AWS SAML Provider ARN

Optional Parameters:
* `--region`: AWS Region to use (default: us-east-1)
* `--duration-seconds`: Duration in seconds for the assumed role session (default: 3600)
* `--profile-to-update`: Name of the AWS profile to update
* `--path`: Path to AWS config file to update (default: "~/.aws/config")
* `--console`: Flag to open an AWS Management Console session
* `--issuer`: Relevant URL from your IDP that will kick off SAML federation to AWS. The tool will open the default system browser to this URL. issuer may be something like your okta tenant, or deep links to SAML federation flows from your IDP.



### Usage examples

This tool was designed with 3 usecases in mind.

1. Using a wrapper script to call the python script, to set the relevant AWS environment variables. The AWS CLI, and other applications using the [default credentials provider chain](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html) will find and discover these credentials from the environment variables.
2. Call the script as a `credential_process`. This is the best option to deliver temporary credentials to an application that are only for that application, as they're only in the applications memory 
3. Call the script with an additional flag to update a [profile in your aws configuration](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html#cli-configure-files-format-profile) file. AWS SDKs, and the CLI can then reference this profile.



### Wrapper script for environment variables.

To set environment variables, use the provided `saml_aws_environment.sh` script. 

run the script like:

```bash
source saml_aws_environment.sh -r your-aws-region -a arn:aws:iam::111122223333:role/your-iam-role -p arn:aws:iam::11112222333:saml-provider/your-iam-saml-idp
```

Replacing the aws region (-r), the role ARN (-a), and the IAM IDP ARN -(p), as you need.

Passing -c will pass the "--console" flag to the underlying script, to open a console session as well as set environment variables.

After executing the script, start your SAML login procedure.

If successful, environment variables will be set and any application using the default credentials provider chain with the AWS SDKs, or the AWS CLI, will discover and use these credentials.

Please note the script assumes it's running in the same directory where the venv with the python dependencies exist.

### As a credential process

You'll need to a create a profile in `~/.aws/config`, or wherever your application reads it's aws configuration from like so:

```
[profile samlexample]
credential_process = /path/to/samldriver --region your-aws-region --role-arn arn:aws:iam::111122223333:role/your-iam-role --saml-provider-arn arn:aws:iam::11112222333:saml-provider/your-iam-saml-idp
```

Then you'll need to reference the profile when you create a `session` or `credential provider`. Here is an example from the python boto3 sdk which will create a session using this profile, then call aws sts to return the caller identity.

```python
import boto3
process_session = boto3.Session(profile_name='samlexample')
sts_client = process_session.client('sts')
response = sts_client.get_caller_identity()
```

With credential_process, only the application you start will run with those credentials and they will not be set as environment variables or available to other applications.

The credential_process will start the samldriver and it will hold cause your application to halt until the SAML assertion is received by the tool.

When using a credential process in your application, you need to account for re-try and error logic within your application.

Credential process is typically not recommended with the AWS CLI, as it will call the credential process once per CLI command, which is a lot of needless commands. If you want to use the AWS CLI, a profile or environment variables are preferable.

### Updating a profile

you can specify the flags `--profile-to-update` and optionally `--path` to update an aws configuration profile.

```bash
/path/to/samldriver --region your-aws-region --role-arn arn:aws:iam::111122223333:role/your-iam-role --saml-provider-arn arn:aws:iam::11112222333:saml-provider/your-iam-saml-idp --profile-to-update saml --path ~/.aws/config
```

This will update the "saml" profile in ~/.aws/config (the default location).  Then the aws cli can be invoked with "--profile-to-update saml" to use that profile. AWS SDKs can [reference the saml profile](https://docs.aws.amazon.com/sdkref/latest/guide/feature-static-credentials.html) using the relevant approaches for each language.

After you run samldriver, perform your saml login. The script will wait until a SAML assertion is received on http://localhost:8090.
