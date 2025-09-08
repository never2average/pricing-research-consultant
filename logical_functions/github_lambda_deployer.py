import os
import subprocess
import tempfile
import zipfile
import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime


def clone_github_repo(github_url, temp_dir):
    try:
        subprocess.run(['git', 'clone', github_url, temp_dir], check=True, capture_output=True, text=True)
        print(f"Successfully cloned repository: {github_url}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to clone repository {github_url}: {e.stderr}")
        return False


def create_deployment_package(repo_path):
    zip_path = os.path.join(tempfile.gettempdir(), 'lambda_deployment.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, repo_path)
                zipf.write(file_path, arcname)
    
    print(f"Created deployment package: {zip_path}")
    return zip_path


def create_or_update_lambda_function(function_name, zip_path, repo_name):
    session = get_aws_session()
    lambda_client = session.client('lambda')
    
    # Read the zip file
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        # Try to get existing function
        lambda_client.get_function(FunctionName=function_name)
        
        # Function exists, update it
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"Updated existing Lambda function: {function_name}")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Function doesn't exist, create it
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime=os.getenv('LAMBDA_DEFAULT_RUNTIME', 'python3.9'),
            Role=get_lambda_execution_role_arn(),
            Handler='lambda_function.lambda_handler',  # Default handler
            Code={'ZipFile': zip_content},
            Description=f'Auto-deployed from GitHub repo: {repo_name}',
            Timeout=int(os.getenv('LAMBDA_DEFAULT_TIMEOUT', '300')),
            MemorySize=int(os.getenv('LAMBDA_DEFAULT_MEMORY', '128')),
            Environment={
                'Variables': {
                    'REPO_NAME': repo_name
                }
            }
        )
        print(f"Created new Lambda function: {function_name}")
    
    return response


def get_lambda_execution_role_arn():
    role_arn = os.getenv('LAMBDA_EXECUTION_ROLE_ARN')
    if not role_arn:
        raise ValueError("LAMBDA_EXECUTION_ROLE_ARN environment variable is required")
    return role_arn


def get_aws_session():
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    return session


def create_cloudwatch_event_rule(function_name, repo_name):
    session = get_aws_session()
    events_client = session.client('events')
    lambda_client = session.client('lambda')
    
    rule_name = f"{function_name}-schedule"
    
    try:
        # Create or update the EventBridge rule for 120 seconds (2 minutes)
        rule_response = events_client.put_rule(
            Name=rule_name,
            ScheduleExpression='rate(2 minutes)',
            Description=f'Trigger {function_name} every 120 seconds',
            State='ENABLED'
        )
        
        # Get Lambda function ARN
        function_response = lambda_client.get_function(FunctionName=function_name)
        function_arn = function_response['Configuration']['FunctionArn']
        
        # Add target to the rule
        events_client.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    'Id': '1',
                    'Arn': function_arn
                }
            ]
        )
        
        # Add permission for EventBridge to invoke Lambda
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=f"{rule_name}-permission",
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=rule_response['RuleArn']
            )
        except lambda_client.exceptions.ResourceConflictException:
            # Permission already exists
            pass
        
        print(f"Created CloudWatch Event rule: {rule_name}")
        return rule_response
        
    except ClientError as e:
        print(f"Failed to create CloudWatch Event rule: {e}")
        raise


