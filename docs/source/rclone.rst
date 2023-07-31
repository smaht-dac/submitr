=======================================
Awscli/Rclone Submission (experimental)
=======================================

For some use cases we are trialing a more streamlined submission process that does
not involve the installation of Python or ``submitr`` and instead involves transferring
files directly into a ``PUBLIC-WRITE`` S3 bucket defined by us. The idea is you will source
credentials associated with the datastore where your files are kept and sync them
directly into the submission bucket, along with the submission Excel (for data
accessioning).

These instructions are intended to support both ``awscli`` if transferring directly from
``AWS S3`` or ``rclone`` if you are transferring from other Cloud Providers (still compatible
with ``AWS S3``). At this time we recommend using ``rclone``, since it is compatible with
most popular Cloud Providers.


Installing rclone
-----------------

Navigate to the ``rclone`` `download page <https://rclone.org/downloads/>`_ and click the
download button that corresponds to the operating system you are running. Once installed
you should see the ``rclone`` command in your path.

.. code-block:: console

    $ which rclone


Configuring Anonymous S3 Remote
-------------------------------

The ``rclone`` `S3 documentation page <https://rclone.org/s3/>`_ has detailed information
on how to configure S3 remotes. If your submission files are not on AWS S3, you will need
to create an anonymous S3 remote for use with the transfer. The bucket name we will give
you will allow anyone to submit files to it but will only us internally to read the files.

Upon running ``rclone config`` you should be greeted with detailed setup instructions that
the below block emulates to walk you through the process. Our submission bucket will be
in us-east-1, but be aware if transferring from another AZ on S3 you will incur S3
egress charges when transferring into our bucket.

If you are submitting from S3, you will want to follow very similar configuration as
the below except that you will want to pass your account access key ID and secret so
you can access the files in your account. You will not need access credentials to submit
to our buckets, though that can be arranged if it is preferred.


