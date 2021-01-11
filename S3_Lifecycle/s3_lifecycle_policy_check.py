import boto3
import json
from botocore.exceptions import ClientError

######################
# Input variables : Each represents days
current_intelligent_tiering_transition = 120
noncurrent_glacier_transition = 120
noncurrent_permanent_delete = 365
######################

# Configure S3 client
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')
# Create variable with list of  buckets
bucket_list = s3_client.list_buckets()

############
# Function will create 2 dictionaries containing s3 buckets with and without a lifecycle policy
############
def view_lifecycle_policy(bucket_list):
    buckets_with_policy= {}
    buckets_without_policy= {}
    for bucket in bucket_list['Buckets']:
        try:
            lifecycle = s3_client.get_bucket_lifecycle(Bucket=bucket['Name'])
            rules = lifecycle['Rules']
            buckets_with_policy.update({bucket['Name']: rules})
        except:
            rules = 'No Policy'
            buckets_without_policy.update({bucket['Name']: rules})
    return buckets_with_policy, buckets_without_policy

############
# Function will apply the inline policy to dictionary provided
############
def configure_policies(bucket_list):
    for bucket, policy in bucket_list.items():
        bucket_lifecycle_configuration = s3_resource.BucketLifecycleConfiguration(bucket)
        # Sets lifecycle configuration for your bucket. If a lifecycle configuration exists, it replaces it.
        response = bucket_lifecycle_configuration.put(
            LifecycleConfiguration={
                'Rules': [
                    {
                        'ID': (str(bucket) + "-LifecyclePolicy"),
                        'Prefix': '',
                        'Status': 'Enabled',
                        'Transitions': [
                            {
                                'Days': current_intelligent_tiering_transition,
                                'StorageClass': 'INTELLIGENT_TIERING'
                            },
                            # {
                            #     'Days': (current_intelligent_tiering_transition + 30),
                            #     'StorageClass': 'GLACIER'
                            # },
                        ],
                        'NoncurrentVersionTransitions': [
                            {
                                'NoncurrentDays': noncurrent_glacier_transition,
                                'StorageClass': 'GLACIER'
                            },
                        ],
                        'NoncurrentVersionExpiration': {
                            'NoncurrentDays': noncurrent_permanent_delete
                        },
                        'AbortIncompleteMultipartUpload': {
                            'DaysAfterInitiation': 7
                        }
                    },
                ]
            }
        )
        print("Applied lifecycle to " + str(bucket))

def main():
    dict_policy_buckets = view_lifecycle_policy(bucket_list)
    # Because the dictionary returns buckets with and buckets without, there are 2 new variables
    buckets_with = dict_policy_buckets[0]
    buckets_without = dict_policy_buckets[1]
    print(json.dumps(buckets_with, indent=2, sort_keys=True, default=str))
    print('--------------')
    print(json.dumps(buckets_without, indent=2, sort_keys=True, default=str))
    print('--------------')
    #### ↑↑↑ This is non-impactful, no changes will be made ####
    #### ↓↓↓ This is apply the bucket policy to all buckets that currently do not have a policy ####
    # configure_policies(buckets_without) # --> Apply to all buckets
    print(" Apply lifecycle policy")
    ### ↓↓↓ This is a way to apply to a single bucket ↓↓↓ ###
    # configure_policies({"cf-templates-1berghw91kmrz-us-east-1": "No Policy"})
    print(" Applied lifecycle policy")

if __name__ == "__main__":
    main()