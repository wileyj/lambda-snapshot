provider "aws" {
  region = "${var.region["${var.buildenv}"]}"
}

variable "org_name" {
  description = "Org name"
  default = "Local"
}

variable "owner" {
  description = "Default Asset owner"
  default     = "ops"
}

variable "region" {
  description = "AWS Region"

  default {
    "primary"   = "us-west-2"
    "secondary" = "us-east-1"
  }
}

variable "buildenv" {
  default = "primary"
}

variable "s3_bucket" {
  description = "S3 Bucket to store lambda function"
  default = "mylambdabucket"
}

data "aws_iam_policy_document" "instance-assume-role-policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "snapshot_lambda" {
  policy_id = "${var.org_name}-Ops-Snapshot"

  statement {
    sid    = "${var.org_name}OpsSnapshot"
    effect = "Allow"
    resources = [
      "*",
    ]

    actions = [
      "ec2:CreateTags",
      "ec2:CreateSnapshot",
      "ec2:DeleteSnapshot",
      "ec2:DeregisterImage",
      "ec2:DescribeImages",
      "ec2:DescribeInstances",
      "ec2:DescribeSnapshots",
      "ec2:DescribeTags",
      "ec2:DescribeVolumes",
      "cloudwatch:GetMetricStatistics",
    ]
  }
}

resource "aws_iam_policy" "snapshot_lambda" {
  name        = "${var.org_name}.Ops.Snapshot"
  description = "${var.org_name}.Ops.Snapshot"
  path        = "/${var.org_name}/Ops/"
  policy      = "${data.aws_iam_policy_document.snapshot_lambda.json}"
}

resource "aws_iam_role" "snapshot_lambda" {
  name               = "${var.org_name}.Ops.Snapshot"
  assume_role_policy = "${data.aws_iam_policy_document.instance-assume-role-policy.json}"
  path               = "/${var.org_name}/"

  depends_on = [
    "aws_iam_policy.snapshot_lambda",
  ]
}

resource "aws_iam_role_policy_attachment" "snapshot_lambda" {
  role       = "${aws_iam_role.snapshot_lambda.name}"
  policy_arn = "${aws_iam_policy.snapshot_lambda.arn}"

}

resource "aws_cloudwatch_event_rule" "snapshot_lambda" {
  name                = "${var.org_name}_Ops_EC2_EBS_Snapshot"
  description         = "Run Snapshots nightly"
  schedule_expression = "cron(00 03 * * ? *)"

  depends_on = [
    "aws_lambda_function.snapshot_lambda",
  ]
}

resource "aws_cloudwatch_event_target" "snapshot_lambda" {
  rule      = "${aws_cloudwatch_event_rule.snapshot_lambda.name}"
  target_id = "snapshot_lambda"
  arn       = "${aws_lambda_function.snapshot_lambda.arn}"

  depends_on = [
    "aws_cloudwatch_event_rule.snapshot_lambda",
  ]
}

resource "aws_lambda_function" "snapshot_lambda" {
  s3_bucket        = "${var.s3_bucket}"
  s3_key           = "ops-snapshot.zip"
  function_name    = "${var.org_name}_Ops_EC2_EBS_Snapshot"
  role             = "${aws_iam_role.snapshot_lambda.arn}"
  handler          = "main.handler"
# the following is predicated on a local copy of the zipped code. 
# without it commented, terraform doesn't know the code has changed and won't update lambda function
# source_code_hash = "${base64sha256(file("snapshot.zip"))}"
  runtime          = "python2.7"
  description      = "Function to create EBS snapshot volumes of currently used volumes"
  timeout          = "300"

  tags {
    Name        = "${var.org_name}.Ops.EC2.ebs_snapshotter"
    Department  = "${var.owner}"
    Environment = ""
    Stage       = ""
    Region      = "${var.region["${var.buildenv}"]}"
    Application = "shared"
    Role        = "lambda"
    Service     = "lambda"
    Category    = "lambda"
  }

  environment {
    variables = {
      TYPE                = "all"
      REGION              = "us-west-2"
      VERBOSITY           = "INFO"
      VOLUME              = ""
      INSTANCE_ID         = ""
      AMI_CREATION_METHOD = "Packer"
      RETENTION           = 7
      ROTATION            = 7
      HOURLY              = ""
      PERSIST             = ""
      ENVIRONMENT         = "*"
      INCLUDE_AMI         = "false"
      DRY_RUN             = "true"
      #ACCOUNT_ID = ""
    }
  }

  depends_on = [
    "aws_iam_role_policy_attachment.snapshot_lambda",
  ]
}