.. code-block:: console

    $ rclone configure
    No remotes found, make a new one?
    n) New remote
    s) Set configuration password
    q) Quit config
    n/s/q> n
    name> smaht_s3_submission
    Type of storage to configure.
    Choose a number from below, or type in your own value
    [snip]
    XX / Amazon S3 Compliant Storage Providers including AWS, Ceph, ChinaMobile, ArvanCloud, Dreamhost, IBM COS, Minio, and Tencent COS
       \ "s3"
    [snip]
    Storage> s3
    Choose your S3 provider.
    Choose a number from below, or type in your own value
     1 / Amazon Web Services (AWS) S3
       \ "AWS"
     2 / Ceph Object Storage
       \ "Ceph"
     3 / Digital Ocean Spaces
       \ "DigitalOcean"
     4 / Dreamhost DreamObjects
       \ "Dreamhost"
     5 / IBM COS S3
       \ "IBMCOS"
     6 / Minio Object Storage
       \ "Minio"
     7 / Wasabi Object Storage
       \ "Wasabi"
     8 / Any other S3 compatible provider
       \ "Other"
    provider> 1
    Get AWS credentials from runtime (environment variables or EC2/ECS meta data if no env vars). Only applies if access_key_id and secret_access_key is blank.
    Choose a number from below, or type in your own value
     1 / Enter AWS credentials in the next step
       \ "false"
     2 / Get AWS credentials from the environment (env vars or IAM)
       \ "true"
    env_auth> 1
    AWS Access Key ID - leave blank for anonymous access or runtime credentials.
    access_key_id>
    AWS Secret Access Key (password) - leave blank for anonymous access or runtime credentials.
    secret_access_key>
    Region to connect to.
    Choose a number from below, or type in your own value
       / The default endpoint - a good choice if you are unsure.
     1 | US Region, Northern Virginia, or Pacific Northwest.
       | Leave location constraint empty.
       \ "us-east-1"
       / US East (Ohio) Region
     2 | Needs location constraint us-east-2.
       \ "us-east-2"
       / US West (Oregon) Region
     3 | Needs location constraint us-west-2.
       \ "us-west-2"
       / US West (Northern California) Region
     4 | Needs location constraint us-west-1.
       \ "us-west-1"
       / Canada (Central) Region
     5 | Needs location constraint ca-central-1.
       \ "ca-central-1"
       / EU (Ireland) Region
     6 | Needs location constraint EU or eu-west-1.
       \ "eu-west-1"
       / EU (London) Region
     7 | Needs location constraint eu-west-2.
       \ "eu-west-2"
       / EU (Frankfurt) Region
     8 | Needs location constraint eu-central-1.
       \ "eu-central-1"
       / Asia Pacific (Singapore) Region
     9 | Needs location constraint ap-southeast-1.
       \ "ap-southeast-1"
       / Asia Pacific (Sydney) Region
    10 | Needs location constraint ap-southeast-2.
       \ "ap-southeast-2"
       / Asia Pacific (Tokyo) Region
    11 | Needs location constraint ap-northeast-1.
       \ "ap-northeast-1"
       / Asia Pacific (Seoul)
    12 | Needs location constraint ap-northeast-2.
       \ "ap-northeast-2"
       / Asia Pacific (Mumbai)
    13 | Needs location constraint ap-south-1.
       \ "ap-south-1"
       / Asia Pacific (Hong Kong) Region
    14 | Needs location constraint ap-east-1.
       \ "ap-east-1"
       / South America (Sao Paulo) Region
    15 | Needs location constraint sa-east-1.
       \ "sa-east-1"
    region> 1
    Endpoint for S3 API.
    Leave blank if using AWS to use the default endpoint for the region.
    endpoint>
    Location constraint - must be set to match the Region. Used when creating buckets only.
    Choose a number from below, or type in your own value
     1 / Empty for US Region, Northern Virginia, or Pacific Northwest.
       \ ""
     2 / US East (Ohio) Region.
       \ "us-east-2"
     3 / US West (Oregon) Region.
       \ "us-west-2"
     4 / US West (Northern California) Region.
       \ "us-west-1"
     5 / Canada (Central) Region.
       \ "ca-central-1"
     6 / EU (Ireland) Region.
       \ "eu-west-1"
     7 / EU (London) Region.
       \ "eu-west-2"
     8 / EU Region.
       \ "EU"
     9 / Asia Pacific (Singapore) Region.
       \ "ap-southeast-1"
    10 / Asia Pacific (Sydney) Region.
       \ "ap-southeast-2"
    11 / Asia Pacific (Tokyo) Region.
       \ "ap-northeast-1"
    12 / Asia Pacific (Seoul)
       \ "ap-northeast-2"
    13 / Asia Pacific (Mumbai)
       \ "ap-south-1"
    14 / Asia Pacific (Hong Kong)
       \ "ap-east-1"
    15 / South America (Sao Paulo) Region.
       \ "sa-east-1"
    location_constraint> 1
    Canned ACL used when creating buckets and/or storing objects in S3.
    For more info visit https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl
    Choose a number from below, or type in your own value
     1 / Owner gets FULL_CONTROL. No one else has access rights (default).
       \ "private"
     2 / Owner gets FULL_CONTROL. The AllUsers group gets READ access.
       \ "public-read"
       / Owner gets FULL_CONTROL. The AllUsers group gets READ and WRITE access.
     3 | Granting this on a bucket is generally not recommended.
       \ "public-read-write"
     4 / Owner gets FULL_CONTROL. The AuthenticatedUsers group gets READ access.
       \ "authenticated-read"
       / Object owner gets FULL_CONTROL. Bucket owner gets READ access.
     5 | If you specify this canned ACL when creating a bucket, Amazon S3 ignores it.
       \ "bucket-owner-read"
       / Both the object owner and the bucket owner get FULL_CONTROL over the object.
     6 | If you specify this canned ACL when creating a bucket, Amazon S3 ignores it.
       \ "bucket-owner-full-control"
    acl> 1
    The server-side encryption algorithm used when storing this object in S3.
    Choose a number from below, or type in your own value
     1 / None
       \ ""
     2 / AES256
       \ "AES256"
    server_side_encryption> 2
    The storage class to use when storing objects in S3.
    Choose a number from below, or type in your own value
     1 / Default
       \ ""
     2 / Standard storage class
       \ "STANDARD"
     3 / Reduced redundancy storage class
       \ "REDUCED_REDUNDANCY"
     4 / Standard Infrequent Access storage class
       \ "STANDARD_IA"
     5 / One Zone Infrequent Access storage class
       \ "ONEZONE_IA"
     6 / Glacier storage class
       \ "GLACIER"
     7 / Glacier Deep Archive storage class
       \ "DEEP_ARCHIVE"
     8 / Intelligent-Tiering storage class
       \ "INTELLIGENT_TIERING"
     9 / Glacier Instant Retrieval storage class
       \ "GLACIER_IR"
    storage_class> 1
    Remote config
    --------------------
    [smaht_s3_submission]
    type = s3
    provider = AWS
    env_auth = false
    access_key_id =
    secret_access_key =
    region = us-east-1
    endpoint =
    location_constraint =
    acl = private
    server_side_encryption = AES256
    storage_class =
    --------------------
    y) Yes this is OK
    e) Edit this remote
    d) Delete this remote
    y/e/d> y


