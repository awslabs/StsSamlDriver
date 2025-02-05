#!/bin/zsh
#execute this by calling source saml_aws_cli.sh . Failure to do so will not set the environment variables.
#We use a bash script because python cannot modify the environment variables of it's parent shell.
#be sure to execute this using source and not calling it directly.
OPTIND=1

#Unset a bunch of stuff that might confuse the STS client.
#Please note since you're sourcing this script, it will unset these environment variables in your shell session.
unset AWS_CONFIG_FILE
unset AWS_PROFILE
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
unset AWS_EXPIRATION


REGION=""
ROLEARN=""
PROVIDERARN=""
CONSOLE=false

# Parse command line arguments
while getopts "r:a:p:c" opt; do
  case $opt in
    r) REGION="$OPTARG";;
    a) ROLEARN="$OPTARG";;
    p) PROVIDERARN="$OPTARG";;
    c) CONSOLE="true";;
    \?) echo "Invalid option -$OPTARG" >&2; exit 1;;
  esac
done

# Check if required parameters are provided
if [ -z "$REGION" ] || [ -z "$ROLEARN" ] || [ -z "$PROVIDERARN" ]; then
    echo "Usage: source $0 -r <region> -a <role-arn> -p <provider-arn>"
    return 0
fi

echo "Waiting for SAML Assertion..."
#update this with your required region, role-arn, and saml provider arn (principal arn)
#You may optionally add an argument for --duration-seconds
#likewise, if you want a console session you can add a --console flag

if [ "$CONSOLE" = true ]; then
  CREDENTIALS=`stssamldriver --role-arn $ROLEARN --saml-provider-arn $PROVIDERARN --region $REGION  --console`
else
  CREDENTIALS=`stssamldriver --role-arn $ROLEARN --saml-provider-arn $PROVIDERARN --region $REGION`
fi


if ! echo "${CREDENTIALS}" | jq -e 'has("AccessKeyId")' >/dev/null 2>&1; then
    echo "Error: Did not receive valid AWS credentials format"
    echo "${CREDENTIALS}"
    return 1
fi

export AWS_ACCESS_KEY_ID=`echo ${CREDENTIALS} | jq -r '.AccessKeyId'`
export AWS_SECRET_ACCESS_KEY=`echo ${CREDENTIALS} | jq -r '.SecretAccessKey'`
export AWS_SESSION_TOKEN=`echo ${CREDENTIALS} | jq -r '.SessionToken'`
export AWS_EXPIRATION=`echo ${CREDENTIALS} | jq -r '.Expiration'`


if [[ "$AWS_ACCESS_KEY_ID" == *"ASIA"* ]]; then
  echo "Credentials set, looks good to go!"
else
  echo "Looks like this operation was not succesful."
  echo $CREDENTIALS
fi