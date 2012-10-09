

def add_tags(object_, tags):
    for key, value in tags.iteritems():
        object_.add_tag(key, value)


def get_userdata_dict():
    from json import loads
    from boto.utils import get_instance_userdata
    userdata = loads(get_instance_userdata())
    return userdata


def get_ec2_conn():
    from snaptastic import settings
    from boto import ec2
    ec2_conn = ec2.connect_to_region(settings.REGION,
                                     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    return ec2_conn