def create_cloudwatch_alarms(function_name, repo_name):
    if not os.getenv('ENABLE_CLOUDWATCH_ALARMS', 'false').lower() == 'true':
        print("CloudWatch alarms disabled")
        return None
    
    session = get_aws_session()
    cloudwatch = session.client('cloudwatch')
    sns = session.client('sns')
    
    # Create SNS topic if email endpoint is provided
    sns_topic_arn = os.getenv('CLOUDWATCH_ALARM_SNS_TOPIC_ARN')
    email_endpoint = os.getenv('ALARM_EMAIL_ENDPOINT')
    
    if not sns_topic_arn and email_endpoint:
        try:
            topic_response = sns.create_topic(
                Name=f'{function_name}-alerts'
            )
            sns_topic_arn = topic_response['TopicArn']
            
            # Subscribe email to topic
            sns.subscribe(
                TopicArn=sns_topic_arn,
                Protocol='email',
                Endpoint=email_endpoint
            )
            print(f"Created SNS topic and email subscription for {function_name}")
        except ClientError as e:
            print(f"Failed to create SNS topic: {e}")
            sns_topic_arn = None
    
    alarms_created = []
    
    # Error alarm
    try:
        error_alarm = cloudwatch.put_metric_alarm(
            AlarmName=f'{function_name}-errors',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='Errors',
            Namespace='AWS/Lambda',
            Period=300,
            Statistic='Sum',
            Threshold=0.0,
            ActionsEnabled=True,
            AlarmActions=[sns_topic_arn] if sns_topic_arn else [],
            AlarmDescription=f'Alarm when {function_name} has errors',
            Dimensions=[
                {
                    'Name': 'FunctionName',
                    'Value': function_name
                }
            ]
        )
        alarms_created.append(f'{function_name}-errors')
        print(f"Created error alarm for {function_name}")
    except ClientError as e:
        print(f"Failed to create error alarm: {e}")
    
    # Duration alarm (for timeouts)
    try:
        timeout = int(os.getenv('LAMBDA_DEFAULT_TIMEOUT', '300'))
        duration_threshold = timeout * 0.8 * 1000  # 80% of timeout in milliseconds
        
        duration_alarm = cloudwatch.put_metric_alarm(
            AlarmName=f'{function_name}-duration',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='Duration',
            Namespace='AWS/Lambda',
            Period=300,
            Statistic='Average',
            Threshold=duration_threshold,
            ActionsEnabled=True,
            AlarmActions=[sns_topic_arn] if sns_topic_arn else [],
            AlarmDescription=f'Alarm when {function_name} duration is high',
            Dimensions=[
                {
                    'Name': 'FunctionName',
                    'Value': function_name
                }
            ]
        )
        alarms_created.append(f'{function_name}-duration')
        print(f"Created duration alarm for {function_name}")
    except ClientError as e:
        print(f"Failed to create duration alarm: {e}")
    
    # Throttle alarm
    try:
        throttle_alarm = cloudwatch.put_metric_alarm(
            AlarmName=f'{function_name}-throttles',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='Throttles',
            Namespace='AWS/Lambda',
            Period=300,
            Statistic='Sum',
            Threshold=0.0,
            ActionsEnabled=True,
            AlarmActions=[sns_topic_arn] if sns_topic_arn else [],
            AlarmDescription=f'Alarm when {function_name} is throttled',
            Dimensions=[
                {
                    'Name': 'FunctionName',
                    'Value': function_name
                }
            ]
        )
        alarms_created.append(f'{function_name}-throttles')
        print(f"Created throttle alarm for {function_name}")
    except ClientError as e:
        print(f"Failed to create throttle alarm: {e}")
    
    return {
        'sns_topic_arn': sns_topic_arn,
        'alarms_created': alarms_created
    }


def deploy_github_repo_to_lambda(github_url):
    try:
        # Extract repo name from URL
        repo_name = github_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        function_name = f"github-deploy-{repo_name}"
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, 'repo')
            
            # Clone the repository
            if not clone_github_repo(github_url, repo_path):
                raise Exception("Failed to clone repository")
            
            # Create deployment package
            zip_path = create_deployment_package(repo_path)
            
            try:
                # Deploy to Lambda
                lambda_response = create_or_update_lambda_function(function_name, zip_path, repo_name)
                
                # Create schedule
                schedule_response = create_cloudwatch_event_rule(function_name, repo_name)
                
                # Create CloudWatch alarms
                alarms_response = create_cloudwatch_alarms(function_name, repo_name)
                
                # Clean up zip file
                os.remove(zip_path)
                
                return {
                    'success': True,
                    'function_name': function_name,
                    'function_arn': lambda_response.get('FunctionArn'),
                    'schedule_rule': schedule_response.get('RuleArn'),
                    'alarms': alarms_response,
                    'message': f'Successfully deployed {repo_name} to Lambda with 120-second schedule and monitoring'
                }
                
            except Exception as e:
                # Clean up zip file on error
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                raise
        
    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to deploy {github_url} to Lambda'
        }


def get_deployment_status(function_name):
    try:
        session = get_aws_session()
        lambda_client = session.client('lambda')
        events_client = session.client('events')
        
        # Get function info
        function_info = lambda_client.get_function(FunctionName=function_name)
        
        # Get schedule rule info
        rule_name = f"{function_name}-schedule"
        try:
            rule_info = events_client.describe_rule(Name=rule_name)
        except events_client.exceptions.ResourceNotFoundException:
            rule_info = None
        
        return {
            'function_exists': True,
            'function_arn': function_info['Configuration']['FunctionArn'],
            'last_modified': function_info['Configuration']['LastModified'],
            'runtime': function_info['Configuration']['Runtime'],
            'schedule_enabled': rule_info['State'] == 'ENABLED' if rule_info else False,
            'schedule_expression': rule_info.get('ScheduleExpression') if rule_info else None
        }
        
    except lambda_client.exceptions.ResourceNotFoundException:
        return {
            'function_exists': False,
            'message': f'Function {function_name} not found'
        }
    except Exception as e:
        return {
            'error': str(e),
            'message': f'Failed to get status for {function_name}'
        }