If successful you should be able to transfer files from the local machine or your private
s3 buckets into our submission bucket. If we have not told you the bucket name to submit
to, please reach out to us at `cgap-support@hms-dbmi.atlassian.net <mailto:cgap-support@hms-dbmi.atlassian.net>`_.

You then can transfer files from your local machine or your private S3 buckets into
our submission bucket. Test our remote by filling out the accessioning spreadsheet
and submitting it to our S3 bucket. Please denote a sensible case ID to use as a folder
prefix for the current submission. Transfer the spreadsheet with:

.. code-block:: console

    $ rclone copy ~/Documents/submitr/case0001/case0001_accessioning.xls smaht_s3_submission:smaht-submission-bucket/case0001/case0001_accessioning.xls


If successful, continue by transferring the raw files into the submission bucket.

.. code-block:: console

    $ rclone copy smaht_s3_submission:your-private-s3-bucket/fastq1.fastq.gz smaht_s3_submission:smaht-submission-bucket/case0001/fastq1.fastq.gz
    $ rclone copy smaht_s3_submission:your-private-s3-bucket/fastq2.fastq.gz smaht_s3_submission:smaht-submission-bucket/case0001/fastq2.fastq.gz


If you are not using AWS S3 as your storage provider, see the following instructions.


Transferring from Another Cloud
-------------------------------

As mentioned previously, ``rclone`` is a cross-platform compatible file transfer tool.
This allows you to submit files to our S3 buckets that live in other cloud platforms.
To do this, you will need to locate your cloud provider on the main
`rclone documentation page <https://rclone.org/>`_
and click the ``config`` button then follow the configuration instructions for ``rclone`` on
the subsequent page.


Transferring from Google Cloud
------------------------------

A common use-case is to transfer files that live in Google Cloud to us on S3. Similar to
the S3 remote setup needed to communicate with our submission bucket, you must do a
similar sort of
`configuration <https://rclone.org/googlecloudstorage/>`_
for communicating with Google Cloud. Run ``rclone config`` as before.

