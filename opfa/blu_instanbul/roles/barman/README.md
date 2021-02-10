Role Name
=========

Install pgBarman into a server, and configure multiple backup with optional s3 backup.

Requirements
------------

An instance with network access to target machines (instance to backup).

Optionally an user with access to S3 (access key + secret).

Role Variables
--------------

TODO

Dependencies
------------

None.

Example Playbook
----------------

``` YAML
 - role: barman
      upload_to_s3: true
      aws_access_key_id: "aws_access_key_id"
      aws_secret_access_key: "aws_secret_access_key"
      aws_region: REGION
      aws_s3_bucket: BUCKET_NAME
      hosts:
        - { target_host: 192.168.0.1, port: 5432, target_name: target_name, db_name: target_db_name, barman_user_pass: "pg_pass_for_barman_user_in_target", retention_policy: REDUNDANCY 7 }
        - { target_host: 192.168.0.2, port: 5432, target_name: target_name, db_name: target_db_name, barman_user_pass: "pg_pass_for_barman_user_in_target", retention_policy: REDUNDANCY 7, cron_minute: 45, cron_hour: 12 }
```


License
-------

TODO