.. code-block:: console

    $ rclone config
    New remote
    d) Delete remote
    q) Quit config
    e/n/d/q> n
    name> remote_files_for_smaht_submission
    Type of storage to configure.
    Choose a number from below, or type in your own value
    [snip]
    XX / Google Cloud Storage (this is not Google Drive)
       \ "google cloud storage"
    [snip]
    Storage> google cloud storage
    Google Application Client Id - leave blank normally.
    client_id>
    Google Application Client Secret - leave blank normally.
    client_secret>
    Project number optional - needed only for list/create/delete buckets - see your developer console.
    project_number> 12345678
    Service Account Credentials JSON file path - needed only if you want use SA instead of interactive login.
    service_account_file>
    Access Control List for new objects.
    Choose a number from below, or type in your own value
     1 / Object owner gets OWNER access, and all Authenticated Users get READER access.
       \ "authenticatedRead"
     2 / Object owner gets OWNER access, and project team owners get OWNER access.
       \ "bucketOwnerFullControl"
     3 / Object owner gets OWNER access, and project team owners get READER access.
       \ "bucketOwnerRead"
     4 / Object owner gets OWNER access [default if left blank].
       \ "private"
     5 / Object owner gets OWNER access, and project team members get access according to their roles.
       \ "projectPrivate"
     6 / Object owner gets OWNER access, and all Users get READER access.
       \ "publicRead"
    object_acl> 4
    Access Control List for new buckets.
    Choose a number from below, or type in your own value
     1 / Project team owners get OWNER access, and all Authenticated Users get READER access.
       \ "authenticatedRead"
     2 / Project team owners get OWNER access [default if left blank].
       \ "private"
     3 / Project team members get access according to their roles.
       \ "projectPrivate"
     4 / Project team owners get OWNER access, and all Users get READER access.
       \ "publicRead"
     5 / Project team owners get OWNER access, and all Users get WRITER access.
       \ "publicReadWrite"
    bucket_acl> 2
    Location for the newly created buckets.
    Choose a number from below, or type in your own value
     1 / Empty for default location (US).
       \ ""
     2 / Multi-regional location for Asia.
       \ "asia"
     3 / Multi-regional location for Europe.
       \ "eu"
     4 / Multi-regional location for United States.
       \ "us"
     5 / Taiwan.
       \ "asia-east1"
     6 / Tokyo.
       \ "asia-northeast1"
     7 / Singapore.
       \ "asia-southeast1"
     8 / Sydney.
       \ "australia-southeast1"
     9 / Belgium.
       \ "europe-west1"
    10 / London.
       \ "europe-west2"
    11 / Iowa.
       \ "us-central1"
    12 / South Carolina.
       \ "us-east1"
    13 / Northern Virginia.
       \ "us-east4"
    14 / Oregon.
       \ "us-west1"
    location> 12
    The storage class to use when storing objects in Google Cloud Storage.
    Choose a number from below, or type in your own value
     1 / Default
       \ ""
     2 / Multi-regional storage class
       \ "MULTI_REGIONAL"
     3 / Regional storage class
       \ "REGIONAL"
     4 / Nearline storage class
       \ "NEARLINE"
     5 / Coldline storage class
       \ "COLDLINE"
     6 / Durable reduced availability storage class
       \ "DURABLE_REDUCED_AVAILABILITY"
    storage_class> 5
    Remote config
    Use auto config?
     * Say Y if not sure
     * Say N if you are working on a remote or headless machine or Y didn't work
    y) Yes
    n) No
    y/n> y
    If your browser doesn't open automatically go to the following link: http://127.0.0.1:53682/auth
    Log in and authorize rclone for access
    Waiting for code...
    Got code
    --------------------
    [remote_files_for_smaht_submission]
    type = google cloud storage
    client_id =
    client_secret =
    token = {"AccessToken":"xxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","RefreshToken":"x/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx_xxxxxxxxx","Expiry":"2014-07-17T20:49:14.929208288+01:00","Extra":null}
    project_number = 12345678
    object_acl = private
    bucket_acl = private
    --------------------
    y) Yes this is OK
    e) Edit this remote
    d) Delete this remote
    y/e/d> y


After the Google Cloud connection is configured, you should be able to combine them
to submit your submission files directly.

.. code-block:: console

    $ rclone copy remote_files_for_smaht_submission:your-private-gcloud-bucket/fastq1.fastq.gz smaht_s3_submission:smaht-submission-bucket/case0001/fastq1.fastq.gz
    $ rclone copy remote_files_for_smaht_submission:your-private-gcloud-bucket/fastq2.fastq.gz smaht_s3_submission:smaht-submission-bucket/case0001/fastq2.fastq.gz


These transfers may take some significant time but should still be faster than if
downloading to the local machine. Once complete please notify one of our data wranglers
who will verify the submission was successful and finalize the process on our end.
